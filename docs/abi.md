# usegolib ABI (v0.x)

This document specifies the cross-language ABI between Python and the Go shared library.

## Transport

- Requests and responses are **MessagePack** encoded.
- The Go shared library exposes a stable C ABI:
  - `usegolib_call(req_ptr, req_len, *resp_ptr, *resp_len) -> int`
  - `usegolib_free(ptr) -> void`

The ABI is intentionally small: the wire format carries only generic MessagePack values. Higher-level typing
(record structs, typed adapters) is enforced by the runtime using manifest schema exchange.

## Memory Ownership

- The caller (Python) owns the request buffer.
- The callee (Go) allocates the response buffer.
- The caller MUST call `usegolib_free(resp_ptr)` after copying the response into Python-owned memory.

## Request Format

All requests are MessagePack maps:

- `abi`: integer ABI version (v0 == `0`)
- `op`: operation name (v0 supports: `call`, `obj_new`, `obj_call`, `obj_free`)

### `op = "call"`

- `pkg`: Go package import path (string)
- `fn`: exported function name (string)
- `args`: list of arguments (see Type Bridge below)

Example (conceptual):

```text
{
  "abi": 0,
  "op": "call",
  "pkg": "example.com/mod",
  "fn": "AddInt",
  "args": [1, 2]
}
```

### `op = "obj_new"`

Create a Go-side object instance and return an opaque id.

- `pkg`: Go package import path (string)
- `type`: receiver struct type name (string, exported; no leading `*`)
- `init`: optional record-struct value used to initialize the struct (Level 3); if omitted, the zero value is used

Example (conceptual):

```text
{
  "abi": 0,
  "op": "obj_new",
  "pkg": "example.com/mod",
  "type": "Counter",
  "init": {"n": 1}
}
```

### `op = "obj_call"`

Call a method on a previously created object.

- `pkg`: Go package import path (string)
- `type`: receiver struct type name (string, exported; no leading `*`)
- `id`: object id returned by `obj_new`
- `method`: exported method name (string)
- `args`: list of arguments (see Type Bridge below)

Example (conceptual):

```text
{
  "abi": 0,
  "op": "obj_call",
  "pkg": "example.com/mod",
  "type": "Counter",
  "id": 1,
  "method": "Inc",
  "args": [2]
}
```

### `op = "obj_free"`

Free a Go-side object id.

- `id`: object id returned by `obj_new`

Example (conceptual):

```text
{
  "abi": 0,
  "op": "obj_free",
  "id": 1
}
```

## Response Format

All responses are MessagePack maps:

- `ok`: boolean
- If `ok == true`:
  - `result`: the return value (or `nil` for void). This field is always present when `ok == true`.
- If `ok == false`:
  - `error`: error object

### Error Object

- `type`: string (stable error class, e.g. `GoError`, `GoPanicError`, `UnsupportedSignatureError`)
- `message`: string (human readable)
- `detail`: map (optional; structured details)

## Type Bridge (v0.x)

Supported values crossing the ABI:

- Level 1:
  - `nil`
  - `bool`
  - integers (signed 64-bit range)
  - floats (`float32`/`float64` encoded as MessagePack float; Python uses `float`)
  - `string`
  - `bytes`
  - slices/lists of supported values (including lists of bytes)
- `any`:
  - `any` is represented on the wire as a plain MessagePack value (no extra envelope)
  - `[]any` and `map[string]any` are supported recursively
- Level 2:
  - `map[string]T` where `T` is a Level 1 scalar or a slice of Level 1 scalars
  - Encoded as a MessagePack map from string keys to values
- Level 3 (Record Structs):
  - Named Go structs are represented as MessagePack maps from canonical field keys to values
  - Field values are limited to Level 1/2 and record structs recursively

Unsupported values MUST fail with `UnsupportedTypeError`.

### Variadic Parameters (`...T`)

Go variadic parameters (`...T`) are represented in the ABI as a single final argument whose value is a list.

Examples:
- Go: `Append(values ...any)`
  - Python: `obj.Append(1, 2, 3)` sends `args = [[1, 2, 3]]`
  - Python: `obj.Append()` sends `args = [[]]`
- Go: `Data(useNamesAsKeys ...bool)`
  - Python: `dt.Data(True)` sends `args = [[True]]`

When manifest schema is present, the Python runtime packs varargs automatically.

### Canonical Keys (Tags)

For record structs, canonical keys follow:
1. `msgpack:"name,omitempty"`
2. `json:"name,omitempty"`
Otherwise the exported Go field name is used.

Tag options:
- `omitempty`: field may be omitted on input; may be omitted on output when empty
- ignore: `msgpack:"-"` (or, if no msgpack tag exists, `json:"-"`) is excluded from schema and outputs

### Typed Adapters

Some Go types are supported by encoding them as plain MessagePack scalars:

- `time.Time` is encoded as an RFC3339Nano string
- `time.Duration` is encoded as an int64 nanoseconds count
- `uuid.UUID` (`github.com/google/uuid.UUID`) is encoded as a UUID string

These are interpreted using the manifest schema; on the wire they are just strings/integers.

## Schema Exchange (Manifest)

Artifacts embed a schema in `manifest.json` describing:
- callable symbols and their parameter/return types
- callable methods (receiver type + method name) and their parameter/return types
- named struct types and their fields (including keys, aliases, required/omitempty)

When schema is present, the runtime validates call arguments and successful results against the schema
before invoking (and before returning to user code) to fail fast in Python.

# usegolib ABI (v0)

This document specifies the cross-language ABI between Python and the Go shared library.

## Transport

- Requests and responses are **MessagePack** encoded.
- The Go shared library exposes a stable C ABI:
  - `usegolib_call(req_ptr, req_len, *resp_ptr, *resp_len) -> int`
  - `usegolib_free(ptr) -> void`

## Memory Ownership

- The caller (Python) owns the request buffer.
- The callee (Go) allocates the response buffer.
- The caller MUST call `usegolib_free(resp_ptr)` after copying the response into Python-owned memory.

## Request Format

All requests are MessagePack maps:

- `abi`: integer ABI version (v0 == `0`)
- `op`: operation name (v0 supports only `call`)
- `pkg`: Go package import path (string)
- `fn`: exported function name (string)
- `args`: list of arguments (Level 1 types only for v0)

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

## Response Format

All responses are MessagePack maps:

- `ok`: boolean
- If `ok == true`:
  - `result`: the return value (or `nil` for void)
- If `ok == false`:
  - `error`: error object

### Error Object

- `type`: string (stable error class, e.g. `GoError`, `GoPanicError`, `UnsupportedSignatureError`)
- `message`: string (human readable)
- `detail`: map (optional; structured details)

## Type Bridge (v0 = Level 1)

Supported values crossing the ABI:

- `nil`
- `bool`
- integers (signed 64-bit range)
- floats (64-bit)
- `string`
- `bytes`
- slices/lists of the above (including lists of bytes)

Unsupported values MUST fail with `UnsupportedTypeError`.


# Design: Go-Side Object Handles + Method Dispatch

## Goal

Enable calling exported methods without serializing the receiver struct each time:
- create object once (`obj_new`) from record-struct input
- subsequent method calls pass only `(id, args...)`
- free explicitly (`obj_free`) with best-effort Python finalizer

## ABI Extensions (v0)

All requests remain MessagePack maps with `abi=0`.

- `op="obj_new"`:
  - `pkg`: package import path
  - `type`: receiver struct type name (in that package)
  - `init`: record-struct map (optional; omitted means zero value)
- `op="obj_call"`:
  - `pkg`: package import path
  - `type`: receiver struct type name
  - `id`: int (opaque handle)
  - `method`: exported method name
  - `args`: list
- `op="obj_free"`:
  - `id`: int

Responses reuse the existing envelope (`ok/result/error`).

## Go Bridge Implementation

- Maintain an object registry: `map[uint64]any` protected by a mutex.
- Generate a `typeByKey` map to get `reflect.Type` for allowed struct types (`pkg.Type`).
- `obj_new`:
  - Convert `init` into the struct type using existing `convertToType`
  - Store a pointer to the struct in the registry
  - Return the generated ID (int)
- `obj_call`:
  - Dispatch to a generated wrapper function keyed by `pkg:type:method`
  - Wrapper:
    - load `*T` from registry
    - convert args
    - call `recv.Method(...)`
    - encode results using existing export helpers
- `obj_free`: delete from registry

## Python Runtime

- Add `PackageHandle.object(type_name, init=None) -> GoObject`.
- `GoObject` holds `(handle, pkg, type, id)` and supports:
  - `__getattr__` to call methods
  - `close()` / context manager
  - `__del__` best-effort `obj_free`
- When schema is present, validate `type_name` exists and validate method args/results.


## Why

For performance and ergonomics, we want to call Go exported methods without re-serializing the entire receiver struct on every call. This requires Go-side state with an opaque handle ID, plus Python proxy objects that hold the handle and call methods through the ABI.

## What Changes

- Extend ABI v0 with additional operations:
  - `obj_new`: create a Go object from an initial record-struct value and return an opaque ID
  - `obj_call`: call an exported method on a stored object by ID
  - `obj_free`: free an object ID
- Builder:
  - scan exported methods (non-generic) and include them in manifest schema
  - generate bridge code that supports object registry + method dispatch
- Runtime:
  - add a Python `GoObject` proxy with `obj.MethodName(...)` calls
  - add `PackageHandle.object(type_name, init=...) -> GoObject`

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities

- `usegolib-core`: ABI operations + method support + object handles

## Impact

- Affected code: `src/usegolib/abi.py`, `src/usegolib/handle.py`, `src/usegolib/schema.py`,
  `src/usegolib/builder/scan.py`, `src/usegolib/builder/build.py`, `src/usegolib/builder/gobridge.py`
- Affected docs: `docs/abi.md`
- Affected tests: add new integration tests for object handles/method calls


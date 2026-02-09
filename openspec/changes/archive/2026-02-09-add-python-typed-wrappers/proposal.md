# Change: Python Typed Struct Wrappers

## Why
Record structs (dicts) are powerful but error-prone and lack IDE help. The runtime already exchanges struct schemas via the manifest; we can leverage that to generate Python dataclasses for named Go structs and provide an ergonomic, typed calling surface.

## What Changes
- Add a runtime facility to generate Python dataclasses for Go named structs from the manifest schema.
- Add a typed call wrapper that:
  - accepts dataclass instances as arguments (encoded to record-struct dicts using canonical keys)
  - converts record-struct results into dataclass instances based on the schema return type

## Impact
- Affected specs: `usegolib-core`
- Affected code:
  - `src/usegolib/handle.py`
  - `src/usegolib/schema.py`
  - `src/usegolib/typed.py` (new)
  - tests


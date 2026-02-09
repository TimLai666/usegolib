# Change: Typed Adapter For uuid.UUID

## Why
UUID is a very common value type in Go APIs. For typed structs and schema validation to be practical in real projects, `uuid.UUID` should roundtrip without custom glue code.

## What Changes
- Support `github.com/google/uuid.UUID` across the ABI as a string.
- Scanner canonicalizes selector types to `uuid.UUID` even if the import uses an alias (e.g. `gouuid.UUID`).
- Extend builder signature filter, Go bridge conversion, and runtime schema validation to treat `uuid.UUID` as an adapter type.

## Impact
- Affected specs: `usegolib-core`
- Affected code:
  - `src/usegolib/builder/scan.py` (import-aware type rendering)
  - `src/usegolib/builder/build.py`
  - `src/usegolib/builder/gobridge.py`
  - `src/usegolib/schema.py`
  - `src/usegolib/typed.py`
  - tests


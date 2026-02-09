# Change: Python Bindings Generator (Static Module)

## Why
The runtime can already call Go functions and exchange typed-struct schemas, but dynamic handles provide limited IDE/type-checker support.
Generating a real Python module with dataclasses and typed methods provides a stable, checkable surface that can be committed to downstream repos.

## What Changes
- Add `usegolib gen` CLI to generate a Python module (`.py`) from a built artifact's manifest schema for a specific package.
- Generated module includes:
  - dataclasses for Go named structs in the package
  - an `API` wrapper with typed methods for exported symbols
  - a `load()` helper that loads the artifact via `usegolib.import_`
- Generated API decodes struct results into the generated dataclasses and accepts those dataclasses as inputs.

## Impact
- Affected specs: `usegolib-core`
- Affected code:
  - `src/usegolib/cli.py`
  - `src/usegolib/handle.py`
  - `src/usegolib/typed.py`
  - `src/usegolib/bindgen.py` (new)
  - tests


# Change: GoDoc To Python Docstrings

## Why
When calling Go modules from Python, users often rely on IDE help / `help()` output to understand APIs. Today, `usegolib` exposes callable symbols but drops Go doc comments, so Python callables have no docstrings.

## What Changes
- The builder scanner extracts Go doc comments for exported functions/methods (and generic funcs) from source AST comments (not `go doc` text output).
- The artifact manifest schema includes a `doc` field for symbols and methods.
- The Python runtime attaches docstrings to dynamically created callables (best-effort when schema is present).
- The bindgen generator emits docstrings into the generated Python module.

## Impact
- Affected specs: `usegolib-core`
- Affected code: `src/usegolib/builder/scan.py`, `src/usegolib/builder/symbols.py`, `src/usegolib/builder/build.py`, `src/usegolib/schema.py`, `src/usegolib/handle.py`, `src/usegolib/bindgen.py`


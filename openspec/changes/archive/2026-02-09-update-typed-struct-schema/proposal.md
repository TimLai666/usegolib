# Change: Update Typed Struct Schema (Required Fields + Tag Options + Embedded Fields)

## Why
Typed structs are becoming the primary Level 3 interface. To make them production-safe and predictable, the runtime validator needs to catch missing required fields, and the builder/runtime need to agree on tag semantics (ignore/omitempty) and embedded fields.

## What Changes
- Extend manifest struct field schema with field metadata:
  - `required` (input presence requirement)
  - `omitempty` (tag option)
  - `embedded` (anonymous/embedded field)
- Builder scanner includes embedded exported struct fields in schema exchange (previously skipped).
- Runtime schema validation rejects missing required fields (in addition to type/unknown-field checks).
- Record struct export respects `omitempty` and ignore tags (`msgpack:"-"` / `json:"-"`) to avoid emitting fields that are not part of the schema.

## Impact
- Affected specs: `usegolib-core`
- Affected code:
  - `src/usegolib/builder/scan.py`
  - `src/usegolib/builder/build.py`
  - `src/usegolib/schema.py`
  - `src/usegolib/builder/gobridge.py`


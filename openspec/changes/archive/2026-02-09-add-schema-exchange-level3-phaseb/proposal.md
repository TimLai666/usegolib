## Why

Level 3 Phase A (record structs) relies on runtime reflection conversion. To improve correctness and debuggability, we need a typed/schema exchange step at import time describing struct fields and supported function signatures.

This enables:
- deterministic validation errors before calling into the shared library
- recursive validation for nested structs (schema-driven)
- future extensibility (typed envelopes, schema versioning)

## What Changes

- Builder emits a `schema` section in `manifest.json` describing:
  - exported callable symbols (per package) with param/result type strings
  - named struct types and their exported fields (field name + type string)
- Runtime loads the schema on import and validates arguments against it before ABI encoding.

## Impact

- No breaking changes to the MessagePack call format.
- Better errors (`UnsupportedTypeError`) when values don't match schema.


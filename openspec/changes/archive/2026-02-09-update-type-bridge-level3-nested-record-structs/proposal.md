## Why

Level 3 Phase A (record structs) currently supports passing/returning named struct values as maps, but does not support nested structs (struct fields whose type is also a struct), nor composite containers of structs (e.g. `[]Person`, `map[string]Person`).

Many real-world Go APIs model data with nested structs and lists/maps of structs, so this is a practical prerequisite before adding typed schema exchange (Phase B).

## What Changes

- Extend Level 3 record structs to support **nested record structs** recursively for fields whose type is a supported struct.
- Extend supported types to include slices and maps whose element/value type is a supported struct.

## Impact

- More signatures become supported by the builder and bridge generator.
- Runtime behavior remains backward compatible for Level 1/2 payloads.


## Why

Level 2 adds `map[string]T`, but many Go libraries expose richer data via structs. To enable practical interop without a full schema system, we want a Level 3 Phase A bridge where structs are represented as records: MessagePack maps of exported field names to values.

This keeps the ABI stable (Level 1 and 2 meanings do not change) while enabling a useful subset of structured data.

## What Changes

- Extend the v0 bridge to support passing and returning **named struct types** as records.
  - Struct values are represented as dict/map from exported field names to supported values.
  - Field values are limited to Level 1 and Level 2 types (no nested structs in Phase A).
- Extend the builder scanner output so it can identify which named types are structs, enabling signature filtering and bridge generation.

## Impact

- New supported signatures for exported functions that take/return named structs defined in the target package.
- Bridge runtime performs struct field conversion and validation at call time.


## Why

Typed structs become significantly more useful when they can include common standard library types. The most common is `time.Time`, which appears in APIs and struct fields.

We want `time.Time` to cross the boundary as a stable scalar representation, without treating it as a record struct.

## What Changes

- Support `time.Time` in supported signatures and struct fields.
- Encode/decode `time.Time` as RFC3339Nano strings across the ABI.
- Extend schema validation to treat `time.Time` as a string-like adapter type.

## Impact

- New supported type: `time.Time` (including pointers/slices/maps containing it).
- More Go APIs become callable without custom glue.


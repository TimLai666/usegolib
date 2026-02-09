## Why

`time.Duration` is a common parameter and struct field type in Go APIs. Typed structs and schema validation should support it without requiring custom glue code.

## What Changes

- Support `time.Duration` in supported signatures and typed structs.
- Encode/decode `time.Duration` across the ABI as an integer number of nanoseconds (int64 range).
- Extend schema validation to treat `time.Duration` as an integer adapter type.

## Impact

- New supported type: `time.Duration` (including pointers/slices/maps containing it).


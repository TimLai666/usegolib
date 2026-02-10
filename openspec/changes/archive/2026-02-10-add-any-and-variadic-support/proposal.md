## Why

Many real-world Go libraries (including Insyra) model data as `any` and use variadic parameters (e.g. `values ...any`). Today those symbols are excluded by the scanner/build filter, which blocks practical interop use cases like `DataList` and `DataTable`.

## What Changes

- Builder scanner recognizes variadic parameters and records them in a stable type form (`...T`).
- Type bridge supports `any` (Go `interface{}`) and common containers (`[]any`, `map[string]any`) for parameters and results.
- Bridge wrappers correctly call variadic functions/methods using slice expansion (`arg...`) and can encode/decode `any` values safely.
- Runtime packs variadic Python arguments into the ABI form and validates them against schema when present.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `usegolib-core`: extend the supported type bridge to include `any` and variadic parameters

## Impact

- Affected code:
  - `src/usegolib/builder/scan.py` (variadic scanning)
  - `src/usegolib/builder/build.py` (signature support filter)
  - `src/usegolib/builder/gobridge.py` (arg conversion + export for `any`, variadic call sites)
  - `src/usegolib/schema.py` (parse/validate `...T` and `any`)
  - `src/usegolib/handle.py` (runtime packing for variadic calls)
  - docs + examples

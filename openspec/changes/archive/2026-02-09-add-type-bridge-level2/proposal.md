## Why

V0 currently supports Level 1 values only. Many practical APIs in Go take structured inputs like `map[string]T` (options, metadata, row objects). We need the planned Level 2 bridge so Python can pass dictionaries and Go can return dictionaries in a supported, testable way.

## What Changes

- Extend the bridge to support `map[string]T` where `T` is a Level 1 scalar or a slice of Level 1 scalars.
- Add integration tests for map arguments and map return values.

## Capabilities

### New Capabilities
- *(none)*

### Modified Capabilities
- `usegolib-core`: supported type bridge expands to Level 2

## Impact

- Go bridge generator adds map conversion helpers.
- Builder signature filter expands to include `map[string]...` types.
- Integration tests will validate map behavior across ABI.


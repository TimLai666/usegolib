## Why

The spec says remote module builds default to `@latest` when no version is provided. The current resolver uses `latest` (without `@`), which can break `go mod download` and prevents the "auto-download Go module" workflow from working reliably.

## What Changes

- Fix remote module version defaulting: `None` -> `@latest` (and accept `latest` by mapping to `@latest`).
- Add unit tests to enforce resolver behavior without requiring a Go toolchain in unit test runs.
- Update README to explicitly show importing a remote module/package triggers auto-download/build (dev mode).

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities

- `usegolib-core`: remote module version resolution behavior (bug fix)

## Impact

- Affected code: `src/usegolib/builder/resolve.py`
- Affected docs: `README.md`
- Affected tests: `tests/test_builder_resolve.py`


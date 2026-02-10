## Why

`usegolib.import_` now supports auto-build and remote module downloads in dev workflows, which changes when Go is required on the user's machine. README should clearly distinguish end-user runtime usage (no Go) from developer convenience auto-build (needs Go).

## What Changes

- Update `README.md` to explicitly document:
  - end-user runtime usage that does not require Go (prebuilt artifacts / packaged wheels)
  - dev convenience auto-build behavior that requires Go toolchain
  - how to disable building by using explicit `artifact_dir` and/or `build_if_missing=False`

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
<!-- doc-only -->
- `usegolib-dev`: developer-facing documentation clarity

## Impact

- Affected docs: `README.md`


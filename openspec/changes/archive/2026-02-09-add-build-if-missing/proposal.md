## Why

In development workflows, users want `usegolib.import_(..., build_if_missing=True)` to "just work": if an artifact is not present under an artifact root, `usegolib` should build it and then load it. This should be safe under concurrent processes (avoid two builds writing to the same directory) and should reuse existing artifacts when available.

## What Changes

- `usegolib.import_()` supports `build_if_missing=True`:
  - If a matching artifact exists: load it.
  - If missing: build into `artifact_dir`, then load it.
- `usegolib build` reuses an existing artifact directory when present (unless forced).
- Builder uses a file lock per artifact leaf directory to prevent concurrent builds corrupting outputs.

## Capabilities

### New Capabilities
- *(none)*

### Modified Capabilities
- `usegolib-core`: import/build behavior in dev mode, caching/reuse semantics

## Impact

- Public API behavior: `build_if_missing` becomes supported (dev-focused).
- CLI: adds `usegolib build --force` (rebuild even if artifact exists).
- Tests: add integration test for import+build in a temp directory (gated behind `USEGOLIB_INTEGRATION=1`).


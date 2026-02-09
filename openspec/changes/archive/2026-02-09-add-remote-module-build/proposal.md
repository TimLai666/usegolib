## Why

Today `usegolib build` only accepts a local Go module directory and always labels the artifact version as `local`. To support CI and real distribution workflows, the builder must also accept a Go module import path and resolve a concrete version (`@latest` default or a pinned version) so artifacts are reproducible and deterministic.

## What Changes

- `usegolib build` accepts `--module` as either:
  - local module directory path, or
  - Go module/package import path
- `--version` is supported:
  - omitted => resolves to `@latest` for remote module paths
  - for local module directories, version remains `local`
- Manifest `version` field is a concrete resolved version for remote modules.

## Capabilities

### New Capabilities
- *(none)*

### Modified Capabilities
- `usegolib-core`: module/version resolution behavior for builder and manifest

## Impact

- New CLI surface: `usegolib build --version ...` and `usegolib package --version ...`
- Builder implementation adds Go module resolution via `go mod download -json`.
- Tests added for resolution behavior (networked remote tests remain optional/gated).


## Why

`usegolib.import_()` currently requires callers to point directly at a single artifact directory. This prevents a realistic workflow where one `artifact_dir` contains multiple modules/versions/platforms (for CI output or wheel embedding), and it does not model subpackage imports cleanly.

## What Changes

- `usegolib.import_()` resolves an artifact from an `artifact_dir` containing many artifacts (by module/package + version + platform).
- Subpackage imports are first-class: importing `example.com/mod/subpkg` returns a handle that calls functions in that package (not always the module root).
- The builder writes artifacts using a stable on-disk layout so runtime lookup is deterministic.

## Capabilities

### New Capabilities
- *(none)*

### Modified Capabilities
- `usegolib-core`: import semantics, artifact discovery, artifact directory layout

## Impact

- Public API behavior: `usegolib.import_()` changes from "artifact_dir must be a single manifest directory" to "artifact_dir is an artifact root; import_ selects the right artifact".
- Builder output layout changes (affects CI/build scripts).
- Tests: update integration tests to use `import_()` with an artifact root.


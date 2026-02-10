# Change: Improve Missing Go Toolchain Error

## Why
When `usegolib` needs to build artifacts (auto-build on import or `usegolib build`) and the Go toolchain is not installed or not on `PATH`, users currently get a raw `FileNotFoundError` traceback. This is confusing and non-actionable.

## What Changes
- Detect "missing `go` executable" failures and raise `BuildError` with an actionable message:
  - install Go / ensure `go` is on `PATH`
  - optionally disable auto-build using `build_if_missing=False` and use prebuilt artifacts/wheels

## Impact
- Affected specs: `usegolib-core`
- Affected code: `src/usegolib/builder/build.py`, `src/usegolib/builder/resolve.py`, `src/usegolib/builder/scan.py`


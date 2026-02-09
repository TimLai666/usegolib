# Change: Strict Artifact Manifest Validation On Load

## Why
Today, the runtime largely trusts `manifest.json` fields like `manifest_version`, `abi_version`, and `goos/goarch`.
Failing fast with clear errors improves safety, debuggability, and makes compatibility boundaries explicit.

## What Changes
- The runtime validates `manifest_version` and `abi_version` are supported before attempting to load a shared library.
- The runtime rejects artifacts built for a different `goos/goarch` than the current host, even when loaded via `load_artifact(...)`.

## Impact
- Affected specs: `usegolib-core`
- Affected code: `src/usegolib/artifact.py`, `src/usegolib/handle.py`
- Tests: new unit tests for unsupported versions and platform mismatch.


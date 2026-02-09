# Change: Pin Go Version For WSL Integration And CI Parity

## Why
Integration tests depend on a Go toolchain. Using "latest/stable" implicitly can introduce drift between CI, Windows-host development, and WSL-based Linux verification.
Pinning a specific Go version in-repo makes the workflow reproducible and easier to debug.

## What Changes
- Add `tools/go-version.txt` as the single source of truth for the Go version used in integration flows.
- Update GitHub Actions integration job to use the pinned version.
- Update the WSL integration runner to default to the pinned version (with env overrides still supported).

## Impact
- Affected specs: `usegolib-dev`
- Affected code/docs: `.github/workflows/ci.yml`, `tools/wsl_linux_tests.ps1`, `docs/testing.md`


# Reproducible Builds Guidance

This repository aims to make artifact builds repeatable enough to debug and verify across machines.

## Recommended Pins

- Go version: use `tools/go-version.txt` (CI uses this pin).
- Zig version: use `tools/zig-version.txt` (CI/WSL integration uses this pin).
- Module versions: prefer pinned semantic versions over `@latest` for anything production-like.

## Environment Notes

- Keep `GOOS/GOARCH` consistent with the target artifact.
- Avoid leaking local state into builds:
  - use a clean module cache when debugging reproducibility issues
  - record `go version` and Zig version in the manifest

## Integrity Outputs

- Ensure `manifest.json` records the shared library SHA256 and that runtime verification stays enabled.


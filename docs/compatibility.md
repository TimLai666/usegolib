# Compatibility Matrix

## Supported Python Versions

- Python: 3.10+

## Supported Platforms

Runtime support is based on Python support plus the ability to load the platform's shared libraries.

- Linux: `amd64`, `arm64`
- macOS: `amd64`, `arm64`
- Windows: `amd64`

## Artifact Compatibility

Artifacts are platform-specific.

- A Linux artifact (`goos=linux`) cannot be loaded on macOS/Windows.
- An `amd64` artifact cannot be loaded on `arm64`, and vice versa.

## Toolchain Pins (Build/CI)

This repository pins toolchain versions for CI parity:

- Go: `tools/go-version.txt`
  - WSL integration tests default to this version unless `USEGOLIB_WSL_GO_VERSION` is set.
- Zig (for cgo `CC`): `tools/zig-version.txt`
  - Builder honors `USEGOLIB_ZIG_VERSION` (optional override).
  - WSL integration tests set `USEGOLIB_ZIG_VERSION` from the pin by default.


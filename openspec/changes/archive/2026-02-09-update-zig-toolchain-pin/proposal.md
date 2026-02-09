# Change: Pin Zig Version For Reproducible Integration Builds

## Why
Integration builds bootstrap Zig automatically. If Zig drifts (latest stable changes), the build environment can change under us, reducing reproducibility and making CI/WSL parity worse.

## What Changes
- Add `tools/zig-version.txt` as the single source of truth for the Zig version used in this repo's integration flows.
- Update CI to set `USEGOLIB_ZIG_VERSION` from `tools/zig-version.txt`.
- Update WSL integration runner to set `USEGOLIB_ZIG_VERSION` from `tools/zig-version.txt` by default.
- Make the WSL runner more robust by using `uv venv -c` (clear existing venv) instead of failing when a venv directory already exists.

## Impact
- Affected specs: `usegolib-dev`
- Affected code/docs: `.github/workflows/ci.yml`, `tools/wsl_linux_tests.ps1`, `docs/testing.md`, `src/usegolib/builder/zig.py`


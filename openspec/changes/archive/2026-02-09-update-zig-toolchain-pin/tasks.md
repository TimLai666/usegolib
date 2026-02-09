## 1. Specs And Validation

- [x] 1.1 Add spec delta and run `openspec validate update-zig-toolchain-pin --strict`

## 2. Implementation

- [x] 2.1 Add `tools/zig-version.txt`
- [x] 2.2 Update CI integration workflow to set `USEGOLIB_ZIG_VERSION` from `tools/zig-version.txt`
- [x] 2.3 Update WSL integration runner to set `USEGOLIB_ZIG_VERSION` from `tools/zig-version.txt` by default
- [x] 2.4 Update `ensure_zig()` to honor `USEGOLIB_ZIG_VERSION`
- [x] 2.5 Make WSL runner venv creation robust (`uv venv -c`)
- [x] 2.6 Update docs (`docs/testing.md`)

## 3. Verification

- [x] 3.1 Run `python -m pytest -q` on Windows host
- [x] 3.2 Run unit tests in WSL via `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run integration tests in WSL via `tools/wsl_linux_tests.ps1 -Integration`
- [x] 3.4 Run `openspec validate --all --strict --no-interactive`

## 1. Specs And Validation

- [x] 1.1 Add spec delta and run `openspec validate update-wsl-integration-toolchain-pin --strict`

## 2. Implementation

- [x] 2.1 Add `tools/go-version.txt` and use it in CI integration job
- [x] 2.2 Update `tools/wsl_linux_tests.ps1 -Integration` to default to the pinned Go version
- [x] 2.3 Update `docs/testing.md` to document the pinned Go version behavior

## 3. Verification

- [x] 3.1 Run `python -m pytest -q` on Windows host
- [x] 3.2 Run `tools/wsl_linux_tests.ps1` on Windows host (WSL Linux unit)
- [x] 3.3 Run `tools/wsl_linux_tests.ps1 -Integration` on Windows host (WSL Linux integration)
- [x] 3.4 Run `openspec validate --all --strict --no-interactive`

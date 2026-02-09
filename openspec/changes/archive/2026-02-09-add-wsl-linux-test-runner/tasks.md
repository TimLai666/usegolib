## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-wsl-linux-test-runner --strict` and fix any schema issues

## 2. Implementation

- [x] 2.1 Add `tools/wsl_linux_tests.ps1` (WSL venv install + pytest)
- [x] 2.2 Add `docs/testing.md` with commands for unit/integration tests on Windows, WSL(Linux), and CI parity notes

## 3. Verification

- [x] 3.1 Run `python -m pytest -q` on Windows host
- [x] 3.2 Run unit tests in WSL via `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run integration tests in WSL via `tools/wsl_linux_tests.ps1 -Integration`
- [x] 3.4 Run `openspec validate --all --strict --no-interactive`

## 1. Specs And Design

- [x] 1.1 Create `proposal.md`
- [x] 1.2 Create delta spec `specs/usegolib-dev/spec.md`
- [x] 1.3 Create `design.md`
- [x] 1.4 Run `openspec validate fix-wsl-runner-stderr-noise --strict --no-interactive`

## 2. Implementation

- [x] 2.1 Update `tools/wsl_linux_tests.ps1` so WSL execution output capture does not emit PowerShell `NativeCommandError` records

## 3. Verification

- [x] 3.1 Run Windows unit tests: `python -m pytest -q`
- [x] 3.2 Run WSL unit tests: `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run WSL integration tests: `tools/wsl_linux_tests.ps1 -Integration`
- [x] 3.4 Run `openspec validate --all --strict --no-interactive`

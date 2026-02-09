## 1. Specs And Validation

- [x] 1.1 Add spec delta and run `openspec validate add-manifest-load-validation --strict`

## 2. Implementation

- [x] 2.1 Reject unsupported `manifest_version` and `abi_version` at manifest read/load time
- [x] 2.2 Reject `goos/goarch` mismatches when loading an artifact into the current process
- [x] 2.3 Add unit tests for version/platform validation failures

## 3. Verification

- [x] 3.1 Run `python -m pytest -q` on Windows host
- [x] 3.2 Run unit tests in WSL via `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

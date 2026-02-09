## 1. Specs And Validation

- [x] 1.1 Add spec delta for shared library SHA256 verification and run `openspec validate add-library-sha256-verification --strict`

## 2. Implementation

- [x] 2.1 Verify `library.sha256` matches the library file bytes before creating `SharedLibClient`
- [x] 2.2 Add unit tests for missing/invalid/mismatched SHA256 and the success path

## 3. Verification

- [x] 3.1 Run `python -m pytest -q` on Windows host
- [x] 3.2 Run unit tests in WSL via `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

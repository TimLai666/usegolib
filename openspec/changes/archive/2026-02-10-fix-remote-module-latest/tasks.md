## 1. Specs And Validation

- [x] 1.1 Run `openspec validate fix-remote-module-latest --strict --no-interactive`

## 2. Implementation

- [x] 2.1 Fix remote version default to `@latest` in `src/usegolib/builder/resolve.py`
- [x] 2.2 Update `README.md` to show remote module import auto-download/build behavior

## 3. Tests

- [x] 3.1 Add unit tests for remote resolver default and package-path trimming

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run `tools/wsl_linux_tests.ps1`
- [x] 4.3 Run `openspec validate --all --strict --no-interactive`

## 1. Specs And Validation

- [x] 1.1 Run `openspec validate update-packager-wheel-install --strict` and fix any schema issues

## 2. Integration Test (TDD)

- [x] 2.1 Add a failing integration test that builds and installs a wheel from a generated project and runs with a sanitized PATH (RED)
- [x] 2.2 Implement minimal changes so the test passes on Windows/macOS/Linux (GREEN)

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run integration tests with `USEGOLIB_INTEGRATION=1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

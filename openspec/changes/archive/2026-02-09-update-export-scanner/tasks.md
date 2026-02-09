## 1. Specs And Validation

- [x] 1.1 Run `openspec validate update-export-scanner --strict` and fix any schema issues

## 2. Integration Test (TDD)

- [x] 2.1 Add failing integration test for grouped parameters (RED)
- [x] 2.2 Implement AST-based scanner and remove `go doc` parsing (GREEN)

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run integration tests with `USEGOLIB_INTEGRATION=1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

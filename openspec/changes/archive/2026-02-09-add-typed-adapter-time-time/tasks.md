## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-typed-adapter-time-time --strict` and fix any schema issues

## 2. Integration Tests (TDD)

- [x] 2.1 Add failing integration test for time.Time in struct fields and function params/results (RED)
- [x] 2.2 Implement time.Time adapter in scanner/signature filter/Go bridge/schema validator (GREEN)

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run integration tests with `USEGOLIB_INTEGRATION=1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-type-bridge-level2 --strict` and fix any schema issues

## 2. Integration Test (TDD)

- [x] 2.1 Add failing integration test for map arguments and map return values (RED)
- [x] 2.2 Implement map support in Go bridge generator and signature filter (GREEN)

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run integration tests with `USEGOLIB_INTEGRATION=1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

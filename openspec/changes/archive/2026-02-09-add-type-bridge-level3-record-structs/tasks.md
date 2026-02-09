## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-type-bridge-level3-record-structs --strict` and fix any schema issues

## 2. Integration Test (TDD)

- [x] 2.1 Add failing integration test for passing/returning record structs (RED)
- [x] 2.2 Implement Level 3 Phase A (record structs) in scanner, signature filter, and Go bridge generator (GREEN)

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run integration tests with `USEGOLIB_INTEGRATION=1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

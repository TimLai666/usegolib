## 1. Specs And Validation

- [x] 1.1 Run `openspec validate update-typed-structs-tags-and-return-validation --strict` and fix any schema issues

## 2. Integration Tests (TDD)

- [x] 2.1 Add failing integration test: tag keys accepted and return uses canonical tag keys (RED)
- [x] 2.2 Implement tag-aware typed structs (Go bridge + schema + runtime validator) (GREEN)

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run integration tests with `USEGOLIB_INTEGRATION=1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

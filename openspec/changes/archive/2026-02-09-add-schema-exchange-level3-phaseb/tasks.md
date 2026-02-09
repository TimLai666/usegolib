## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-schema-exchange-level3-phaseb --strict` and fix any schema issues

## 2. Unit/Integration Tests (TDD)

- [x] 2.1 Add failing test: manifest contains schema for structs and runtime rejects bad struct field type with a schema error (RED)
- [x] 2.2 Implement builder schema emission and runtime schema validation (GREEN)

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run integration tests with `USEGOLIB_INTEGRATION=1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

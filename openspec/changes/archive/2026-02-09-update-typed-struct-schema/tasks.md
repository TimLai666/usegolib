## 1. Specs And Validation

- [x] 1.1 Run `openspec validate update-typed-struct-schema --strict` and fix any schema issues

## 2. Tests (TDD)

- [x] 2.1 Add unit tests for missing required fields and omitempty optional fields (RED)
- [x] 2.2 Extend integration test module with:
  - a struct field tagged `omitempty` that should be omitted on output
  - an ignored field `json:"-"` that must not appear in schema/output
  - an embedded exported field that appears in schema/output (RED)

## 3. Implementation

- [x] 3.1 Extend Go scanner output to include `omitempty` and `embedded` and to skip ignored fields
- [x] 3.2 Emit `required/omitempty/embedded` in manifest schema
- [x] 3.3 Update runtime schema parsing/validation to enforce required fields
- [x] 3.4 Update Go bridge export to respect `omitempty` and ignore tags

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run integration tests with `USEGOLIB_INTEGRATION=1`
- [x] 4.3 Run `openspec validate --all --strict --no-interactive`

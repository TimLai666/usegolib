## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-typed-adapter-uuid --strict` and fix any schema issues

## 2. Tests (TDD)

- [x] 2.1 Add/extend integration test covering:
  - struct field `*uuid.UUID` tagged `omitempty`
  - return value includes UUID as a string
  - function param `uuid.UUID` accepts UUID strings
- [x] 2.2 Add unit tests for schema validator accepting `uuid.UUID` as string

## 3. Implementation

- [x] 3.1 Make Go scanner import-aware and canonicalize google/uuid selector types to `uuid.UUID`
- [x] 3.2 Extend signature filter + adapter detection for `uuid.UUID`
- [x] 3.3 Extend Go bridge:
  - parse `uuid.UUID` from string on input
  - export `uuid.UUID` to string on output
- [x] 3.4 Extend runtime schema + typed wrappers to treat `uuid.UUID` as `str`

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run integration tests with `USEGOLIB_INTEGRATION=1`
- [x] 4.3 Run `openspec validate --all --strict --no-interactive`

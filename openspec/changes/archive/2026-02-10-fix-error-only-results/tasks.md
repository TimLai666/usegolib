## 1. Specs And Validation

- [x] 1.1 Add spec delta for error-only results
- [x] 1.2 Run `openspec validate fix-error-only-results --type change --strict --no-interactive`

## 2. Implementation

- [x] 2.1 Schema validation: accept `error` results as nil
- [x] 2.2 Go bridge: treat `error`-only returns as GoError on non-nil

## 3. Tests

- [x] 3.1 Unit: schema validates error-only result
- [x] 3.2 Integration: error-only return works

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run integration tests (USEGOLIB_INTEGRATION=1)
- [x] 4.3 Run `openspec validate --all --strict --no-interactive`

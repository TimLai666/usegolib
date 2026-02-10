## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-opaque-pointer-return-handles --strict --no-interactive`

## 2. Bridge + Runtime

- [x] 2.1 Detect "opaque" struct types (no exported fields) during build
- [x] 2.2 For results `*T` where `T` is opaque, return object id from `call`/`obj_call` handlers
- [x] 2.3 Runtime: convert returned object ids into `GoObject` for `*T` opaque results
- [x] 2.4 Schema validation: allow int object ids as valid values for `*T` opaque results

## 3. Tests

- [x] 3.1 Integration test: exported function returning `*Opaque` returns a handle usable for method calls

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run integration tests (USEGOLIB_INTEGRATION=1)
- [x] 4.3 Run `openspec validate --all --strict --no-interactive`

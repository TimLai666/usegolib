## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-build-if-missing --strict` and fix any schema issues

## 2. Builder Reuse + Locking (TDD)

- [x] 2.1 Add unit tests for “artifact ready” detection and reuse decisions (RED)
- [x] 2.2 Implement per-leaf file lock context manager (GREEN)
- [x] 2.3 Implement reuse behavior and `--force` flag in `usegolib build` (GREEN)

## 3. import_ build_if_missing (TDD)

- [x] 3.1 Add integration test: import_ with build_if_missing builds then calls a function (RED, gated)
- [x] 3.2 Implement import_ build_if_missing path using builder (GREEN)

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run integration tests with `USEGOLIB_INTEGRATION=1`
- [x] 4.3 Run `openspec validate --all --strict --no-interactive`

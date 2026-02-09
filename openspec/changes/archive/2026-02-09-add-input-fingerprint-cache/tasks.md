## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-input-fingerprint-cache --strict` and fix any schema issues

## 2. Fingerprinting + Reuse (TDD)

- [x] 2.1 Add unit tests for fingerprint comparison in reuse logic (RED)
- [x] 2.2 Implement local module fingerprint computation (GREEN)
- [x] 2.3 Write `input_fingerprint` into manifest for local builds and enforce reuse checks (GREEN)

## 3. Integration (Gated)

- [x] 3.1 Add integration test: local module change triggers rebuild (RED)
- [x] 3.2 Implement minimal fixes until test passes (GREEN)

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run integration tests with `USEGOLIB_INTEGRATION=1`
- [x] 4.3 Run `openspec validate --all --strict --no-interactive`

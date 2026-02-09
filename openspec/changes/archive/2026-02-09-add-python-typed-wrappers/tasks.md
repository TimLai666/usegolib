## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-python-typed-wrappers --strict` and fix any schema issues

## 2. Tests (TDD)

- [x] 2.1 Add unit tests for dataclass generation and encode/decode roundtrips (RED)
- [x] 2.2 Add integration test using typed wrapper:
  - `h.typed().MakePerson(...)` returns a dataclass
  - `h.typed().EchoPerson(Person(...))` accepts a dataclass (RED)

## 3. Implementation

- [x] 3.1 Extend schema parsing to retain canonical field keys per struct field
- [x] 3.2 Implement dataclass generation and encode/decode helpers (new module)
- [x] 3.3 Add `PackageHandle.typed()` wrapper with typed result decoding
- [x] 3.4 Ensure plain `PackageHandle` remains dict-based and backwards compatible

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run integration tests with `USEGOLIB_INTEGRATION=1`
- [x] 4.3 Run `openspec validate --all --strict --no-interactive`

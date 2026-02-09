## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-python-bindings-generator --strict` and fix any schema issues

## 2. Tests (TDD)

- [x] 2.1 Add unit tests for bindings generation output and importability (RED)
- [x] 2.2 Add integration test that:
  - builds an artifact
  - generates bindings module
  - imports the generated module and calls a function end-to-end (RED)

## 3. Implementation

- [x] 3.1 Add `PackageHandle.schema` accessor
- [x] 3.2 Add `typed.package_types_from_classes(...)` to allow decoding into provided dataclasses
- [x] 3.3 Implement `bindgen.generate_python_bindings(...)`
- [x] 3.4 Add `usegolib gen` CLI command

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run integration tests with `USEGOLIB_INTEGRATION=1`
- [x] 4.3 Run `openspec validate --all --strict --no-interactive`

## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-go-object-handles --strict --no-interactive`

## 2. ABI And Docs

- [x] 2.1 Extend `src/usegolib/abi.py` with request encoders for `obj_new/obj_call/obj_free`
- [x] 2.2 Update `docs/abi.md` to document new ops and object-handle semantics

## 3. Builder (Scan + Manifest)

- [x] 3.1 Extend Go scanner to emit exported methods with receiver type
- [x] 3.2 Update `src/usegolib/builder/scan.py` to parse methods
- [x] 3.3 Include methods in manifest schema and/or top-level symbols list

## 4. Bridge Runtime (Go)

- [x] 4.1 Extend `src/usegolib/builder/gobridge.py` to generate:
  - object registry (id -> *T)
  - type map for struct constructors
  - method dispatch wrappers
  - new ops in `usegolib_call`

## 5. Python Runtime API

- [x] 5.1 Add `PackageHandle.object(...) -> GoObject`
- [x] 5.2 Add `GoObject` proxy class with `close()` and context manager
- [x] 5.3 Validate type/methods against schema when available

## 6. Tests

- [x] 6.1 Add integration test module with a struct + methods and verify `obj_new/obj_call/obj_free`

## 7. Verification

- [x] 7.1 Run `python -m pytest -q`
- [x] 7.2 Run integration tests: `USEGOLIB_INTEGRATION=1 python -m pytest -q -k integration`
- [x] 7.3 Run WSL unit tests: `tools/wsl_linux_tests.ps1`
- [x] 7.4 Run WSL integration tests: `tools/wsl_linux_tests.ps1 -Integration`
- [x] 7.5 Run `openspec validate --all --strict --no-interactive`

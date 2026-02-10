## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-generic-functions --strict --no-interactive`

## 2. CLI Surface

- [x] 2.1 Add `usegolib build --generics <path>` flag and plumb to builder

## 3. Builder Scan

- [x] 3.1 Extend Go scanner to emit exported generic function definitions
- [x] 3.2 Parse generic definitions into `ModuleScan`

## 4. Builder Instantiation + Manifest

- [x] 4.1 Parse generics config JSON and validate entries
- [x] 4.2 Instantiate generic signatures (type param substitution) and filter supported instantiations
- [x] 4.3 Include instantiated symbols in `symbols` and `schema.symbols`
- [x] 4.4 Add `schema.generics` mapping to manifest schema

## 5. Bridge Generator (Go)

- [x] 5.1 Generate wrapper functions that call `Fn[T...](...)` for configured instantiations

## 6. Runtime API + Schema

- [x] 6.1 Extend `Schema` to parse `schema.generics` mapping
- [x] 6.2 Add `PackageHandle.generic(name, type_args) -> Callable` (and typed variant)

## 7. Bindgen

- [x] 7.1 Include instantiated generic symbols (and mapping) in generated bindings output

## 8. Docs + Roadmap

- [x] 8.1 Update `docs/roadmap.md` to reflect generic support implementation
- [x] 8.2 Update `README.md` with a generic usage example

## 9. Tests + Verification

- [x] 9.1 Add integration test exercising generic instantiation build + runtime call
- [x] 9.2 Run `python -m pytest -q`
- [x] 9.3 Run integration tests: `USEGOLIB_INTEGRATION=1 python -m pytest -q -k integration`
- [x] 9.4 Run WSL unit tests: `tools/wsl_linux_tests.ps1`
- [x] 9.5 Run WSL integration tests: `tools/wsl_linux_tests.ps1 -Integration`
- [x] 9.6 Run `openspec validate --all --strict --no-interactive`

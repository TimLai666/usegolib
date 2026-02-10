## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-any-and-variadic-support --strict --no-interactive`

## 2. Scanner

- [x] 2.1 Extend Go scanner to detect variadic parameters and render `...T`

## 3. Builder Support Filter

- [x] 3.1 Treat `any` as supported type
- [x] 3.2 Treat `...T` as supported when `T` is supported

## 4. Bridge Generator (Go)

- [x] 4.1 Support `any`, `[]any`, `map[string]any`, and `[]map[string]any` in arg conversion
- [x] 4.2 Support returning `any` by exporting through `exportAny` (including interface unwrapping)
- [x] 4.3 Call variadic symbols using slice expansion for the last argument (`arg...`)

## 5. Runtime + Schema

- [x] 5.1 Extend schema parsing/validation to understand `...T` and `any`
- [x] 5.2 Pack Python varargs for variadic symbols before ABI encoding

## 6. Examples + Docs

- [x] 6.1 Update `examples/insyra_basic.py` to use auto-download (`import_` with `version="v0.2.14"`) and demonstrate DataList/DataTable
- [x] 6.2 Update `docs/abi.md` (type bridge section) for `any` and variadic behavior

## 7. Verification

- [x] 7.1 Run `python -m pytest -q`
- [x] 7.2 Run integration tests: `USEGOLIB_INTEGRATION=1 python -m pytest -q -k integration`
- [x] 7.3 Run WSL unit tests: `tools/wsl_linux_tests.ps1`
- [x] 7.4 Run WSL integration tests: `tools/wsl_linux_tests.ps1 -Integration`
- [x] 7.5 Run `openspec validate --all --strict --no-interactive`

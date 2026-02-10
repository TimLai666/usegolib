## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-godoc-docstrings --strict --no-interactive`

## 2. Scanner + Manifest

- [x] 2.1 Extract doc comments for exported functions and methods via Go AST comments (`parser.ParseComments`)
- [x] 2.2 Emit `doc` fields into manifest `schema.symbols` and `schema.methods`

## 3. Runtime + Bindgen

- [x] 3.1 Parse `doc` fields into schema doc maps
- [x] 3.2 Attach docstrings to dynamic callables returned by `PackageHandle.__getattr__` and `GoObject.__getattr__`
- [x] 3.3 Emit docstrings in `usegolib bindgen` generated modules

## 4. Tests

- [x] 4.1 Unit test: schema parses docs + bindgen output includes docstring text

## 5. Verification

- [x] 5.1 Run `python -m pytest -q`
- [x] 5.2 Run `openspec validate --all --strict --no-interactive`

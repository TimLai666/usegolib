## 1. Specs And Validation

- [x] 1.1 Update usegolib-core spec to require docstrings for all dynamic callables
- [x] 1.2 Run `openspec validate improve-godoc-visibility --type change --strict --no-interactive`

## 2. Implementation

- [x] 2.1 Runtime: attach GoDoc or signature fallback for all functions and methods (handles + typed wrappers)
- [x] 2.2 Builder: include doc for concrete generic instantiation symbols

## 3. Tests

- [x] 3.1 Unit: runtime attaches docs for functions/methods and preserves in typed wrappers

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run `openspec validate --all --strict --no-interactive`

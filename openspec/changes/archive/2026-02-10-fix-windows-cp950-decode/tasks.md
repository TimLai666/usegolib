## 1. Specs And Validation

- [x] 1.1 Add spec delta for Windows locale-safe Go subprocess output decoding
- [x] 1.2 Run `openspec validate fix-windows-cp950-decode --type change --strict --no-interactive`

## 2. Implementation

- [x] 2.1 Decode Go subprocess output as UTF-8 bytes (avoid cp950 UnicodeDecodeError)
- [x] 2.2 Make JSON parsing robust to non-JSON prefix lines

## 3. Tests

- [x] 3.1 Unit: non-UTF8 prefix does not crash resolve/scan

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run `openspec validate --all --strict --no-interactive`

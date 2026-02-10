## 1. Specs And Validation

- [x] 1.1 Add spec delta: version=None follows already loaded module version
- [x] 1.2 Run `openspec validate follow-loaded-version-on-import --type change --strict --no-interactive`

## 2. Implementation

- [x] 2.1 Importer: if module already loaded and version omitted, use loaded version

## 3. Tests

- [x] 3.1 Unit: import_ avoids ambiguity by following loaded version

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run `openspec validate --all --strict --no-interactive`

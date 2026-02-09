## 1. Specs And Validation

- [x] 1.1 Run `openspec validate update-import-resolution --strict` and fix any schema issues

## 2. Runtime Import Resolution

- [x] 2.1 Add `AmbiguousArtifactError` and runtime artifact resolution (scan + select) tests (RED)
- [x] 2.2 Implement artifact scanning + selection logic for `import_()` (GREEN)
- [x] 2.3 Introduce `PackageHandle` (bound package path) and update call routing to send `pkg` correctly (GREEN)
- [x] 2.4 Update/extend unit tests for version conflict + ambiguous artifact behavior (GREEN)

## 3. Builder Output Layout

- [x] 3.1 Update `usegolib build` to write into `<out>/<module>@<version>/<goos>-<goarch>/` (RED)
- [x] 3.2 Update integration test to call `import_()` using an artifact root (GREEN)

## 4. Verification

- [x] 4.1 Run `python -m pytest -q` (unit)
- [x] 4.2 Run integration test with `USEGOLIB_INTEGRATION=1` (build + call)

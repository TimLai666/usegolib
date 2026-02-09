## 1. Specs And Validation

- [x] 1.1 Run `openspec validate update-import-auto-build --strict --no-interactive`

## 2. Implementation

- [x] 2.1 Add `USEGOLIB_ARTIFACT_DIR` default artifact root resolution (`src/usegolib/paths.py`)
- [x] 2.2 Update `usegolib.import_` to allow `artifact_dir=None` (use default root)
- [x] 2.3 Update `usegolib.import_` to support `build_if_missing=None` auto behavior
- [x] 2.4 Update `usegolib.import_` to support local subpackage directory imports (map to correct package import path)
- [x] 2.5 Update builder local resolution to accept subdirectories (walk up to find `go.mod`)

## 3. Tests

- [x] 3.1 Add unit test for module-root discovery when target is a subdirectory
- [x] 3.2 Add integration test: `import_` without `artifact_dir` auto-builds into `USEGOLIB_ARTIFACT_DIR`
- [x] 3.3 Add integration test: importing a subpackage auto-builds and binds to the subpackage

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run `tools/wsl_linux_tests.ps1`
- [x] 4.3 Run `openspec validate --all --strict --no-interactive`

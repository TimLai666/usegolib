## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-remote-module-build --strict` and fix any schema issues

## 2. Builder CLI (TDD)

- [x] 2.1 Add failing tests for module/version resolution (local path vs import path behavior) (RED)
- [x] 2.2 Implement module/version resolution helper using `go mod download -json` (GREEN)
- [x] 2.3 Extend `usegolib build` with `--version` and `--module` accepting import paths (GREEN)
- [x] 2.4 Extend `usegolib package` with `--version` passthrough (GREEN)

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run `openspec validate --all --strict --no-interactive`

## 1. Specs And Validation

- [x] 1.1 Run `openspec validate add-packager-v0 --strict` and fix any schema issues

## 2. CLI + Generator (TDD)

- [x] 2.1 Add failing tests for `usegolib package` project layout (RED)
- [x] 2.2 Implement `usegolib package` to generate the project skeleton + embed artifacts (GREEN)
- [x] 2.3 Add tests that install the generated project into a temp venv and load the artifact (optional; gated behind env var) (RED/GREEN)

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run `openspec validate --all --strict --no-interactive`

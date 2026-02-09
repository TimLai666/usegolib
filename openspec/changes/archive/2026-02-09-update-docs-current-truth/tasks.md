## 1. Specs And Validation

- [x] 1.1 Run `openspec validate update-docs-current-truth --strict`

## 2. Documentation And Code

- [x] 2.1 Update `docs/abi.md` to reflect v0.x: Level 1/2/3, typed adapters, and schema exchange boundaries
- [x] 2.2 Update `README.md` and any outdated docstrings/comments about builder/runtime behavior
- [x] 2.3 Make `usegolib version` print the installed package version

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run WSL unit tests via `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

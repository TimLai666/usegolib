## 1. Specs And Validation

- [x] 1.1 Run `openspec validate update-roadmap-methods-generics --strict --no-interactive`

## 2. Documentation

- [x] 2.1 Update `docs/roadmap.md` with milestones for methods + generics support
- [x] 2.2 Clarify `README.md` examples for remote import paths
- [x] 2.3 Clarify CLI help for `usegolib build/package --module` (dir or import path)

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

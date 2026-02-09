## 1. Specs And Design

- [x] 1.1 Create `proposal.md`
- [x] 1.2 Create delta spec `specs/usegolib-dev/spec.md`
- [x] 1.3 Create `design.md`
- [x] 1.4 Run `openspec validate add-v1-policy-docs --strict --no-interactive`

## 2. Documentation

- [x] 2.1 Add `docs/versioning.md`
- [x] 2.2 Add `docs/compatibility.md`
- [x] 2.3 Add `docs/security.md`
- [x] 2.4 Add `docs/reproducible-builds.md`
- [x] 2.5 Link policy docs from `README.md`

## 3. Verification

- [x] 3.1 Run Windows tests: `python -m pytest -q`
- [x] 3.2 Run WSL unit tests: `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

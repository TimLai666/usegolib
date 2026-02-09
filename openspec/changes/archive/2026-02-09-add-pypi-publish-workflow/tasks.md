## 1. Specs And Design

- [x] 1.1 Create `proposal.md`
- [x] 1.2 Create delta spec `specs/usegolib-dev/spec.md`
- [x] 1.3 Create `design.md`
- [x] 1.4 Run `openspec validate add-pypi-publish-workflow --strict --no-interactive`

## 2. Implementation

- [x] 2.1 Add `.github/workflows/publish-pypi.yml`
- [x] 2.2 Update `docs/releasing.md` with PyPI trusted publishing setup + publish steps

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

## 1. Specs And Design

- [x] 1.1 Create `proposal.md`
- [x] 1.2 Create delta spec `specs/usegolib-dev/spec.md`
- [x] 1.3 Create `design.md`
- [x] 1.4 Run `openspec validate release-v0-1-0 --strict --no-interactive`

## 2. Implementation

- [x] 2.1 Bump `pyproject.toml` version to `0.1.0`
- [x] 2.2 Add tag/version match guard to `.github/workflows/release.yml`
- [x] 2.3 Update `docs/releasing.md` to document the guardrail

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

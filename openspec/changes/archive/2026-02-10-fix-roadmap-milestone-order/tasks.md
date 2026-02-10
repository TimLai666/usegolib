## 1. Specs And Design

- [x] 1.1 Create `proposal.md`
- [x] 1.2 Create `design.md`
- [x] 1.3 Create delta spec `specs/usegolib-dev/spec.md`
- [x] 1.4 Run `openspec validate fix-roadmap-milestone-order --strict --no-interactive`

## 2. Documentation

- [x] 2.1 Reorder milestones in `docs/roadmap.md` so 5 is before 6
- [x] 2.2 Add a sequencing note about Milestone 6 placement

## 3. Verification

- [x] 3.1 Run `python -m pytest -q`
- [x] 3.2 Run `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

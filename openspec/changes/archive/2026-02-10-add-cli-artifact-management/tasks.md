## 1. Specs And Validation

- [x] 1.1 Add spec deltas for CLI artifact management + redownload support
- [x] 1.2 Run `openspec validate add-cli-artifact-management --type change --strict --no-interactive`

## 2. Implementation

- [x] 2.1 Builder: allow passing `GOMODCACHE` through resolve/scan/build steps
- [x] 2.2 CLI: `usegolib build --redownload/--gomodcache`
- [x] 2.3 CLI: `usegolib artifact rm` and `usegolib artifact rebuild`
- [x] 2.4 Artifact module: implement delete helpers and index rebuild
- [x] 2.5 Docs: add `docs/cli.md` and link from README / troubleshooting

## 3. Tests

- [x] 3.1 Unit: artifact delete helpers
- [x] 3.2 Unit: builder resolve tests updated for env plumbing

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run `openspec validate --all --strict --no-interactive`

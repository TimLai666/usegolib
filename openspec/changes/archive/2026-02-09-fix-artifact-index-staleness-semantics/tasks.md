## 1. Specs And Validation

- [x] 1.1 Add spec delta and run `openspec validate fix-artifact-index-staleness-semantics --strict`

## 2. Implementation

- [x] 2.1 Ensure artifact index cache does not change ambiguity behavior when version is omitted
- [x] 2.2 Add regression test: index built with one version, second version added later, version omitted => ambiguous

## 3. Verification

- [x] 3.1 Run `python -m pytest -q` on Windows host
- [x] 3.2 Run unit tests in WSL via `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

## 1. Specs And Validation

- [x] 1.1 Add spec delta and run `openspec validate add-artifact-index-cache --strict`

## 2. Implementation

- [x] 2.1 Add on-disk artifact index file under the artifact root (lazy build, atomic write)
- [x] 2.2 Use the index for `resolve_manifest`, with fallback scan + index rebuild on misses/stale entries
- [x] 2.3 Add unit tests for index creation, stale index fallback, and "new manifest after index" discovery

## 3. Verification

- [x] 3.1 Run `python -m pytest -q` on Windows host
- [x] 3.2 Run unit tests in WSL via `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

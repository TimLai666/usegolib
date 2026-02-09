## 1. Specs And Validation

- [x] 1.1 Add spec delta and run `openspec validate add-zig-download-verification --strict`

## 2. Implementation

- [x] 2.1 Validate Zig index/tarball URLs are `https://ziglang.org/...`
- [x] 2.2 Verify the downloaded archive SHA256 using the digest provided in Zig `index.json`
- [x] 2.3 Perform safe extraction for zip and tar archives (reject path traversal)
- [x] 2.4 Add unit tests covering: missing digest, mismatched digest, and safe extraction behavior

## 3. Verification

- [x] 3.1 Run `python -m pytest -q` on Windows host
- [x] 3.2 Run unit tests in WSL via `tools/wsl_linux_tests.ps1`
- [x] 3.3 Run `openspec validate --all --strict --no-interactive`

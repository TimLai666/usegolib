# Change: Verify Zig Downloads (Source + SHA256) And Safe Extraction

## Why
The builder bootstraps Zig by downloading an archive from the Zig download index. Today we do not verify the archive hash and we use direct `extractall`, which are avoidable risks.
Hardening improves supply-chain safety and prevents malicious archive path traversal.

## What Changes
- Restrict Zig downloads to `https://ziglang.org/...` URLs.
- Verify the downloaded archive SHA256 against the digest published in Zig's `index.json`.
- Extract archives safely (reject path traversal and absolute paths).

## Impact
- Affected specs: `usegolib-core`
- Affected code: `src/usegolib/builder/zig.py`
- Tests: add unit tests for hash verification and safe extraction.


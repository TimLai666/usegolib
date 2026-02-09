# Security Policy And Boundaries

This document describes what `usegolib` verifies, what it does not, and the expected trust boundaries.

## Threat Model (In Scope)

- Accidental corruption or tampering of built artifacts (shared libraries) on disk.
- Unsafe archive extraction when bootstrapping build tools.

## Threat Model (Out Of Scope)

- Malicious Go modules: building and loading arbitrary native code is inherently unsafe. If you do not trust the source, do not build/load it.
- Sandbox escape: artifacts run as native code inside the Python process.

## Current Hardening

- Artifact shared library integrity is verified against `manifest.json` SHA256 before loading.
- Zig bootstrap downloads are restricted to `https://ziglang.org/...` and SHA256-verified using Zig's published metadata.
- Zig archive extraction rejects absolute paths and path traversal entries.

## Operator Guidance

- Prefer shipping wheels containing prebuilt artifacts for end-users.
- Pin module versions for production (avoid `@latest`).
- Treat artifact roots as an integrity-sensitive directory (no untrusted writes).


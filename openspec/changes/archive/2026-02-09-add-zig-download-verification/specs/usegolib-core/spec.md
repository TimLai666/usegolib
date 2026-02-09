## ADDED Requirements

### Requirement: Zig Download Verification (V0.x)
When bootstrapping Zig automatically, the builder SHALL verify the Zig download integrity and SHALL extract archives safely.

The builder MUST:
- fetch Zig download metadata only from `https://ziglang.org/...`
- download Zig archives only from `https://ziglang.org/...`
- verify the archive SHA256 using the digest provided by Zig's download metadata
- reject unsafe archive paths (absolute paths or path traversal) during extraction

#### Scenario: Mismatched Zig archive SHA256 is rejected
- **WHEN** the builder downloads a Zig archive whose SHA256 does not match the metadata digest
- **THEN** the builder SHALL raise `BuildError` and MUST NOT use the downloaded archive

#### Scenario: Unsafe archive paths are rejected
- **WHEN** a Zig archive contains an unsafe path (absolute or path traversal)
- **THEN** the builder SHALL raise `BuildError` and MUST NOT extract the unsafe entry


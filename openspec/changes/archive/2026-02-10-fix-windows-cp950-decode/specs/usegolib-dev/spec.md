## ADDED Requirements

### Requirement: Windows Builder Output Decoding Is Locale-Safe
The builder SHALL not fail with `UnicodeDecodeError` on Windows due to non-UTF8 locale encodings when capturing Go tool output.

#### Scenario: Go tool output contains non-UTF8 bytes under Windows locale
- **WHEN** the builder captures stdout/stderr from Go tools on Windows
- **AND WHEN** the system locale encoding cannot decode those bytes (for example `cp950`)
- **THEN** the build/scan process does not crash with `UnicodeDecodeError`
- **AND THEN** errors are reported as `BuildError` when the underlying Go command fails


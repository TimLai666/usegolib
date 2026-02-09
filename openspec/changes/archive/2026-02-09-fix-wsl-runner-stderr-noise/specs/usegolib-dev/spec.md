## MODIFIED Requirements

### Requirement: WSL Linux Test Runner Script
The repository SHALL include a Windows PowerShell script to run the test suite inside WSL (Linux) for local verification.

The WSL runner SHALL capture combined stdout/stderr from WSL execution without producing PowerShell error records for expected stderr output.

For integration runs, the WSL runner SHALL:
- use a pinned Go toolchain version from `tools/go-version.txt` by default (unless overridden)
- set `USEGOLIB_ZIG_VERSION` from `tools/zig-version.txt` by default (unless overridden), to improve parity with CI

#### Scenario: Run unit tests in WSL
- **WHEN** a developer runs the provided WSL test runner script
- **THEN** unit tests execute successfully inside WSL (Linux)

#### Scenario: Run integration tests in WSL
- **WHEN** a developer runs the provided WSL test runner script with integration enabled
- **THEN** integration tests execute inside WSL (Linux) using the Go toolchain and Zig bootstrap as needed

#### Scenario: Integration Go version is pinned by default
- **WHEN** a developer runs the WSL test runner script with integration enabled
- **AND WHEN** `USEGOLIB_WSL_GO_VERSION` is not set
- **THEN** the runner uses the Go version from `tools/go-version.txt` by default

#### Scenario: Integration Zig version is pinned by default
- **WHEN** a developer runs the WSL test runner script with integration enabled
- **AND WHEN** `USEGOLIB_ZIG_VERSION` is not set
- **THEN** the runner sets `USEGOLIB_ZIG_VERSION` from `tools/zig-version.txt` by default

#### Scenario: Expected stderr output does not produce PowerShell error records
- **WHEN** the WSL test runner executes commands that emit progress logs on stderr (for example tool bootstrap output)
- **THEN** the script output does not include PowerShell `NativeCommandError` records


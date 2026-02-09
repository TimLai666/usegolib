# usegolib-dev Specification

## Purpose
Developer-facing workflows and tooling for this repository (local verification, CI parity, and related utilities).

## Requirements
### Requirement: WSL Linux Test Runner Script
The repository SHALL include a Windows PowerShell script to run the test suite inside WSL (Linux) for local verification.

#### Scenario: Run unit tests in WSL
- **WHEN** a developer runs the provided WSL test runner script
- **THEN** unit tests execute successfully inside WSL (Linux)

#### Scenario: Run integration tests in WSL
- **WHEN** a developer runs the provided WSL test runner script with integration enabled
- **THEN** integration tests execute inside WSL (Linux) using the Go toolchain and Zig bootstrap as needed

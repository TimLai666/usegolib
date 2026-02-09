# usegolib-dev Specification

## Purpose
Developer-facing workflows and tooling for this repository (local verification, CI parity, and related utilities).
## Requirements
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

### Requirement: Developer Docs Match Current Behavior
The repository SHALL keep developer-facing documentation aligned with current `usegolib` behavior so users do not rely on outdated assumptions.

#### Scenario: ABI documentation reflects supported types
- **WHEN** the repository supports Level 2/3 type bridging and typed adapters in v0.x
- **THEN** `docs/abi.md` describes the supported type levels and their wire encodings

### Requirement: Repository Policy Docs
The repository SHALL contain developer-facing policy documentation describing compatibility/versioning rules, security boundaries, and reproducible build guidance.

At minimum, the repository SHALL provide the following documents:
- `docs/versioning.md`
- `docs/compatibility.md`
- `docs/security.md`
- `docs/reproducible-builds.md`

#### Scenario: Policy docs exist
- **WHEN** a developer checks the repository documentation
- **THEN** the policy documents exist at the documented paths

### Requirement: Tag-Triggered Release Workflow
The repository SHALL provide a GitHub Actions workflow that builds release distributions when a version tag is pushed.

The release workflow MUST:
- validate OpenSpec specs (`openspec validate --all --strict --no-interactive`)
- run the Python test suite
- enforce that the pushed tag version matches `pyproject.toml` `project.version`
- build `sdist` and `wheel` into `dist/`
- upload `dist/*` as GitHub Release assets for the tag

#### Scenario: Pushing a version tag produces release assets
- **WHEN** a maintainer pushes a tag matching `v*`
- **THEN** the workflow runs validation and tests
- **AND THEN** the workflow enforces the tag matches the project version
- **AND THEN** the workflow builds `sdist` and `wheel`
- **AND THEN** the workflow uploads the built distributions as release assets

### Requirement: Releasing Documentation
The repository SHALL include `docs/releasing.md` describing the exact steps to perform a release and what artifacts are produced.

#### Scenario: Releasing docs exist
- **WHEN** a maintainer prepares a release
- **THEN** `docs/releasing.md` exists and documents the release steps and outputs

### Requirement: PyPI Publishing Workflow
The repository SHALL provide a GitHub Actions workflow to publish `usegolib` distributions to PyPI using trusted publishing (OIDC) without storing long-lived credentials in repository secrets.

The workflow MUST:
- build `sdist` and `wheel` into `dist/`
- request OIDC token permissions (`id-token: write`)
- publish to PyPI (or TestPyPI) using `pypa/gh-action-pypi-publish`

#### Scenario: Maintainer can publish to PyPI without tokens
- **WHEN** a maintainer runs the PyPI publish workflow
- **THEN** the workflow publishes the built distributions using trusted publishing


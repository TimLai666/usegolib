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

### Requirement: Roadmap Includes Planned Method And Generics Support
The repository SHALL maintain `docs/roadmap.md` to include planned milestones for future support of exported Go methods and generic functions.

#### Scenario: Roadmap describes future method and generics milestones
- **WHEN** a developer reviews `docs/roadmap.md`
- **THEN** it includes explicit milestones describing planned support for exported methods and generic functions

### Requirement: README Clarifies Go Toolchain Requirement
The repository SHALL document in `README.md` when the Go toolchain is required (auto-build/build workflows) versus when it is not required (runtime with prebuilt artifacts/wheels).

#### Scenario: README includes a "Do users need Go?" section
- **WHEN** a developer reads `README.md`
- **THEN** it contains a section explaining that end-users do not need Go when using prebuilt artifacts/wheels
- **AND THEN** it explains that auto-build (downloading/building missing artifacts) requires a Go toolchain

### Requirement: Roadmap Milestone Ordering Is Consistent
The repository SHALL keep `docs/roadmap.md` milestones ordered by increasing milestone number to avoid confusion about sequencing.

#### Scenario: Milestones are ordered
- **WHEN** a developer reads `docs/roadmap.md`
- **THEN** Milestone sections appear in increasing numerical order (e.g. 4, 5, 6)

### Requirement: Troubleshooting Documentation
The repository SHALL include `docs/troubleshooting.md` covering common failures and remedies for building/loading/importing artifacts.

#### Scenario: Ambiguous artifacts mention already-loaded version behavior
- **WHEN** a developer reads the `AmbiguousArtifactError` section in `docs/troubleshooting.md`
- **THEN** it explains that ambiguity applies when the module is not already loaded
- **AND THEN** it notes that `import_(..., version=None)` follows the already-loaded version within a process

#### Scenario: Network/proxy failures mention GOPROXY remediation
- **WHEN** a developer reads the build-related troubleshooting for Go module download failures
- **THEN** it mentions proxy/network errors can be transient
- **AND THEN** it includes a remediation hint mentioning `GOPROXY=direct`

### Requirement: Roadmap Avoids Misleading Internal Version Numbers
The repository SHALL keep `docs/roadmap.md` version-agnostic for unreleased work and MUST NOT assign misleading internal version ranges to future milestones.

#### Scenario: Roadmap does not claim internal version ranges
- **WHEN** a developer reads `docs/roadmap.md`
- **THEN** future milestones do not include internal version ranges like `v0.X - v0.Y`

### Requirement: CLI Supports Artifact Cache Management
The CLI SHALL accept `@version` syntax when targeting a specific module/package version for artifact cache operations.

#### Scenario: Delete a specific cached version
- **WHEN** a user runs `usegolib artifact rm --module <module-or-package>@<vX.Y.Z> --yes`
- **THEN** the matching artifact directory for the current platform is deleted

#### Scenario: Rebuild cached artifacts
- **WHEN** a user runs `usegolib artifact rebuild --module <module-or-package>@<vX.Y.Z>`
- **THEN** the artifact is rebuilt into the selected artifact root

### Requirement: CLI Can Re-Download Go Modules Before Rebuild
The CLI SHALL accept `@version` syntax for remote module builds when re-downloading sources.

#### Scenario: Re-download before build
- **WHEN** a user runs `usegolib build --module <module-or-package>@<vX.Y.Z> --out <dir> --redownload`
- **THEN** the build uses an isolated `GOMODCACHE` and clears that cache before building

### Requirement: CLI Usage Documentation
The repository SHALL document CLI installation and usage, including artifact cache deletion and rebuild workflows.

#### Scenario: CLI docs exist
- **WHEN** a user reads the repository documentation
- **THEN** `docs/cli.md` exists and documents `usegolib build` and `usegolib artifact` commands

### Requirement: Windows Builder Output Decoding Is Locale-Safe
The builder SHALL not fail with `UnicodeDecodeError` on Windows due to non-UTF8 locale encodings when capturing Go tool output.

#### Scenario: Go tool output contains non-UTF8 bytes under Windows locale
- **WHEN** the builder captures stdout/stderr from Go tools on Windows
- **AND WHEN** the system locale encoding cannot decode those bytes (for example `cp950`)
- **THEN** the build/scan process does not crash with `UnicodeDecodeError`
- **AND THEN** errors are reported as `BuildError` when the underlying Go command fails


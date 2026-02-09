## ADDED Requirements

### Requirement: Tag-Triggered Release Workflow
The repository SHALL provide a GitHub Actions workflow that builds release distributions when a version tag is pushed.

The release workflow MUST:
- validate OpenSpec specs (`openspec validate --all --strict --no-interactive`)
- run the Python test suite
- build `sdist` and `wheel` into `dist/`
- upload `dist/*` as GitHub Release assets for the tag

#### Scenario: Pushing a version tag produces release assets
- **WHEN** a maintainer pushes a tag matching `v*`
- **THEN** the workflow runs validation and tests
- **AND THEN** the workflow builds `sdist` and `wheel`
- **AND THEN** the workflow uploads the built distributions as release assets

### Requirement: Releasing Documentation
The repository SHALL include `docs/releasing.md` describing the exact steps to perform a release and what artifacts are produced.

#### Scenario: Releasing docs exist
- **WHEN** a maintainer prepares a release
- **THEN** `docs/releasing.md` exists and documents the release steps and outputs


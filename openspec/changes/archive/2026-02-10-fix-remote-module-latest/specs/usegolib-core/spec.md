## MODIFIED Requirements

### Requirement: Module And Version Resolution (Build)
When building artifacts from a Go import path, the system SHALL resolve a concrete module version and record it in the artifact manifest.

#### Scenario: Version omitted defaults to @latest for remote modules
- **WHEN** `usegolib build` is invoked with a Go module import path and `version=None`
- **THEN** the system resolves the version query to `@latest`
- **AND THEN** the manifest `version` field contains the resolved concrete version

#### Scenario: Pinned version is used as-is for remote modules
- **WHEN** `usegolib build` is invoked with a Go module import path and `version="vX.Y.Z"`
- **THEN** the system builds using `vX.Y.Z`
- **AND THEN** the manifest `version` field MUST equal `vX.Y.Z`

#### Scenario: Local module directories use version "local"
- **WHEN** `usegolib build` is invoked with a local module directory
- **THEN** the manifest `version` field MUST be `"local"`


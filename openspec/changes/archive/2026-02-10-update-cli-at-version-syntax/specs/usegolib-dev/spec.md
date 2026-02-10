## MODIFIED Requirements

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

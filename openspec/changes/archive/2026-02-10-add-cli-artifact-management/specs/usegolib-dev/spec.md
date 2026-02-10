## ADDED Requirements

### Requirement: CLI Supports Artifact Cache Management
The repository SHALL provide CLI commands to manage locally cached artifacts for the current platform.

At minimum, the CLI SHALL support:
- deleting cached artifacts by module/package and version
- deleting all cached versions for a module/package
- rebuilding cached artifacts

#### Scenario: Delete a specific cached version
- **WHEN** a user runs `usegolib artifact rm --module <module-or-package> --version <vX.Y.Z> --yes`
- **THEN** the matching artifact directory for the current platform is deleted

#### Scenario: Delete all cached versions
- **WHEN** a user runs `usegolib artifact rm --module <module-or-package> --all-versions --yes`
- **THEN** all cached versions for the current platform are deleted

#### Scenario: Rebuild cached artifacts
- **WHEN** a user runs `usegolib artifact rebuild --module <module-or-package> --version <vX.Y.Z>`
- **THEN** the artifact is rebuilt into the selected artifact root

### Requirement: CLI Can Re-Download Go Modules Before Rebuild
The CLI SHALL support rebuilding an artifact while forcing a fresh module download without mutating the user's global Go module cache.

#### Scenario: Re-download before build
- **WHEN** a user runs `usegolib build --module <module-or-package> --version <vX.Y.Z> --out <dir> --redownload`
- **THEN** the build uses an isolated `GOMODCACHE` and clears that cache before building

### Requirement: CLI Usage Documentation
The repository SHALL document CLI installation and usage, including artifact cache deletion and rebuild workflows.

#### Scenario: CLI docs exist
- **WHEN** a user reads the repository documentation
- **THEN** `docs/cli.md` exists and documents `usegolib build` and `usegolib artifact` commands


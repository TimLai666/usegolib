## MODIFIED Requirements

### Requirement: Python Import API
The system SHALL expose a Python API that imports a Go module or subpackage and returns a handle that can be used to call exported Go identifiers.

#### Scenario: Import root module from an artifact root
- **WHEN** Python calls `usegolib.import_("example.com/mod", version=None, artifact_dir="out/")`
- **THEN** the system searches `artifact_dir` for a matching artifact for the current OS/arch
- **AND THEN** the system loads the matching shared library into the current Python process
- **AND THEN** the call returns a handle bound to package `example.com/mod`

#### Scenario: Import subpackage returns a handle bound to that package
- **WHEN** Python calls `usegolib.import_("example.com/mod/subpkg", version=None, artifact_dir="out/")`
- **THEN** the system loads a matching artifact that contains package `example.com/mod/subpkg`
- **AND THEN** the call returns a handle bound to package `example.com/mod/subpkg`

#### Scenario: Import chooses a specific version when provided
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="v1.2.3", artifact_dir="out/")`
- **THEN** the system MUST load version `v1.2.3` for that module/package (if present)

#### Scenario: Import fails when version is omitted but ambiguous
- **WHEN** Python calls `usegolib.import_("example.com/mod", version=None, artifact_dir="out/")`
- **AND WHEN** `artifact_dir` contains more than one version for `example.com/mod` for the current OS/arch
- **THEN** the import MUST fail
- **AND THEN** the system SHALL raise `AmbiguousArtifactError`

## ADDED Requirements

### Requirement: Artifact Directory Layout (v0)
The builder SHALL write artifacts to disk using a stable layout so runtime lookup by module/package, version, and platform is deterministic.

#### Scenario: Builder output layout
- **WHEN** an artifact is built for module `example.com/mod` at version `vX.Y.Z` on OS `GOOS` and arch `GOARCH`
- **THEN** the builder writes `manifest.json` under `<out>/example.com/mod@vX.Y.Z/<GOOS>-<GOARCH>/manifest.json`
- **AND THEN** the shared library file path in the manifest is relative to that manifest directory


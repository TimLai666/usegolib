## MODIFIED Requirements

### Requirement: Python Import API
The system SHALL expose a Python API that imports a Go module or subpackage and returns a handle that can be used to call exported Go identifiers.

#### Scenario: Import root module from the default artifact root
- **WHEN** Python calls `usegolib.import_("example.com/mod", version=None)`
- **THEN** the system searches the default artifact root for a matching artifact for the current OS/arch
- **AND THEN** the system loads the matching shared library into the current Python process
- **AND THEN** the call returns a handle bound to package `example.com/mod`

#### Scenario: Import root module from an explicit artifact root
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

### Requirement: Import Builds Missing Artifacts (Dev Mode)
When `build_if_missing=True`, the system SHALL build a missing artifact into the artifact root and then load it.

When `build_if_missing=None` (auto), the system SHALL:
- build missing artifacts when `artifact_dir` is omitted (using the default artifact root)
- NOT build missing artifacts when `artifact_dir` is explicitly provided

#### Scenario: Import triggers build when artifact is missing
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z", artifact_dir="out/", build_if_missing=True)`
- **AND WHEN** no matching artifact exists under `artifact_dir` for the current OS/arch
- **THEN** the system builds the artifact into `artifact_dir`
- **AND THEN** the system loads the newly built artifact and returns a handle

#### Scenario: Import auto-builds when artifact_dir is omitted
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z", build_if_missing=None)`
- **AND WHEN** no matching artifact exists under the default artifact root for the current OS/arch
- **THEN** the system builds the artifact into the default artifact root
- **AND THEN** the system loads the newly built artifact and returns a handle

#### Scenario: Import does not build by default when artifact_dir is provided
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z", artifact_dir="out/", build_if_missing=None)`
- **AND WHEN** no matching artifact exists under `artifact_dir` for the current OS/arch
- **THEN** the call fails with `ArtifactNotFoundError`

#### Scenario: Import does not rebuild when artifact exists
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z", artifact_dir="out/", build_if_missing=True)`
- **AND WHEN** a matching artifact already exists under `artifact_dir` for the current OS/arch
- **THEN** the system loads the existing artifact without rebuilding


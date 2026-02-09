## Purpose

Define the end-to-end behavior of `usegolib`: importing Go modules/packages from Python, version rules, build/load mechanics, ABI encoding, and supported cross-language types for v0.
## Requirements
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

### Requirement: Module Version Uniqueness Per Process
The system MUST NOT allow two different versions of the same Go module to be loaded within the same Python process.

#### Scenario: Version conflict is rejected
- **WHEN** Python imports `example.com/mod` at version `v1.2.0`
- **AND WHEN** Python imports `example.com/mod/subpkg` at version `v1.3.0`
- **THEN** the second import MUST fail
- **AND THEN** the system SHALL raise `VersionConflictError`

### Requirement: Build Mode And Caching
The system SHALL build the Go module into a shared library and cache build artifacts to avoid rebuilding when inputs are unchanged.

#### Scenario: First import builds and caches
- **WHEN** Python imports a module that is not yet built on disk for the resolved version
- **THEN** the system builds a shared library for that module and version
- **AND THEN** the build artifact is stored in a cache location

#### Scenario: Subsequent import reuses cached artifact
- **WHEN** Python imports a module that already has a cached shared library for the resolved version
- **THEN** the system loads the cached artifact without rebuilding

### Requirement: ABI Encoding
All cross-language calls between Python and Go MUST be encoded using MessagePack.

#### Scenario: Successful call returns a structured response
- **WHEN** Python calls an exported Go function through a module handle
- **THEN** the request MUST be encoded as MessagePack
- **AND THEN** the response MUST be MessagePack and indicate either a result or an error

### Requirement: Type Bridge Level 1 (V0)
For v0, the system SHALL support passing and returning only Level 1 values across the Python/Go boundary: `nil`, `bool`, integers, floats, `string`, `bytes`, and slices of these.

#### Scenario: Passing bytes and receiving bytes
- **WHEN** Python passes a `bytes` value as an argument in a cross-language call
- **THEN** Go receives the argument as a byte sequence without loss
- **AND THEN** a byte sequence returned from Go is received by Python as `bytes`

#### Scenario: Passing a list of scalars
- **WHEN** Python passes a list containing only Level 1 scalar values
- **THEN** Go receives a slice containing the corresponding scalar values

### Requirement: Artifact Directory Layout (v0)
The builder SHALL write artifacts to disk using a stable layout so runtime lookup by module/package, version, and platform is deterministic.

#### Scenario: Builder output layout
- **WHEN** an artifact is built for module `example.com/mod` at version `vX.Y.Z` on OS `GOOS` and arch `GOARCH`
- **THEN** the builder writes `manifest.json` under `<out>/example.com/mod@vX.Y.Z/<GOOS>-<GOARCH>/manifest.json`
- **AND THEN** the shared library file path in the manifest is relative to that manifest directory

### Requirement: Module And Version Resolution (Build)
When building artifacts from a Go import path, the system SHALL resolve a concrete module version and record it in the artifact manifest.

#### Scenario: Version omitted defaults to @latest for remote modules
- **WHEN** `usegolib build` is invoked with a Go module import path and `version=None`
- **THEN** the system resolves the version to `@latest`
- **AND THEN** the manifest `version` field contains the resolved concrete version

#### Scenario: Pinned version is used as-is for remote modules
- **WHEN** `usegolib build` is invoked with a Go module import path and `version="vX.Y.Z"`
- **THEN** the system builds using `vX.Y.Z`
- **AND THEN** the manifest `version` field MUST equal `vX.Y.Z`

#### Scenario: Local module directories use version "local"
- **WHEN** `usegolib build` is invoked with a local module directory
- **THEN** the manifest `version` field MUST be `"local"`

### Requirement: Import Builds Missing Artifacts (Dev Mode)
When `build_if_missing=True`, the system SHALL build a missing artifact into the artifact root and then load it.

#### Scenario: Import triggers build when artifact is missing
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z", artifact_dir="out/", build_if_missing=True)`
- **AND WHEN** no matching artifact exists under `artifact_dir` for the current OS/arch
- **THEN** the system builds the artifact into `artifact_dir`
- **AND THEN** the system loads the newly built artifact and returns a handle

#### Scenario: Import does not rebuild when artifact exists
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z", artifact_dir="out/", build_if_missing=True)`
- **AND WHEN** a matching artifact already exists under `artifact_dir` for the current OS/arch
- **THEN** the system loads the existing artifact without rebuilding

### Requirement: Build Reuse And Locking
The builder SHALL reuse an existing artifact output when present (unless forced) and SHALL use file locking per artifact output directory to prevent concurrent writes.

#### Scenario: Build reuses existing artifact
- **WHEN** `usegolib build` is invoked for a module/version whose artifact already exists in `<out>`
- **THEN** the builder MUST return successfully without rebuilding

#### Scenario: Build uses a per-artifact lock
- **WHEN** two processes concurrently build the same module/version into the same `<out>`
- **THEN** only one process performs the build at a time
- **AND THEN** both processes complete without corrupting the output

### Requirement: Local Build Input Fingerprint
For local module directory builds, the system SHALL compute an input fingerprint and record it in the artifact manifest. Reuse MUST only occur when the fingerprint is unchanged.

#### Scenario: Local build writes fingerprint
- **WHEN** `usegolib build` is invoked with a local module directory
- **THEN** the system writes `input_fingerprint` into `manifest.json`

#### Scenario: Local source change triggers rebuild
- **WHEN** `usegolib build` is invoked with a local module directory and an artifact already exists
- **AND WHEN** the local module directory contents change
- **THEN** the builder MUST rebuild the artifact even if `manifest.json` already exists


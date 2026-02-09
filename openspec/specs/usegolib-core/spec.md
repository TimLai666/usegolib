## Requirements

### Requirement: Python Import API
The system SHALL expose a Python API that imports a Go module (root package) and returns a handle that can be used to call exported Go identifiers.

#### Scenario: Import root module at latest version
- **WHEN** Python calls `usegolib.import_("example.com/mod", version=None)`
- **THEN** the system resolves the module version to `@latest`
- **AND THEN** the module is built and loaded into the current Python process
- **AND THEN** the call returns a module handle

#### Scenario: Import subpackage uses the same resolved version
- **WHEN** Python has already imported `example.com/mod` at version `vX.Y.Z`
- **AND WHEN** Python calls `usegolib.import_("example.com/mod/subpkg", version=None)`
- **THEN** the system imports the subpackage from the already-loaded runtime
- **AND THEN** the resolved version MUST be `vX.Y.Z`

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


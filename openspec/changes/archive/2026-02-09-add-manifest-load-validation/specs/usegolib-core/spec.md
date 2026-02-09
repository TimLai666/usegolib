## ADDED Requirements

### Requirement: Manifest Version And Platform Validation (V0.x)
When loading an artifact, the runtime SHALL validate the artifact manifest fields are supported by this version of `usegolib` before attempting to load the shared library.

Supported values are:
- `manifest_version == 1`
- `abi_version == 0`

The runtime SHALL reject artifacts built for a different platform than the current host.

#### Scenario: Unsupported manifest version is rejected
- **WHEN** the runtime loads an artifact whose `manifest_version` is not supported
- **THEN** the runtime SHALL raise `LoadError` before attempting to load the shared library

#### Scenario: Unsupported ABI version is rejected
- **WHEN** the runtime loads an artifact whose `abi_version` is not supported
- **THEN** the runtime SHALL raise `LoadError` before attempting to load the shared library

#### Scenario: Wrong platform artifact is rejected
- **WHEN** the runtime loads an artifact whose `goos/goarch` do not match the current host
- **THEN** the runtime SHALL raise `LoadError` before attempting to load the shared library


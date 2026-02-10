## MODIFIED Requirements

### Requirement: Python Import API
If a Go module is already loaded in the current Python process, then `usegolib.import_(..., version=None)` SHALL follow the already-loaded module version for that module and its subpackages.

#### Scenario: Import omits version but follows already-loaded module version
- **WHEN** Python imports `example.com/mod` at version `v1.2.0`
- **AND WHEN** Python imports `example.com/mod/subpkg` with `version=None`
- **THEN** the second import resolves to version `v1.2.0` (the already-loaded module version)
- **AND THEN** the import does not fail with `AmbiguousArtifactError` even if multiple artifact versions exist on disk

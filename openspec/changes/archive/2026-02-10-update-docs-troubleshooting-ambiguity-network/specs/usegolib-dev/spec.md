## MODIFIED Requirements

### Requirement: Troubleshooting Documentation
The repository SHALL include `docs/troubleshooting.md` covering common failures and remedies for building/loading/importing artifacts.

#### Scenario: Ambiguous artifacts mention already-loaded version behavior
- **WHEN** a developer reads the `AmbiguousArtifactError` section in `docs/troubleshooting.md`
- **THEN** it explains that ambiguity applies when the module is not already loaded
- **AND THEN** it notes that `import_(..., version=None)` follows the already-loaded version within a process

#### Scenario: Network/proxy failures mention GOPROXY remediation
- **WHEN** a developer reads the build-related troubleshooting for Go module download failures
- **THEN** it mentions proxy/network errors can be transient
- **AND THEN** it includes a remediation hint mentioning `GOPROXY=direct`


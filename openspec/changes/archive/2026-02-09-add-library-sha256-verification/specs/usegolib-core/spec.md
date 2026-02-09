## ADDED Requirements

### Requirement: Library SHA256 Verification (V0.x)
When loading an artifact, the runtime SHALL verify the shared library integrity by checking the library file SHA256 against `manifest.json`.

The manifest MUST include `library.sha256` as a 64-character lowercase hex digest.

#### Scenario: Correct SHA256 loads successfully
- **WHEN** the runtime loads an artifact whose library file SHA256 matches `library.sha256`
- **THEN** the runtime loads the shared library successfully

#### Scenario: Missing SHA256 is rejected
- **WHEN** the runtime loads an artifact whose manifest is missing `library.sha256`
- **THEN** the runtime SHALL raise `LoadError` before attempting to load the shared library

#### Scenario: Mismatched SHA256 is rejected
- **WHEN** the runtime loads an artifact whose library file SHA256 does not match `library.sha256`
- **THEN** the runtime SHALL raise `LoadError` before attempting to load the shared library


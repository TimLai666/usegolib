## ADDED Requirements

### Requirement: Local Build Input Fingerprint
For local module directory builds, the system SHALL compute an input fingerprint and record it in the artifact manifest. Reuse MUST only occur when the fingerprint is unchanged.

#### Scenario: Local build writes fingerprint
- **WHEN** `usegolib build` is invoked with a local module directory
- **THEN** the system writes `input_fingerprint` into `manifest.json`

#### Scenario: Local source change triggers rebuild
- **WHEN** `usegolib build` is invoked with a local module directory and an artifact already exists
- **AND WHEN** the local module directory contents change
- **THEN** the builder MUST rebuild the artifact even if `manifest.json` already exists


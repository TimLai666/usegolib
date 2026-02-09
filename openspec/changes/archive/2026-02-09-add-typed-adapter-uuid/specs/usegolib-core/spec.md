## ADDED Requirements

### Requirement: Typed Adapter For uuid.UUID (V0.x)
The system SHALL support `github.com/google/uuid.UUID` values in supported signatures and typed structs by encoding/decoding them as strings across the ABI.

#### Scenario: Passing uuid.UUID as a string
- **WHEN** a Go function parameter type is `uuid.UUID`
- **AND WHEN** Python passes a UUID string
- **THEN** Go receives the corresponding `uuid.UUID` value

#### Scenario: Returning uuid.UUID as a string
- **WHEN** a Go function returns a `uuid.UUID`
- **THEN** Python receives it as a UUID string


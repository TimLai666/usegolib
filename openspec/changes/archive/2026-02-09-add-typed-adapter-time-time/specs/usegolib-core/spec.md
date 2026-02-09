## ADDED Requirements

### Requirement: Typed Adapter For time.Time (V0.x)
The system SHALL support `time.Time` values in supported signatures and typed structs by encoding/decoding them as RFC3339Nano strings across the ABI.

#### Scenario: Passing time.Time as a string
- **WHEN** a Go function parameter type is `time.Time`
- **AND WHEN** Python passes a string formatted as RFC3339Nano
- **THEN** Go receives the corresponding `time.Time` value

#### Scenario: Returning time.Time as a string
- **WHEN** a Go function returns a `time.Time`
- **THEN** Python receives it as an RFC3339Nano string


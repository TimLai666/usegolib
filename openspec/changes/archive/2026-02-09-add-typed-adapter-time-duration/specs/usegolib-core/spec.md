## ADDED Requirements

### Requirement: Typed Adapter For time.Duration (V0.x)
The system SHALL support `time.Duration` values in supported signatures and typed structs by encoding/decoding them as integers representing nanoseconds across the ABI.

#### Scenario: Passing time.Duration as an int
- **WHEN** a Go function parameter type is `time.Duration`
- **AND WHEN** Python passes an integer value (nanoseconds)
- **THEN** Go receives the corresponding `time.Duration` value

#### Scenario: Returning time.Duration as an int
- **WHEN** a Go function returns a `time.Duration`
- **THEN** Python receives it as an integer value (nanoseconds)


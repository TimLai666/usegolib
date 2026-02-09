## ADDED Requirements

### Requirement: Type Bridge Level 3 Phase A (Record Structs) (V0.x)
The system SHALL support passing and returning named struct types as "record structs" across the Python/Go boundary, represented as maps from exported field names to values.

For Level 3 Phase A, struct field values MUST be limited to supported Level 1 and Level 2 types (no nested structs).

#### Scenario: Passing a record struct value
- **WHEN** Python passes a dict for a Go parameter whose type is a named struct
- **THEN** Go receives the argument as the corresponding struct value
- **AND THEN** the struct's exported fields are populated from the dict keys

#### Scenario: Returning a record struct value
- **WHEN** a Go function returns a named struct value
- **THEN** Python receives it as a dict mapping exported field names to values


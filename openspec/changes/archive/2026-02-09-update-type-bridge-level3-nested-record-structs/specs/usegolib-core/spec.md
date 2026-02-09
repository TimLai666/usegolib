## MODIFIED Requirements

### Requirement: Type Bridge Level 3 Phase A (Record Structs) (V0.x)
The system SHALL support passing and returning named struct types as "record structs" across the Python/Go boundary, represented as maps from exported field names to values.

For Level 3 Phase A, struct field values MUST be limited to supported Level 1, Level 2, and Level 3 Phase A types.

#### Scenario: Passing a record struct value
- **WHEN** Python passes a dict for a Go parameter whose type is a named struct
- **THEN** Go receives the argument as the corresponding struct value
- **AND THEN** the struct's exported fields are populated from the dict keys

#### Scenario: Returning a record struct value
- **WHEN** a Go function returns a named struct value
- **THEN** Python receives it as a dict mapping exported field names to values

#### Scenario: Nested record structs are supported
- **WHEN** Python passes a dict for a Go parameter whose type is a named struct
- **AND WHEN** that struct contains exported fields whose types are named structs
- **THEN** nested dict values are converted recursively to the nested struct values

#### Scenario: Containers of record structs are supported
- **WHEN** Python passes a list or dict of record structs for a Go parameter whose type is `[]Struct` or `map[string]Struct`
- **THEN** Go receives the argument as the corresponding slice/map of struct values


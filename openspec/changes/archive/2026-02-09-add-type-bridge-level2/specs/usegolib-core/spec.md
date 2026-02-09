## MODIFIED Requirements

### Requirement: Type Bridge Level 1 (V0)
For v0, the system SHALL support passing and returning Level 1 values across the Python/Go boundary: `nil`, `bool`, integers, floats, `string`, `bytes`, and slices of these.

#### Scenario: Passing bytes and receiving bytes
- **WHEN** Python passes a `bytes` value as an argument in a cross-language call
- **THEN** Go receives the argument as a byte sequence without loss
- **AND THEN** a byte sequence returned from Go is received by Python as `bytes`

#### Scenario: Passing a list of scalars
- **WHEN** Python passes a list containing only Level 1 scalar values
- **THEN** Go receives a slice containing the corresponding scalar values

## ADDED Requirements

### Requirement: Type Bridge Level 2 (V0.x)
The system SHALL support passing and returning Level 2 values across the Python/Go boundary: `map[string]T` where `T` is a Level 1 scalar or a slice of Level 1 scalars.

#### Scenario: Passing map[string]int64
- **WHEN** Python passes a dict of `str -> int` values
- **THEN** Go receives the argument as `map[string]int64` without loss

#### Scenario: Returning map[string][]byte
- **WHEN** a Go function returns `map[string][]byte`
- **THEN** Python receives it as a dict mapping `str -> bytes`


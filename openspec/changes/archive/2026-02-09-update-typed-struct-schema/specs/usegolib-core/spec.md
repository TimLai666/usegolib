## MODIFIED Requirements

### Requirement: Type Bridge Level 3 Phase A (Record Structs) (V0.x)
The system SHALL support passing and returning named struct types as "record structs" across the Python/Go boundary, represented as maps from exported field keys to values.

For Level 3 Phase A, struct field values MUST be limited to supported Level 1, Level 2, and Level 3 Phase A types.

Record struct keys MUST follow the canonical key selection rules (tags) when tags are present.

#### Scenario: Passing a record struct value
- **WHEN** Python passes a dict for a Go parameter whose type is a named struct
- **THEN** Go receives the argument as the corresponding struct value
- **AND THEN** the struct's exported fields are populated from the dict keys

#### Scenario: Returning a record struct value
- **WHEN** a Go function returns a named struct value
- **THEN** Python receives it as a dict mapping canonical field keys to values

#### Scenario: Missing required fields are rejected
- **WHEN** a Go function parameter type is a named struct
- **AND WHEN** Python passes a dict missing a required exported field
- **THEN** the runtime MUST raise `UnsupportedTypeError` before invoking the shared library

#### Scenario: Nested record structs are supported
- **WHEN** Python passes a dict for a Go parameter whose type is a named struct
- **AND WHEN** that struct contains exported fields whose types are named structs
- **THEN** nested dict values are converted recursively to the nested struct values

#### Scenario: Containers of record structs are supported
- **WHEN** Python passes a list or dict of record structs for a Go parameter whose type is `[]Struct` or `map[string]Struct`
- **THEN** Go receives the argument as the corresponding slice/map of struct values

## ADDED Requirements

### Requirement: Typed Struct Tag Options (omitempty and ignore) (V0.x)
When exchanging typed struct values, the system SHALL respect common tag options:

- `omitempty`: fields tagged `omitempty` are not required to be present in Python dict inputs, and may be omitted from record-struct outputs when the field value is empty.
- ignore: fields tagged with `msgpack:"-"` (or, if no msgpack tag is present, `json:"-"`) MUST NOT be included in schema exchange and MUST NOT be present in record-struct outputs.

#### Scenario: omitempty fields are optional
- **WHEN** a Go struct field is tagged `json:"nick,omitempty"`
- **AND WHEN** Python passes a dict that omits `nick`
- **THEN** the runtime accepts the value (no missing-field error)

#### Scenario: omitempty fields may be omitted on output
- **WHEN** a Go struct field is tagged `json:"nick,omitempty"`
- **AND WHEN** the returned struct has an empty `nick` value
- **THEN** Python does not receive the `nick` key in the record-struct dict

#### Scenario: Ignored fields are excluded
- **WHEN** a Go struct field is tagged `json:"-"`
- **THEN** the builder does not include the field in the manifest schema
- **AND THEN** record-struct outputs do not include that field

### Requirement: Typed Struct Embedded Fields (V0.x)
The system SHALL include exported embedded (anonymous) struct fields in schema exchange so runtime validation can accept record structs containing embedded fields.

Note: embedded fields are represented as a nested record-struct field keyed by the embedded field name (type name) unless a canonical tag key overrides it.

#### Scenario: Embedded fields appear in schema and outputs
- **WHEN** a Go struct contains an exported embedded field whose type is a named struct
- **THEN** the manifest schema includes that embedded field
- **AND THEN** record-struct outputs include a nested dict under the embedded field key


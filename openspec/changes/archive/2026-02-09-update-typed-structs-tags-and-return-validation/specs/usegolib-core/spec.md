## ADDED Requirements

### Requirement: Typed Struct Keys (Tags) (V0.x)
When using record structs, the system SHALL support mapping Python dict keys to Go struct fields using either the exported Go field name or supported tag keys.

Supported tags (in order of precedence for canonical keys) are:
1. `msgpack:"name,omitempty"`
2. `json:"name,omitempty"`

#### Scenario: Passing tag-keyed record structs
- **WHEN** a Go struct field has tag `json:"first_name"`
- **AND WHEN** Python passes a dict containing key `"first_name"`
- **THEN** Go receives the struct field populated as if the Python key were the exported field name

#### Scenario: Returning canonical keys
- **WHEN** a Go struct field has tag `msgpack:"age"`
- **AND WHEN** a Go function returns that struct value
- **THEN** Python receives the field under key `"age"` (canonical key), not the exported Go field name

### Requirement: Schema Validation For Results (V0.x)
When schema exchange is available in the artifact manifest, the runtime SHALL validate successful call results against the schema before returning them to user code.

#### Scenario: Runtime rejects schema-invalid results
- **WHEN** a successful call returns a value that does not conform to the schema result type
- **THEN** the runtime raises `UnsupportedTypeError` with a `schema:` prefixed message


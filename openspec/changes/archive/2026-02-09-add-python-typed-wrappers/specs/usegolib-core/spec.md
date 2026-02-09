## ADDED Requirements

### Requirement: Python Typed Struct Wrappers (V0.x)
When schema exchange is available in the artifact manifest, the runtime SHALL be able to generate Python dataclasses corresponding to named Go structs and provide a typed calling surface.

The typed calling surface SHALL:
- accept generated dataclass instances as inputs wherever a record struct value is expected
- decode successful record-struct results into generated dataclass instances when the schema indicates a struct result type

#### Scenario: Dataclass instances are accepted as inputs
- **WHEN** a Go function parameter type is a named struct
- **AND WHEN** Python passes an instance of the generated dataclass for that struct
- **THEN** the runtime encodes it as a record struct dict using canonical keys and calls into the shared library successfully

#### Scenario: Struct results decode to dataclasses
- **WHEN** a Go function returns a named struct value
- **AND WHEN** Python calls the function through the typed calling surface
- **THEN** Python receives an instance of the corresponding generated dataclass


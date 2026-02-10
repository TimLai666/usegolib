## ADDED Requirements

### Requirement: GoDoc To Python Docstrings (V0.x)
When building an artifact, the system SHALL extract Go doc comments for exported functions and methods and include them in the artifact schema.

When schema is present, the Python runtime SHOULD attach these docs as docstrings on the dynamic callables it returns.

The bindgen generator SHOULD emit these docs as Python docstrings in generated modules.

#### Scenario: Bindgen includes docstrings
- **WHEN** an artifact manifest schema includes `doc` for a symbol
- **AND WHEN** the user runs `usegolib bindgen`
- **THEN** the generated Python method includes a docstring derived from the Go doc comment


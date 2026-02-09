## ADDED Requirements

### Requirement: Python Bindings Generator (V0.x)
When schema exchange is available in an artifact manifest, the system SHALL be able to generate a static Python module for a specified Go package containing dataclasses for named structs and a typed API wrapper for callable symbols.

#### Scenario: Generate bindings module
- **WHEN** the user runs `usegolib gen` with an artifact directory and package
- **THEN** the system writes a Python module containing struct dataclasses and typed API methods

#### Scenario: Generated API calls Go successfully
- **WHEN** the user imports the generated module and calls `load(...)` to obtain the API
- **AND WHEN** the user calls a generated method with supported values (including generated dataclasses)
- **THEN** the call succeeds and returns values matching the generated type annotations


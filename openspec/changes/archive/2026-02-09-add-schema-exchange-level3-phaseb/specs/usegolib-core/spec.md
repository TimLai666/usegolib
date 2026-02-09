## ADDED Requirements

### Requirement: Schema Exchange (Import) (V0.x)
When importing an artifact, the system SHALL load a schema describing callable symbols and named struct types so the runtime can validate values before calling into the Go shared library.

#### Scenario: Manifest includes struct field schema
- **WHEN** an artifact is built for a module/package that defines named structs
- **THEN** the emitted `manifest.json` includes a schema describing exported struct fields and their types

#### Scenario: Runtime validates struct field types before call
- **WHEN** Python calls an exported function that accepts a record struct argument
- **AND WHEN** the provided dict contains a field value that does not match the schema type
- **THEN** the call fails with `UnsupportedTypeError` before invoking the shared library


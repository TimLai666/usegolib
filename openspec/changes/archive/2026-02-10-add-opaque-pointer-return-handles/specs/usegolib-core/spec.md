## ADDED Requirements

### Requirement: Opaque Pointer Results Use Object Handles (V0.x)
When a callable symbol or method returns `*T` and the struct type `T` has no exported fields in the manifest schema, the system SHALL represent that value as an object handle rather than a record-struct dict.

#### Scenario: Function returns *Opaque handle
- **WHEN** a Go function returns `*T`
- **AND WHEN** `T` has no exported fields
- **THEN** Python receives a `GoObject` that can be used to call exported methods on `T`

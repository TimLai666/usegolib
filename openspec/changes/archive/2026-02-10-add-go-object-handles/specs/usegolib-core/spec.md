## ADDED Requirements

### Requirement: Go Object Handles And Exported Methods (V0.x)
The system SHALL support calling exported Go methods without serializing the receiver value on every call by using Go-side object handles.

The runtime SHALL expose a Python API to:
- create a Go-side object handle for a named struct type (`obj_new`)
- call exported methods on that handle (`obj_call`)
- free the handle (`obj_free`)

#### Scenario: Create object handle and call method
- **WHEN** Python creates a Go object handle for a named struct type
- **AND WHEN** Python calls an exported method on the object handle
- **THEN** the call succeeds and returns the method result

#### Scenario: Freeing an object handle makes it unusable
- **WHEN** Python frees a Go object handle
- **AND WHEN** Python calls a method on the freed handle
- **THEN** the call fails with an error


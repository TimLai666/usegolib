## ADDED Requirements

### Requirement: Exported Package Variables Are Accessible For Method Calls
The runtime SHALL allow accessing exported Go package variables as Python attributes when they are used as "namespace" objects to call exported methods (common in Go fluent APIs).

#### Scenario: Access exported package variable and call exported method
- **GIVEN** a Go package defines an exported package variable `DL` of a (possibly unexported) struct type
- **AND GIVEN** that type defines an exported method `Of(...any) *dl` (or similar)
- **WHEN** Python evaluates `pkg.DL.Of(1, 2, 3)`
- **THEN** the runtime resolves `pkg.DL` as an object handle bound to that variable
- **AND THEN** the runtime calls method `Of` on that object handle
- **AND THEN** if the result is a pointer to an opaque struct type, the result is represented in Python as a callable object handle (not a dict)


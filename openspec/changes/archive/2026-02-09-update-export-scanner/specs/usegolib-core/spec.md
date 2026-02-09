## ADDED Requirements

### Requirement: Export Scan Correctness (Build)
When building artifacts, the system SHALL discover exported top-level functions and their parameter/return types from Go source in a way that is robust to valid Go syntax and formatting (including grouped parameters).

#### Scenario: Grouped parameters are supported
- **WHEN** a Go package declares `func AddGrouped(a, b int64) int64`
- **THEN** the builder includes `AddGrouped` as a callable symbol

#### Scenario: Methods and generics are ignored
- **WHEN** a Go package declares an exported method `func (T) M(...) ...` or a generic function `func F[T any](...) ...`
- **THEN** the builder MUST NOT include those as callable symbols in v0


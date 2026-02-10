## ADDED Requirements

### Requirement: Error-Only Results Are Treated As Nil On Success
When a callable symbol or method returns only `error`, the system SHALL represent successful results as `nil` (Python `None`).

If the returned `error` is non-nil, the system SHALL report the failure via the ABI error envelope as `GoError`.

#### Scenario: Method returns only error and succeeds
- **WHEN** a Go method returns `error`
- **AND WHEN** the call succeeds (`error` is `nil`)
- **THEN** the Python result is `None`

#### Scenario: Method returns only error and fails
- **WHEN** a Go method returns `error`
- **AND WHEN** the call fails (`error` is non-nil)
- **THEN** the Python call raises `GoError`


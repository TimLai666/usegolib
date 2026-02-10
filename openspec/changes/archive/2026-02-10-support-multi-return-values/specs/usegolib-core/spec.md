## ADDED Requirements

### Requirement: Multiple Return Values Are Returned As Python Tuples
When an artifact manifest schema is available, the runtime SHALL support Go functions and methods that return multiple non-error values by returning a Python tuple containing those values in order.

If a signature ends with `error` and the returned error is non-nil, the runtime SHALL raise `GoError` and SHALL NOT return partial values.

The historical `(T, error) -> T` success representation SHALL be preserved (not a 1-tuple).

#### Scenario: Function returns two values
- **GIVEN** a Go function `Pair() (int64, string)`
- **WHEN** Python calls `pkg.Pair()`
- **THEN** the result is a 2-tuple `(int, str)`

#### Scenario: Function returns multiple values with trailing error
- **GIVEN** a Go function `Trio(ok bool) (int64, int64, error)`
- **WHEN** Python calls `pkg.Trio(True)`
- **THEN** the result is a 2-tuple `(int, int)`
- **AND WHEN** Python calls `pkg.Trio(False)`
- **THEN** the call raises `GoError`


## MODIFIED Requirements

### Requirement: GoDoc To Python Docstrings (V0.x)
When building an artifact, the system SHALL extract Go doc comments for exported functions and methods and include them in the artifact schema.

When schema is present, the Python runtime SHALL attach docstrings to the dynamic callables it returns for exported functions and methods.

If GoDoc is missing for a callable, the runtime SHOULD still attach a signature-based docstring (so `help()` is informative).

Typed wrappers (`handle.typed()` and typed objects) SHALL preserve the docstrings of the underlying dynamic callables.

The bindgen generator SHOULD emit these docs as Python docstrings in generated modules.

#### Scenario: Runtime exposes GoDoc for a function
- **WHEN** an artifact manifest schema includes `doc` for a symbol
- **AND WHEN** the user imports the package and accesses the function
- **THEN** the returned callable has `__doc__` containing the Go doc comment

#### Scenario: Runtime provides signature docstring fallback
- **WHEN** an artifact manifest schema includes a symbol signature but has no `doc`
- **AND WHEN** the user accesses the callable
- **THEN** the returned callable has a non-empty `__doc__` containing a Go signature string

#### Scenario: Typed wrappers preserve docstrings
- **WHEN** a user accesses a callable via `handle.typed()`
- **THEN** the typed callable has the same `__doc__` content as the untyped callable

#### Scenario: Bindgen includes docstrings
- **WHEN** an artifact manifest schema includes `doc` for a symbol
- **AND WHEN** the user runs `usegolib bindgen`
- **THEN** the generated Python method includes a docstring derived from the Go doc comment


## ADDED Requirements

### Requirement: Missing Go Toolchain Hint (V0.x)
When the system needs to build artifacts using the Go toolchain and the `go` executable cannot be found, the system SHALL raise a `BuildError` with an actionable hint.

The hint SHOULD mention:
- installing Go and ensuring `go` is on `PATH`
- disabling auto-build via `build_if_missing=False` and using prebuilt artifacts/wheels

#### Scenario: Import auto-build fails because `go` is missing
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z")`
- **AND WHEN** the artifact is missing and auto-build is attempted
- **AND WHEN** `go` is not available on `PATH`
- **THEN** the call fails with `BuildError`
- **AND THEN** the error message includes a hint to install Go or disable auto-build


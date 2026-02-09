## ADDED Requirements

### Requirement: Generate Python Package With Embedded Artifacts
The system SHALL provide a command that generates a Python package project embedding a built artifact (manifest + shared library) for the current OS/arch.

#### Scenario: Generate package project skeleton
- **WHEN** a user runs `usegolib package --module <local-module-dir> --python-package-name mypkg --out <dir>`
- **THEN** the system writes a Python project under `<dir>/mypkg/` with a `pyproject.toml`
- **AND THEN** the project contains `src/mypkg/_usegolib_artifacts/` with at least one `manifest.json` and shared library file

#### Scenario: Generated package can load the embedded artifact at runtime
- **WHEN** the generated package is installed into a Python environment
- **THEN** importing `mypkg` loads the embedded artifact using `usegolib.import_()`
- **AND THEN** calling an exported Go function from the embedded package works


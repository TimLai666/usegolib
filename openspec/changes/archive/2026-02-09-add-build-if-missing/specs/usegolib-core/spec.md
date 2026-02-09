## ADDED Requirements

### Requirement: Import Builds Missing Artifacts (Dev Mode)
When `build_if_missing=True`, the system SHALL build a missing artifact into the artifact root and then load it.

#### Scenario: Import triggers build when artifact is missing
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z", artifact_dir="out/", build_if_missing=True)`
- **AND WHEN** no matching artifact exists under `artifact_dir` for the current OS/arch
- **THEN** the system builds the artifact into `artifact_dir`
- **AND THEN** the system loads the newly built artifact and returns a handle

#### Scenario: Import does not rebuild when artifact exists
- **WHEN** Python calls `usegolib.import_("example.com/mod", version="vX.Y.Z", artifact_dir="out/", build_if_missing=True)`
- **AND WHEN** a matching artifact already exists under `artifact_dir` for the current OS/arch
- **THEN** the system loads the existing artifact without rebuilding

### Requirement: Build Reuse And Locking
The builder SHALL reuse an existing artifact output when present (unless forced) and SHALL use file locking per artifact output directory to prevent concurrent writes.

#### Scenario: Build reuses existing artifact
- **WHEN** `usegolib build` is invoked for a module/version whose artifact already exists in `<out>`
- **THEN** the builder MUST return successfully without rebuilding

#### Scenario: Build uses a per-artifact lock
- **WHEN** two processes concurrently build the same module/version into the same `<out>`
- **THEN** only one process performs the build at a time
- **AND THEN** both processes complete without corrupting the output


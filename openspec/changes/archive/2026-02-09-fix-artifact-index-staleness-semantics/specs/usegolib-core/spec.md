## MODIFIED Requirements

### Requirement: Artifact Index Cache (V0.x)
To improve performance for large artifact roots, the runtime SHALL be allowed to create and use an index cache file under the artifact root for artifact discovery.

The index MUST NOT change the import resolution semantics: if a matching artifact exists under the artifact root, it MUST be found; if multiple versions exist and version is omitted, the import MUST remain ambiguous.

#### Scenario: Index is created on first import
- **WHEN** Python imports a module from an artifact root that does not yet contain an index
- **THEN** the runtime MAY create an index cache file under the artifact root
- **AND THEN** the import resolution behavior is unchanged

#### Scenario: Stale index entries are handled
- **WHEN** the artifact root contains an index that references missing manifest files
- **THEN** the runtime falls back to scanning and rebuilds the index
- **AND THEN** the import resolution behavior is unchanged

#### Scenario: Stale index does not hide ambiguity
- **WHEN** the artifact root contains an index that was created before a second version of an artifact was added
- **AND WHEN** Python imports with `version=None`
- **THEN** the import MUST still be ambiguous


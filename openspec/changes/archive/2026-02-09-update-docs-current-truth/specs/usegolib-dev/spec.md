## ADDED Requirements

### Requirement: Developer Docs Match Current Behavior
The repository SHALL keep developer-facing documentation aligned with current `usegolib` behavior so users do not rely on outdated assumptions.

#### Scenario: ABI documentation reflects supported types
- **WHEN** the repository supports Level 2/3 type bridging and typed adapters in v0.x
- **THEN** `docs/abi.md` describes the supported type levels and their wire encodings


## ADDED Requirements

### Requirement: Troubleshooting Documentation
The repository SHALL include `docs/troubleshooting.md` covering common failures and remedies for building/loading/importing artifacts.

#### Scenario: Troubleshooting docs exist
- **WHEN** a developer looks for common error remediation steps
- **THEN** `docs/troubleshooting.md` exists and covers common failure modes

### Requirement: Roadmap Avoids Misleading Internal Version Numbers
The repository SHALL keep `docs/roadmap.md` version-agnostic for unreleased work and MUST NOT assign misleading internal version ranges to future milestones.

#### Scenario: Roadmap does not claim internal version ranges
- **WHEN** a developer reads `docs/roadmap.md`
- **THEN** future milestones do not include internal version ranges like `v0.X - v0.Y`


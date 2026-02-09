## Why

The project is approaching the transition from v0.x (rapid iteration) to a v1.0 stability promise. We need explicit, written policies for compatibility/versioning, security, and reproducible builds so development can pause/resume without re-deciding release rules.

## What Changes

- Add documentation describing:
  - ABI + manifest versioning and compatibility rules
  - supported platform matrix and toolchain pins
  - security boundaries and current hardening measures
  - guidance for reproducible builds
- Link these docs from the README.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `usegolib-dev`: developer-facing policy documentation must exist and remain current

## Impact

- Affected files: `docs/*.md`, `README.md`, `openspec/specs/usegolib-dev/spec.md`
- No runtime/build behavior changes


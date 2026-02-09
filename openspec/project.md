# OpenSpec Project: usegolib

This repository uses spec-driven development.

## Conventions

- `openspec/specs/` is the current specification of the system.
- `openspec/changes/` contains proposed changes (each change is a self-contained folder).
- Change IDs:
  - kebab-case
  - verb-led: `add-`, `update-`, `remove-`, `refactor-`
  - example: `add-v0-mvp`
- Capabilities:
  - kebab-case, single purpose
  - example: `usegolib-core`

## Requirements Format

- Use normative wording: **MUST**, **SHALL**, **MUST NOT**, **SHOULD**.
- Every requirement MUST have at least one scenario.
- Scenario headers MUST use this exact format:
  - `#### Scenario: ...`

## Tooling

If the `openspec` CLI is available, validate with:

```bash
openspec validate --strict
openspec validate <change-id> --strict
```

If the CLI is not available, do a manual review:

- Ensure every `### Requirement:` has at least one `#### Scenario:`.
- Ensure deltas are under `## ADDED|MODIFIED|REMOVED|RENAMED Requirements`.
- Ensure scenarios use `- **WHEN**` / `- **THEN**` bullets.


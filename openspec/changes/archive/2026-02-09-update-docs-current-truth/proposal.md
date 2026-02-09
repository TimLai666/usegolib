# Change: Update Docs To Match Current v0.x Behavior

## Why
Several docs and comments still describe earlier v0 assumptions (e.g. "Level 1 only", "builder implemented later"), while the codebase now supports Level 2/3, schema exchange, typed adapters, and additional hardening checks.
Keeping docs aligned with current behavior reduces integration mistakes and makes the project easier to resume later.

## What Changes
- Update `docs/abi.md` to describe the actual v0.x bridge (Level 1/2/3, typed adapters, schema validation boundaries).
- Update README quickstart notes to reflect current import/build behavior.
- Fix CLI `usegolib version` to print the installed package version instead of a hardcoded string.
- Update outdated inline docstrings that claim builder is not implemented.

## Impact
- Affected code/docs: `docs/abi.md`, `README.md`, `src/usegolib/cli.py`, `src/usegolib/importer.py`
- No spec changes (doc-only improvement).


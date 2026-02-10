## Why

Users want `usegolib` to work with remote Go modules (auto-download) and to have a clear plan for future support of exported methods and generics. The roadmap and CLI/docs should reflect current capabilities and the intended upgrade path.

## What Changes

- Update `docs/roadmap.md` to add explicit future milestones for:
  - exported method support
  - generic function support
- Clarify CLI help text and README examples to state that `--module` may be a local module directory or a Go import path.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities

- `usegolib-dev`: roadmap and developer-facing docs for planned features

## Impact

- Affected docs: `docs/roadmap.md`, `README.md`
- Affected CLI help: `src/usegolib/cli.py`


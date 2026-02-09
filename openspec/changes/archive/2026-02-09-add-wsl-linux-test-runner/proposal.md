# Change: WSL Linux Test Runner

## Why
CI already tests Linux, but local development on Windows benefits from a deterministic way to run the Linux test suite without leaving the repo context. WSL provides a convenient Linux environment; the repo should provide a first-class runner script.

## What Changes
- Add `tools/wsl_linux_tests.ps1` to run unit and (optionally) integration tests inside WSL.
- Add `docs/testing.md` documenting Windows+WSL and Linux test workflows.

## Impact
- Affected specs: `usegolib-dev`
- Affected code: none (tooling + docs only)


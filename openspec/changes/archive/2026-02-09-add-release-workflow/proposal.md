## Why

To make v0.x releases repeatable and easy to resume, the repository needs an explicit release workflow (CI automation + docs) that builds distributions and attaches them to GitHub Releases when a version tag is pushed.

## What Changes

- Add a GitHub Actions workflow triggered by tags `v*` that:
  - runs OpenSpec validation and tests
  - builds `sdist` and `wheel`
  - uploads the distributions as GitHub Release assets
- Add `docs/releasing.md` describing the exact release steps and expectations.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `usegolib-dev`: repository release workflow and releasing documentation

## Impact

- Affected files: `.github/workflows/release.yml`, `docs/releasing.md`, `README.md`, `openspec/specs/usegolib-dev/spec.md`
- No runtime/build/package behavior changes


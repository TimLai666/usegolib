## Why

We want the first official version tag and release artifacts to be `v0.1.0`. The repository should also enforce that release tags match the package version to prevent mismatched metadata.

## What Changes

- Bump `pyproject.toml` project version to `0.1.0`.
- Update the tag-triggered release workflow to fail if the pushed tag does not match the `pyproject.toml` version.
- Update releasing docs to mention this check.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities

- `usegolib-dev`: release workflow/version alignment

## Impact

- Affected files: `pyproject.toml`, `.github/workflows/release.yml`, `docs/releasing.md`, `openspec/specs/usegolib-dev/spec.md`


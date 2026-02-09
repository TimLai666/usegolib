## Why

To release `usegolib` beyond GitHub artifacts, we need a repeatable way to publish `sdist` and `wheel` to PyPI without storing long-lived credentials in repository secrets.

## What Changes

- Add a GitHub Actions workflow that can publish to PyPI (and optionally TestPyPI) using PyPI Trusted Publishing (OIDC).
- Document the required PyPI project configuration and the exact publish steps.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities

- `usegolib-dev`: publishing workflow + documentation

## Impact

- Affected files: `.github/workflows/publish-pypi.yml`, `docs/releasing.md`, `openspec/specs/usegolib-dev/spec.md`
- No runtime/build/package behavior changes


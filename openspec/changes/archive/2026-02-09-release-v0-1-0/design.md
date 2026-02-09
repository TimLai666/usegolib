# Design: Version Bump + Tag/Version Guard

## Version Source Of Truth

The Python package version remains `project.version` in `pyproject.toml`.

## Guardrail

In `.github/workflows/release.yml`, add a step that:
- reads the pushed git tag (e.g. `refs/tags/v0.1.0`)
- reads `pyproject.toml` `project.version`
- fails if they differ

This prevents creating a GitHub Release whose assets claim one version while the package metadata claims another.


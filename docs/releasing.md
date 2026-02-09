# Releasing

This repository uses a tag-triggered GitHub Actions workflow to build distributions and attach them to a GitHub Release.

## Release Steps

1. Ensure CI is green on the main development branch.
2. Decide the version (e.g. `0.1.0`) and update `pyproject.toml` accordingly.
3. Create and push a git tag `v<version>` (e.g. `v0.1.0`).

The `Release` workflow will run:
- A guardrail check that the pushed tag version matches `pyproject.toml` `project.version`
- OpenSpec validation
- Python tests
- `python -m build` to produce:
  - `dist/usegolib-<version>.tar.gz` (sdist)
  - `dist/usegolib-<version>-py3-none-any.whl` (wheel)

Those files will be uploaded as GitHub Release assets for the tag.

## Notes

- This workflow does not publish to PyPI by default.
- If you need a reproducible build, follow `docs/reproducible-builds.md`.

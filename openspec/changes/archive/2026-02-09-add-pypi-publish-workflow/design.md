# Design: PyPI Publishing Via Trusted Publishing (OIDC)

## Workflow

Add `.github/workflows/publish-pypi.yml` triggered via `workflow_dispatch` with a target repository selector:
- `pypi` (default)
- `testpypi`

The job will:
1. Build `sdist` + `wheel` using `python -m build`
2. Publish using `pypa/gh-action-pypi-publish@release/v1` with OIDC (`id-token: write`)

## Setup Requirements (Docs)

Publishing requires configuring PyPI Trusted Publishing:
- create a PyPI project named `usegolib` (or reserved)
- add a Trusted Publisher for this GitHub repo and the workflow name/path

No API tokens are stored in GitHub secrets.


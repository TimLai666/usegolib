## ADDED Requirements

### Requirement: PyPI Publishing Workflow
The repository SHALL provide a GitHub Actions workflow to publish `usegolib` distributions to PyPI using trusted publishing (OIDC) without storing long-lived credentials in repository secrets.

The workflow MUST:
- build `sdist` and `wheel` into `dist/`
- request OIDC token permissions (`id-token: write`)
- publish to PyPI (or TestPyPI) using `pypa/gh-action-pypi-publish`

#### Scenario: Maintainer can publish to PyPI without tokens
- **WHEN** a maintainer runs the PyPI publish workflow
- **THEN** the workflow publishes the built distributions using trusted publishing


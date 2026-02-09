# Design: Tag-Triggered Release Workflow

## Trigger

- Workflow triggers on pushes of tags matching `v*` (e.g. `v0.1.0`).

## Steps

1. Checkout
2. Setup Python
3. Install `usegolib` dev dependencies
4. Install OpenSpec CLI
5. Run `openspec validate --all --strict --no-interactive`
6. Run unit tests (`pytest -q`)
7. Build distributions (`python -m build`)
8. Attach `dist/*` to a GitHub Release for that tag

## Notes

- We keep publishing to PyPI out-of-scope for now (can be added later with trusted publishing).
- Since `usegolib` is pure Python, wheels are platform-independent, but we still validate tests via normal CI.


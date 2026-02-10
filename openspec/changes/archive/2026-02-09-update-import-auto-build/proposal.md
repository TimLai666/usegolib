## Why

For day-to-day usage, requiring users to manually pre-build artifacts (and pass `artifact_dir`) adds friction. We want a single call (`usegolib.import_`) to be enough: it should use a default artifact cache directory and, when appropriate, build missing artifacts automatically (including when importing a subpackage of a module).

## What Changes

- `usegolib.import_`:
  - no longer requires `artifact_dir`
  - uses a default artifact cache directory when `artifact_dir` is omitted
  - supports `build_if_missing=None` (auto mode):
    - if `artifact_dir` is omitted: build missing artifacts into the default cache
    - if `artifact_dir` is provided: do not build unless `build_if_missing=True`
  - supports local subpackage directory imports by mapping the directory to the correct Go import path
- Add an environment override: `USEGOLIB_ARTIFACT_DIR` to set the default artifact root.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities

- `usegolib-core`: import defaults and auto-build behavior

## Impact

- Affected code: `src/usegolib/importer.py`, `src/usegolib/builder/resolve.py` (local module root discovery), new `src/usegolib/paths.py`
- Affected docs: `README.md`, `docs/testing.md` (optional), `docs/roadmap.md` (optional)


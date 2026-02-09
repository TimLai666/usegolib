# Change: Artifact Directory Index Cache For Faster Imports

## Why
Artifact resolution currently scans the entire `artifact_dir` via `rglob("manifest.json")` for every import, which can become slow for large artifact roots.
An on-disk index cache amortizes the scan cost across imports without changing resolution semantics.

## What Changes
- `usegolib.import_(..., artifact_dir=...)` will create and use a cache file under the artifact root (e.g. `.usegolib-index.json`) to speed manifest discovery.
- If the index is missing, invalid, or stale (manifests missing), the runtime falls back to scanning and rebuilds the index.

## Impact
- Affected specs: `usegolib-core`
- Affected code: `src/usegolib/artifact.py`
- Tests: add unit tests for index creation and stale-index fallback.


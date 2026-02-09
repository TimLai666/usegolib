# Change: Fix Artifact Index Staleness Semantics (Ambiguity)

## Why
The artifact index cache is an optimization, but it MUST NOT change import resolution semantics.
If the index is stale and missing newer manifests, importing without a pinned version must still detect ambiguity rather than selecting an arbitrary version.

## What Changes
- When resolving without an explicit version, the runtime performs a scan-based resolution (or otherwise ensures completeness) so ambiguity detection remains correct even if the index is stale.
- The index remains an optimization for pinned-version resolution, and is rebuilt opportunistically.

## Impact
- Affected specs: `usegolib-core`
- Affected code: `src/usegolib/artifact.py`
- Tests: add a regression test for stale index + version omitted.


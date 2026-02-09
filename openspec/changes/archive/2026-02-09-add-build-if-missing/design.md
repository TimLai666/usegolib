## Context

Runtime import resolution already scans manifests under an artifact root and loads matching artifacts. The missing piece is "dev mode": build on demand when the artifact isn't present.

## Goals / Non-Goals

**Goals:**
- Add `build_if_missing=True` for `usegolib.import_()`.
- Prevent concurrent builds from clobbering outputs with a file lock on the leaf output directory.
- Reuse existing leaf outputs as a cache hit (unless forced).

**Non-Goals:**
- Global build cache in a separate default location (we build into the provided `artifact_dir`).
- Content-based rebuild detection for local modules (v0 uses presence-based reuse).

## Decisions

- Lock file: `<leaf>/.usegolib.lock` (exclusive lock).
- Reuse policy:
  - If `<leaf>/manifest.json` exists and the referenced shared library exists, treat as "ready" and reuse.
  - Add `--force` to override reuse and rebuild.

## Risks / Trade-offs

- Presence-based reuse can miss local source changes.
  - Mitigation: `--force` and/or choose a new output root per build; later milestone can add content hashing.


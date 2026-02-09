## Context

`usegolib` needs to support real artifact directories produced by CI and embedded into wheels. That implies:

- One `artifact_dir` can contain multiple modules, versions, and platforms.
- Importing a subpackage must call into that package (not always module root).
- Resolution must be deterministic and fail loudly on ambiguity.

## Goals / Non-Goals

**Goals:**
- `usegolib.import_()` resolves an artifact from an artifact root by `(package_path, version?, platform)`.
- Handles are bound to a specific package path, so function calls route to `pkg` correctly.
- Builder output follows a stable `<module>@<version>/<goos>-<goarch>/` layout.

**Non-Goals:**
- Remote module download and version resolution from the internet (`@latest`) in this change.
- Multi-version loading in one Python process (explicitly forbidden by spec).

## Decisions

- **Artifact discovery**: runtime scans `artifact_dir` for `manifest.json` files and selects the best match.
  - Match is defined as: manifest contains the requested package path, and matches current `(goos, goarch)`.
  - If `version` is provided, it must match exactly.
  - If `version` is omitted, there must be exactly one candidate, else raise `AmbiguousArtifactError`.
- **Handle model**: introduce a `PackageHandle` that carries `package` and a shared `SharedLibClient` per loaded module runtime.
- **Builder output**: `usegolib build --out <root>` writes into the layout directory for the module/version/platform.

## Risks / Trade-offs

- Scanning `artifact_dir` recursively can be slow for very large trees.
  - Mitigation: keep v0 simple; later add an index/cache file or a deterministic layout-only search.


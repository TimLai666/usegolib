# Design: Default Artifact Root + Auto-Build Import

## Default Artifact Root

Introduce a runtime default artifact root for `usegolib.import_`:

- If `artifact_dir` is passed: use it.
- Else if `USEGOLIB_ARTIFACT_DIR` is set: use it.
- Else use OS defaults:
  - Windows: `%LOCALAPPDATA%/usegolib/artifacts`
  - macOS/Linux: `~/.cache/usegolib/artifacts`

The directory is created on demand.

## Auto-Build Behavior

`build_if_missing` becomes tri-state:

- `True`: build missing artifacts into the chosen artifact root.
- `False`: never build; missing artifacts raise `ArtifactNotFoundError`.
- `None` (auto):
  - if `artifact_dir` is omitted: behave like `True`
  - if `artifact_dir` is provided: behave like `False`

## Local Directory Imports (Subpackages)

If the `module` argument is a directory:
- Find the module root directory by walking up to the nearest `go.mod`.
- Parse module path from that `go.mod`.
- Compute the package import path as `module_path + "/" + <relative path from module root>` (if any).
- Build target is always the module root directory (not the subdirectory).


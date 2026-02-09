## Context

We need reproducible artifacts for distribution. For remote Go modules, the builder must resolve a concrete version and have a local filesystem directory containing the module source for:

- listing packages
- scanning exported functions
- compiling the bridge

## Goals / Non-Goals

**Goals:**
- Support `usegolib build --module <import-path>` with optional `--version`.
- Default remote resolution to `@latest` when version is omitted.
- Record resolved version in `manifest.json`.

**Non-Goals:**
- Implement remote resolution in `usegolib.import_()` itself (runtime still loads from artifacts).
- Implement build cache/locking across processes (later milestone).

## Decisions

- Resolution mechanism: `go mod download -json <module>@<version-or-latest>`.
  - For package paths that are not module roots, resolve module root by trimming path segments until `go mod download` succeeds.
- For local paths (directory exists), parse `go.mod` to obtain module path; label version as `"local"`.
- Bridge module `go.mod`:
  - local: `replace <module> => <dir>`
  - remote: `require <module> <resolved version>` without replace

## Risks / Trade-offs

- Remote module resolution depends on network and Go proxy configuration.
  - Mitigation: keep remote integration tests optional and gated by env var.


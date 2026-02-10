# CLI

`usegolib` installs a `usegolib` command (and also supports `python -m usegolib`).

## Installation

```bash
python -m pip install usegolib
usegolib version
```

## Build Artifacts

Build from a local Go module directory:

```bash
usegolib build --module path/to/go/module --out out/artifacts
```

Build from a remote Go module (downloads via `go mod download`):

```bash
usegolib build --module github.com/HazelnutParadise/insyra@v0.2.14 --out out/artifacts
```

Force rebuild:

```bash
usegolib build --module github.com/HazelnutParadise/insyra@v0.2.14 --out out/artifacts --force
```

Re-download modules before rebuilding (implies `--force`):

```bash
usegolib build --module github.com/HazelnutParadise/insyra@v0.2.14 --out out/artifacts --redownload
```

Notes:
- `--redownload` uses an isolated Go module cache (sets `GOMODCACHE`) under the output root unless `--gomodcache` is provided.
- Building requires a Go toolchain on `PATH` (`go`). Zig is bootstrapped automatically for cgo.
- If Go module downloads fail due to proxy/network issues, retry. If `proxy.golang.org` is blocked/unreliable in your environment, try `GOPROXY=direct`.

## Manage The Artifact Cache

Artifacts are stored in an artifact root directory. By default this is:
- overridden by `USEGOLIB_ARTIFACT_DIR` when set
- otherwise OS cache (see `src/usegolib/paths.py`)

Delete an artifact (dry-run first):

```bash
usegolib artifact rm --module github.com/HazelnutParadise/insyra@v0.2.14
```

Actually delete:

```bash
usegolib artifact rm --module github.com/HazelnutParadise/insyra@v0.2.14 --yes
```

Delete all versions of a module/package for the current platform:

```bash
usegolib artifact rm --module github.com/HazelnutParadise/insyra --all-versions --yes
```

Rebuild into the artifact root (optionally cleaning existing artifacts and re-downloading sources):

```bash
usegolib artifact rebuild --module github.com/HazelnutParadise/insyra@v0.2.14 --clean --redownload
```

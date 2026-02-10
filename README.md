# usegolib

[![CI](https://github.com/TimLai666/usegolib/actions/workflows/ci.yml/badge.svg)](https://github.com/TimLai666/usegolib/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/usegolib.svg)](https://pypi.org/project/usegolib/)
[![Python Versions](https://img.shields.io/pypi/pyversions/usegolib.svg)](https://pypi.org/project/usegolib/)
[![License](https://img.shields.io/github/license/TimLai666/usegolib.svg)](LICENSE)

Call Go libraries from Python by loading a Go-built shared library directly into the Python process.

- No C/C++ glue code written by you
- No background Go process (no daemon / RPC / subprocess)
- MessagePack-based ABI with manifest-driven schema validation

## Status

`usegolib` is early-stage software (v0.x). Expect sharp edges and evolving interfaces.

## How It Works

- Build time (CI / build machine): use the Go toolchain plus an auto-provisioned C compiler (Zig) to build a Go module into a shared library and emit `manifest.json`.
- Runtime (end-user / production): Python loads the shared library and calls it via MessagePack. No daemon, no RPC, no subprocess.

## Requirements

- Python 3.10+
- Go toolchain
  - required for building artifacts (CI / build machine)
  - required in dev if you rely on auto-build (missing artifact triggers a build)
  - not required for end-user runtime if you ship prebuilt artifacts or wheels

## Installation

```bash
python -m pip install usegolib
```

From source (dev):

```bash
python -m pip install -e ".[dev]"
```

## Quickstart

Build an artifact from a local Go module directory:

```bash
usegolib build --module path/to/go/module --out out/artifact
```

Import from the artifact root and call exported functions:

```python
import usegolib

h = usegolib.import_("example.com/mod", artifact_dir="out/artifact")
print(h.AddInt(1, 2))
```

Dev convenience: omit `artifact_dir` to use the default artifact cache root. If the artifact
is missing, `usegolib.import_` will build it into the default cache when a Go toolchain is
available.

```python
import usegolib

h = usegolib.import_("example.com/mod")
print(h.AddInt(1, 2))
```

To enforce "no build" behavior, pass an explicit artifact root and set `build_if_missing=False`:

```python
import usegolib

h = usegolib.import_("example.com/mod", artifact_dir="out/artifact", build_if_missing=False)
```

## Example: Calling Insyra From Python

Insyra is a Go data-analysis library: `github.com/HazelnutParadise/insyra`.

Auto-build on import (developer convenience; downloads the module + builds into usegolib's default artifact root):

```python
import usegolib

insyra = usegolib.import_("github.com/HazelnutParadise/insyra", version="v0.2.14")

# DataList (object handle + variadic any)
dl = insyra.NewDataList()
dl.Append(1, 2, 3, 4, 5)
print(dl.Sum(), dl.Mean())

# DataTable (variadic map[string]any + variadic bool)
dt = insyra.NewDataTable()
dt.AppendRowsByColIndex({"A": 1, "B": 2}, {"A": 3, "B": 4})
print(dt.NumRows(), dt.NumCols())
dt.Show()
```

Notes:

- `usegolib` can only call functions/methods whose parameter and return types are supported by the current type bridge (see `docs/abi.md`).
- This example requires a Go toolchain to be installed. (At the time of writing, `insyra@v0.2.14` requires `go >= 1.25`.)
- If you want to disable auto-build, pass `build_if_missing=False` (and usually an explicit `artifact_dir`).
- For end-users without Go, ship prebuilt artifacts/wheels (see Packaging).

## Methods (Object Handles)

For exported methods, `usegolib` supports Go-side object handles (opaque ids) to avoid serializing the receiver on every call:

```python
with h.object("Counter", {"n": 1}) as c:
    print(c.Inc(2))
```

Typed object handles (schema required):

```python
th = h.typed()
types = th.types

with th.object("Counter", types.Counter(N=10)) as c:
    snap = c.Snapshot()
    print(snap)
```

## Generic Functions (Build-Time Instantiation)

Generic functions require explicit build-time instantiation:

```bash
usegolib build --module example.com/mod --out out/artifact --generics generics.json
```

At runtime (schema required), use the helper:

```python
fn = h.generic("Id", ["int64"])
print(fn(123))
```

## Packaging (Ship Wheels Without Requiring Go)

Generate a distributable Python package project embedding artifacts:

```bash
usegolib package --module path/to/go/module --python-package-name mypkg --out out/
```

Install the generated project:

```bash
python -m pip install -e out/mypkg
```

```python
import mypkg

print(mypkg.AddInt(1, 2))
```

## Version Rules

- One Go module = one version per Python process
- If a module is already loaded, all subpackages must use the same version
- If `version=None` and multiple artifact versions exist under `artifact_dir`, import fails with `AmbiguousArtifactError`

## Documentation

- `docs/roadmap.md`
- `docs/abi.md`
- `docs/cli.md`
- `docs/versioning.md`
- `docs/compatibility.md`
- `docs/testing.md`
- `docs/security.md`
- `docs/troubleshooting.md`
- `docs/releasing.md`

## License

MIT. See `LICENSE`.

# usegolib

**usegolib** lets Python call Go libraries by loading a Go-built shared library directly into the Python process.

- No C/C++ glue code written by you
- No background Go process (no daemon / RPC / subprocess)
- MessagePack-based ABI

## What problem does this solve?

- You have a Go library
- You want Python users to call it like a native Python module
- You do NOT want:
  - C/C++ glue code
  - gopy-style heavy bindings
  - running a Go server or subprocess

## Model

- **Build time (CI / build machine)**: use Go toolchain + an auto-provisioned C compiler (Zig) to build a Go module into a shared library + `manifest.json`.
- **Runtime (end-user / production)**: Python loads the shared library and calls it via MessagePack. Go is not running as a service.

## Requirements

- Python 3.10+
- Go toolchain (build-time only; not required for runtime if you ship prebuilt artifacts/wheels)

## Quickstart (local build + call)

```bash
# Build an artifact from a local Go module directory
python -m usegolib build --module path/to/go/module --out out/artifact
```

Remote module build (build machine):

```bash
python -m usegolib build --module github.com/yourorg/insyra --out out/artifact
```

```python
import usegolib

# Import from an artifact *root* (may contain many modules/versions/platforms)
h = usegolib.import_("example.com/mod", artifact_dir="out/artifact")
print(h.AddInt(1, 2))
```

Convenience (dev): omit `artifact_dir` to use the default artifact cache root.
If the artifact is missing, `usegolib.import_` will build it into the default cache
when a Go toolchain is available.

```python
import usegolib

h = usegolib.import_("example.com/mod")
print(h.AddInt(1, 2))
```

Remote modules/packages (dev): you can also pass a Go import path. If the artifact is
missing in the default cache, `usegolib` will download the module (via `go mod download`)
and build it automatically.

```python
import usegolib

h = usegolib.import_("github.com/yourorg/insyra")
sub = usegolib.import_("github.com/yourorg/insyra/subpkg")
```

Typed wrappers (when schema is present in the artifact manifest):

```python
th = h.typed()
print(th.AddInt(1, 2))
```

## Quickstart (generate a distributable Python package project)

```bash
python -m usegolib package --module path/to/go/module --python-package-name mypkg --out out/
```

Then install the generated project:

```bash
python -m pip install -e out/mypkg
```

```python
import mypkg
print(mypkg.AddInt(1, 2))
```

## Version Rules (important)

- One Go module = one version per Python process
- If a module is already loaded, all subpackages must use the same version
- If `version=None` and multiple artifact versions exist under `artifact_dir`, import fails with `AmbiguousArtifactError`

## Policies

- `docs/versioning.md`: ABI + manifest versioning and compatibility rules
- `docs/compatibility.md`: supported platforms and toolchain pins
- `docs/security.md`: security boundaries and current hardening
- `docs/reproducible-builds.md`: reproducible build guidance

## Releasing

- `docs/releasing.md`

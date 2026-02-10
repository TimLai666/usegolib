# Troubleshooting

Common issues when importing, building, or loading `usegolib` artifacts.

## Import Errors

### `ArtifactNotFoundError`

Meaning: no matching artifact for the requested module/package/version was found under the artifact root.

Fix:
- If you are an end-user: install a wheel that embeds artifacts (via `usegolib package`) or point `artifact_dir` to a directory containing prebuilt artifacts.
- If you are a developer: omit `artifact_dir` (use default cache) or set `build_if_missing=True` to allow building into your artifact root.

### `AmbiguousArtifactError`

Meaning: `version=None` but multiple versions exist for the same module under the artifact root (and the module is not already loaded in the current Python process).

Fix:
- Pass an explicit `version="vX.Y.Z"` (or `"local"` for local module builds), or
- Remove/relocate the extra version(s) under the artifact root.

Note:
- If the module is already loaded in the current process, `usegolib.import_(..., version=None)` follows the already-loaded module version (including for subpackage imports), and does not fail with ambiguity.

Tip: you can delete cached artifacts via the CLI:

```bash
usegolib artifact rm --module example.com/mod@vX.Y.Z --yes
usegolib artifact rm --module example.com/mod --all-versions --yes
```

### `VersionConflictError`

Meaning: the current Python process already loaded one version of a module, and you're trying to load a different version (possibly via a subpackage import).

Fix:
- Ensure all imports use the same module version in a single process.
- Restart the Python process if you need to switch versions.

## Build Errors

### Go toolchain missing / `go` not on PATH

Auto-build (import triggers download/build) requires a Go toolchain.

Fix:
- Install Go, or
- Avoid auto-build: ship prebuilt artifacts/wheels and import with an explicit `artifact_dir` and `build_if_missing=False`.

### Go module download fails (network / proxy)

Symptoms: build logs mention `proxy.golang.org`, `sum.golang.org`, `i/o timeout`, `wsarecv`, or similar network/proxy errors.

Fix:
- Retry (transient failures are common), and
- If `proxy.golang.org` is blocked/unreliable in your environment, try `GOPROXY=direct` and rebuild.

```powershell
$env:GOPROXY="direct"
usegolib artifact rebuild --module example.com/mod@vX.Y.Z --clean --redownload
```

### Go auto-downloads a newer toolchain

If the target module requires a newer Go version, Go may print messages like `go: downloading go1.25.0` during builds.
This requires network access. If you want to avoid auto toolchain downloads, install a suitable Go version up front or configure Go toolchain selection (for example via `GOTOOLCHAIN`).

### Zig bootstrap failures

Meaning: `usegolib` could not download/verify/extract Zig for cgo.

Fix:
- Ensure network access to `https://ziglang.org/`.
- Override Zig binary: set `USEGOLIB_ZIG` (or `ZIG`) to a local Zig executable path.
- If you are pinning: verify `USEGOLIB_ZIG_VERSION` matches an entry in Zig's `index.json`.

## Load Errors

### `LoadError` for SHA256 mismatch

Meaning: the shared library file does not match the hash recorded in `manifest.json`.

Fix:
- Rebuild the artifact (or re-download the artifact root).
- Ensure the artifact root is not modified after build.

### `LoadError` for platform mismatch

Meaning: the artifact was built for a different `goos/goarch` than the current machine.

Fix:
- Build artifacts for your target platform, or install a wheel that includes your platform's artifact.

## WSL (Linux) Local Verification

If you're developing on Windows, run Linux tests via:

```powershell
.\tools\wsl_linux_tests.ps1
.\tools\wsl_linux_tests.ps1 -Integration
```

If integration tests fail because Go is missing in WSL, the integration runner will bootstrap Go automatically (no sudo).

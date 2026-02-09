# Testing

This repo is designed to be verified on all three target OSes (Windows, macOS, Linux).

CI already runs unit and integration tests on `ubuntu-latest`, `windows-latest`, and `macos-latest`.
This document focuses on local workflows, including Linux verification via WSL when developing on Windows.

## Windows (Host)

Unit tests:

```powershell
python -m pytest -q
```

Integration tests (builds a Go shared library via Zig + Go toolchain):

```powershell
$env:USEGOLIB_INTEGRATION="1"
python -m pytest -q -k integration
```

## Windows + WSL (Linux)

Prereqs inside WSL:
- `python3`
- `curl` and `tar` (used for bootstrapping tools without `sudo`)

Unit tests in Linux (WSL):

```powershell
.\tools\wsl_linux_tests.ps1
```

Integration tests in Linux (WSL):

```powershell
.\tools\wsl_linux_tests.ps1 -Integration
```

The integration run will bootstrap a Go toolchain automatically if `go` is not already on `PATH`
(downloaded from `go.dev` into `~/.cache/usegolib/go/...`), so you do not need `sudo apt install golang`.

Advanced overrides:
- `USEGOLIB_WSL_GO_VERSION`: pin Go version (e.g. `1.24.1`; the script will prepend `go`)
- `USEGOLIB_WSL_GO_ROOT`: set the cache root for the downloaded toolchain

By default the script targets the `Ubuntu` WSL distro. To run on a different distro:

```powershell
.\tools\wsl_linux_tests.ps1 -Distro Debian
```

## Notes

- The WSL runner creates a temporary venv at `/tmp/usegolib-venv` and installs `usegolib` editable with `.[dev]`.
- If WSL does not have `pip`/`venv` available from the distro packages, the script bootstraps `uv` (installed under `~/.local/bin`) and uses it to create the venv and install dependencies without `sudo`.
- Integration tests will download and cache Zig under the WSL user's home cache directory (`~/.cache/usegolib`).
- The WSL runner executes a temporary bash script file (written on the Windows side) to avoid stdin/quoting edge cases.

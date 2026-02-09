## Why

`tools/wsl_linux_tests.ps1` captures `wsl.exe` stderr to stdout so the script can surface useful diagnostics. In Windows PowerShell 5.1, expected stderr output from native commands (e.g. `uv` bootstrap progress) can be surfaced as `NativeCommandError` records, creating noisy output even when the command succeeds.

## What Changes

- Update `tools/wsl_linux_tests.ps1` to capture combined stdout/stderr from WSL execution without producing PowerShell error records for expected stderr output.
- Keep behavior identical otherwise (exit code handling, output content, and error throwing on non-zero exit).

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `usegolib-dev`: WSL test runner script output handling (avoid PowerShell error records for expected stderr)

## Impact

- Affected code: `tools/wsl_linux_tests.ps1`
- Developer experience only; no runtime/build/package behavior changes


# Design: WSL Runner Output Capture Without PowerShell Error Records

## Goal

Keep the current behavior (capture full output, throw on non-zero exit) while avoiding `NativeCommandError` noise in Windows PowerShell 5.1 when a native command writes to stderr.

## Approach

Inside `Invoke-WslBash`, execute the WSL command via `cmd.exe /c` and perform `2>&1` redirection at the `cmd` layer:

- `cmd.exe` combines stderr into stdout.
- PowerShell receives only stdout and does not emit error records.
- `$LASTEXITCODE` still reflects the exit code of the `cmd.exe` invocation (which matches the last command executed by `cmd`, i.e. `wsl.exe`).

## Error Handling

- Preserve the existing behavior:
  - capture combined output
  - if exit code is non-zero: throw including the original bash script content + captured output

## Non-Goals

- Changing what is printed (other than removing PowerShell-generated error records).
- Changing venv paths, toolchain bootstrapping, or integration behavior.


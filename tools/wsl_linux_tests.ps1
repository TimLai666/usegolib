param(
  [string]$Distro = "Ubuntu",
  [switch]$Integration,
  [string]$Python = "python3"
)

$ErrorActionPreference = "Stop"

function Invoke-WslBash {
  param(
    [string]$Cmd
  )
  # Avoid stdin piping into `wsl.exe`: we've observed it can subtly alter argv for
  # child processes (pytest receiving a stray "-" argument). Also avoid `bash -lc`
  # with a huge multi-line command string because `wsl.exe` argument parsing is
  # fragile. Instead, write a temp bash script on the Windows side and execute it
  # inside WSL via `/mnt/<drive>/...`.
  $Cmd = $Cmd -replace "`r`n", "`n"
  $tmpWin = [System.IO.Path]::GetTempFileName()
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($tmpWin, $Cmd, $utf8NoBom)
  $tmpWsl = Convert-ToWslPath $tmpWin
  try {
    # Windows PowerShell 5.1 can surface native stderr as `NativeCommandError`
    # records even when the command succeeds. Run via `cmd.exe` and do the
    # redirection there so PowerShell only receives stdout.
    $out = & cmd.exe /c wsl.exe -d $Distro -- bash $tmpWsl "2^>^&1"
    $code = $LASTEXITCODE
  } finally {
    Remove-Item -Force $tmpWin -ErrorAction SilentlyContinue
  }
  if ($code -ne 0) {
    throw "WSL command failed ($code): $Cmd`n$out"
  }
  return (($out | Out-String) -replace "`0", "")
}

$repoWin = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Convert-ToWslPath {
  param([string]$WinPath)
  # Best-effort conversion for drive-backed paths (e.g. C:\repo -> /mnt/c/repo).
  if ($WinPath -match "^([A-Za-z]):\\(.*)$") {
    $drive = $matches[1].ToLower()
    $rest = $matches[2] -replace "\\", "/"
    return "/mnt/$drive/$rest"
  }
  # Fallback to wslpath inside WSL.
  $quoted = $WinPath.Replace("'", "'\\''")
  return (Invoke-WslBash "wslpath -u '$quoted'").Trim()
}

$repoWsl = Convert-ToWslPath $repoWin

$venv = "/tmp/usegolib-venv"
$envLine = ""
if ($Integration) {
  $envLine = "USEGOLIB_INTEGRATION=1"
}

Write-Host ("WSL distro: " + $Distro)
Write-Host ("Repo (Windows): " + $repoWin)
Write-Host ("Repo (WSL): " + $repoWsl)
Write-Host ("Integration: " + ($Integration.IsPresent))

# Create venv in /tmp and install editable package with dev extras.
if ($Integration) {
  Invoke-WslBash @"
set -euo pipefail
cd "$repoWsl"
$Python -V

# Pin Zig version for parity with CI (optional).
if [ -z "`${USEGOLIB_ZIG_VERSION:-}" ] && [ -f "$repoWsl/tools/zig-version.txt" ]; then
  export USEGOLIB_ZIG_VERSION="`$(tr -d '\\r\\n' < "$repoWsl/tools/zig-version.txt")"
fi

# Bootstrap Go toolchain without sudo (needed for integration tests).
if ! command -v go >/dev/null 2>&1; then
  GO_VERSION="`${USEGOLIB_WSL_GO_VERSION:-}"
  if [ -z "`$GO_VERSION" ] && [ -f "$repoWsl/tools/go-version.txt" ]; then
    GO_VERSION="`$(tr -d '\\r\\n' < "$repoWsl/tools/go-version.txt")"
  fi
  if [ -z "`$GO_VERSION" ]; then
    GO_VERSION="`$(curl -LsSf https://go.dev/VERSION?m=text | head -n1)"
  else
    GO_VERSION="go`$GO_VERSION"
  fi

  ARCH="`$(uname -m)"
  case "`$ARCH" in
    x86_64) GOARCH=amd64 ;;
    aarch64|arm64) GOARCH=arm64 ;;
    *) echo "Unsupported arch for Go bootstrap: `$ARCH" >&2; exit 2 ;;
  esac

  GO_ROOT="`${USEGOLIB_WSL_GO_ROOT:-`$HOME/.cache/usegolib/go/`$GO_VERSION}"
  if [ ! -x "`$GO_ROOT/go/bin/go" ]; then
    mkdir -p "`$GO_ROOT"
    tmp="`$(mktemp -d)"
    curl -LsSf -o "`$tmp/go.tgz" "https://go.dev/dl/`$GO_VERSION.linux-`$GOARCH.tar.gz"
    tar -C "`$tmp" -xzf "`$tmp/go.tgz"
    rm -rf "`$GO_ROOT/go"
    mv "`$tmp/go" "`$GO_ROOT/go"
    rm -rf "`$tmp"
  fi
  export PATH="`$GO_ROOT/go/bin:`$PATH"
fi

go version

rm -rf "$venv"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="`$HOME/.local/bin:`$PATH"
fi

uv venv -c "$venv"
uv pip install --python "$venv/bin/python" -e ".[dev]"
$envLine "$venv/bin/python" -m pytest -q
"@
} else {
  Invoke-WslBash @"
set -euo pipefail
cd "$repoWsl"
$Python -V

rm -rf "$venv"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="`$HOME/.local/bin:`$PATH"
fi

uv venv -c "$venv"
uv pip install --python "$venv/bin/python" -e ".[dev]"
"$venv/bin/python" -m pytest -q
"@
}

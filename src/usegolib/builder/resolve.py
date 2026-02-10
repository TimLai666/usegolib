from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ..errors import BuildError


@dataclass(frozen=True)
class ResolvedModule:
    module_path: str
    version: str
    module_dir: Path


def resolve_module_target(*, target: str, version: str | None) -> ResolvedModule:
    """Resolve a builder target to a local module directory and concrete version.

    - If `target` is a local directory, locate the nearest parent containing go.mod
      (allows passing a subdirectory of a module) and return version "local".
    - Otherwise treat `target` as a Go import path (module or package path) and use
      `go mod download -json` to resolve module root and version (defaults to @latest).
    """
    p = Path(target)
    if p.exists() and p.is_dir():
        module_dir = _find_module_root(p.resolve())
        module_path = _read_module_path(module_dir)
        return ResolvedModule(module_path=module_path, version="local", module_dir=module_dir)

    wanted = version
    if wanted is None or wanted == "latest":
        wanted = "@latest"
    mod_path, mod_version, mod_dir = _resolve_remote_module(import_path=target, wanted=wanted)
    return ResolvedModule(module_path=mod_path, version=mod_version, module_dir=mod_dir)


def _read_module_path(module_dir: Path) -> str:
    go_mod = module_dir / "go.mod"
    if not go_mod.exists():
        raise BuildError(f"go.mod not found in {module_dir}")
    for line in go_mod.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("module "):
            return line.split()[1]
    raise BuildError("failed to parse module path from go.mod")


def _find_module_root(start: Path) -> Path:
    p = start
    while True:
        if (p / "go.mod").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    raise BuildError(f"go.mod not found in {start} or any parent directory")


def _resolve_remote_module(*, import_path: str, wanted: str) -> tuple[str, str, Path]:
    # For non-module package paths, trim segments until download succeeds.
    candidate = import_path
    while True:
        try:
            # `go mod download` uses special queries like `@latest`.
            # Allow callers to pass `wanted` with or without the leading "@".
            arg = f"{candidate}{wanted}" if wanted.startswith("@") else f"{candidate}@{wanted}"
            info = _go_mod_download_json(arg)
            mod_path = str(info["Path"])
            mod_version = str(info["Version"])
            mod_dir = Path(str(info["Dir"])).resolve()
            return mod_path, mod_version, mod_dir
        except BuildError:
            # Trim one path segment and try again.
            if "/" not in candidate:
                raise
            candidate = candidate.rsplit("/", 1)[0]


def _go_mod_download_json(arg: str) -> dict:
    # `go mod download` does not require being inside a module, but to be robust
    # across environments, run in a temp directory.
    with tempfile.TemporaryDirectory(prefix="usegolib-moddl-") as td:
        proc = subprocess.run(
            ["go", "mod", "download", "-json", arg],
            cwd=td,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise BuildError(f"go mod download failed for {arg}\n{proc.stdout}")
        out = proc.stdout
        try:
            return json.loads(out)
        except Exception:
            # Go may print non-JSON lines (e.g. toolchain switching messages) to stderr,
            # which we merge into stdout for portability. Extract the first JSON object.
            start = out.find("{")
            if start == -1:
                raise BuildError(f"failed to parse go mod download output for {arg}")
            depth = 0
            end = -1
            for i, ch in enumerate(out[start:], start=start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end == -1:
                raise BuildError(f"failed to parse go mod download output for {arg}")
            try:
                return json.loads(out[start:end])
            except Exception as e:  # noqa: BLE001
                raise BuildError(f"failed to parse go mod download output for {arg}: {e}") from e

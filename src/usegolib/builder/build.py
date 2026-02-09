from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ..errors import BuildError
from .lock import leaf_lock
from .resolve import resolve_module_target
from .reuse import artifact_ready
from .zig import ensure_zig


@dataclass(frozen=True)
class ExportedFunc:
    pkg: str
    name: str
    params: list[str]
    results: list[str]


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise BuildError(f"command failed: {' '.join(cmd)}\n{proc.stdout}")
    return proc.stdout


def _read_module_path(module_dir: Path) -> str:
    go_mod = module_dir / "go.mod"
    if not go_mod.exists():
        raise BuildError(f"go.mod not found in {module_dir}")
    for line in go_mod.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("module "):
            return line.split()[1]
    raise BuildError("failed to parse module path from go.mod")


def _list_packages(module_dir: Path) -> list[str]:
    out = _run(["go", "list", "./..."], cwd=module_dir)
    pkgs = [ln.strip() for ln in out.splitlines() if ln.strip()]
    # Exclude internal packages (Go import rules).
    return [p for p in pkgs if "/internal/" not in p and not p.endswith("/internal")]


def _scan_exported_funcs(module_dir: Path, pkg: str) -> list[ExportedFunc]:
    # Use `go doc` as a cheap scanner for v0.
    out = _run(["go", "doc", "-all", pkg], cwd=module_dir)
    funcs: list[ExportedFunc] = []
    for line in out.splitlines():
        line = line.strip()
        if not line.startswith("func "):
            continue
        sig = line[len("func ") :]
        # Expect: Name(args...) ret  OR  Name(args...) (ret1, ret2)
        # Keep parsing minimal; ignore methods and generics.
        if sig.startswith("("):  # method receiver - ignore
            continue
        name_end = sig.find("(")
        if name_end <= 0:
            continue
        name = sig[:name_end].strip()
        args_and_rest = sig[name_end:]
        args_end = args_and_rest.find(")")
        if args_end < 0:
            continue
        args_str = args_and_rest[1:args_end].strip()
        rest = args_and_rest[args_end + 1 :].strip()

        params: list[str] = []
        if args_str:
            # Very small parser: split by commas, keep last token as type.
            for part in args_str.split(","):
                part = part.strip()
                if not part:
                    continue
                # "a int64" -> type is last token; "[]byte" single token.
                tokens = part.split()
                ptype = tokens[-1]
                params.append(ptype)

        results: list[str] = []
        if rest:
            if rest.startswith("(") and rest.endswith(")"):
                inner = rest[1:-1].strip()
                if inner:
                    for part in inner.split(","):
                        results.append(part.strip().split()[-1])
            else:
                results.append(rest.split()[-1])

        if not results:
            results = []

        funcs.append(ExportedFunc(pkg=pkg, name=name, params=params, results=results))
    return funcs


def _is_supported_type(t: str) -> bool:
    return t in {
        "bool",
        "string",
        "[]byte",
        "int",
        "int8",
        "int16",
        "int32",
        "int64",
        "float32",
        "float64",
        "[]bool",
        "[]string",
        "[]int",
        "[]int64",
        "[]float64",
        "[][]byte",
    }


def _is_supported_sig(fn: ExportedFunc) -> bool:
    if any(not _is_supported_type(t) for t in fn.params):
        return False
    if any(not _is_supported_type(t) and t != "error" for t in fn.results):
        return False
    if len(fn.results) > 2:
        return False
    if len(fn.results) == 2 and fn.results[1] != "error":
        return False
    return True


def _bridge_go_mod(
    *,
    bridge_dir: Path,
    module_path: str,
    module_dir: Path,
    module_version: str,
    local_replace: bool,
) -> None:
    lines: list[str] = [
        "module usegolib.bridge",
        "",
        "go 1.22",
        "",
        "require github.com/vmihailenco/msgpack/v5 v5.4.1",
        f"require {module_path} {module_version}",
        "",
    ]
    if local_replace:
        lines.append(f"replace {module_path} => {module_dir.as_posix()}")
        lines.append("")
    (bridge_dir / "go.mod").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def _go_ext() -> str:
    if sys.platform.startswith("win"):
        return ".dll"
    if sys.platform == "darwin":
        return ".dylib"
    return ".so"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _artifact_leaf_dir(
    *,
    out_root: Path,
    module_path: str,
    version: str,
    goos: str,
    goarch: str,
) -> Path:
    parts = module_path.split("/")
    if not parts:
        raise BuildError(f"invalid module path: {module_path}")
    parts[-1] = f"{parts[-1]}@{version}"
    return out_root.joinpath(*parts, f"{goos}-{goarch}")


def build_artifact(
    *,
    module: str | Path,
    out_dir: Path,
    version: str | None = None,
    force: bool = False,
) -> Path:
    resolved = resolve_module_target(target=str(module), version=version)
    module_dir = resolved.module_dir
    out_root = Path(out_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    module_path = resolved.module_path
    packages = _list_packages(module_dir)

    exported: list[ExportedFunc] = []
    for pkg in packages:
        exported.extend(_scan_exported_funcs(module_dir, pkg))

    exported = [fn for fn in exported if _is_supported_sig(fn)]

    with tempfile.TemporaryDirectory(prefix="usegolib-bridge-") as td:
        bridge_dir = Path(td)
        _bridge_go_mod(
            bridge_dir=bridge_dir,
            module_path=module_path,
            module_dir=module_dir,
            module_version=resolved.version if resolved.version != "local" else "v0.0.0",
            local_replace=(resolved.version == "local"),
        )

        from .gobridge import write_bridge

        write_bridge(bridge_dir=bridge_dir, module_path=module_path, functions=exported)

        goos = _run(["go", "env", "GOOS"], cwd=module_dir).strip()
        goarch = _run(["go", "env", "GOARCH"], cwd=module_dir).strip()

        artifact_version = resolved.version
        out_leaf = _artifact_leaf_dir(
            out_root=out_root,
            module_path=module_path,
            version=artifact_version,
            goos=goos,
            goarch=goarch,
        )
        out_leaf.mkdir(parents=True, exist_ok=True)

        lock_path = out_leaf / ".usegolib.lock"
        with leaf_lock(lock_path):
            if not force and artifact_ready(out_leaf):
                return out_leaf / "manifest.json"

            lib_name = f"libusegolib{_go_ext()}"
            lib_path = out_leaf / lib_name

            zig = ensure_zig()
            env = dict(os.environ)
            env["CGO_ENABLED"] = "1"
            env["CC"] = f"{zig} cc"

            # Ensure module sums exist for reproducible builds.
            _run(["go", "mod", "tidy"], cwd=bridge_dir, env=env)

            # Build the bridge runtime.
            _run(
                ["go", "build", "-buildmode=c-shared", "-o", str(lib_path), "."],
                cwd=bridge_dir,
                env=env,
            )

    sha = _sha256_file(lib_path)
    go_version = _run(["go", "version"], cwd=module_dir).strip()
    zig_version = _run([str(zig), "version"], cwd=module_dir).strip()

    manifest = {
        "manifest_version": 1,
        "abi_version": 0,
        "module": module_path,
        "version": artifact_version,
        "goos": goos,
        "goarch": goarch,
        "go_version": go_version,
        "zig_version": zig_version,
        "packages": packages,
        "symbols": [
            {
                "pkg": fn.pkg,
                "name": fn.name,
                "params": fn.params,
                "results": fn.results,
            }
            for fn in exported
        ],
        "library": {"path": lib_name, "sha256": sha},
    }
    manifest_path = out_leaf / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path

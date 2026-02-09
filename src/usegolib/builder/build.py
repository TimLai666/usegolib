from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from ..errors import BuildError
from .fingerprint import fingerprint_local_module_dir
from .lock import leaf_lock
from .resolve import resolve_module_target
from .reuse import artifact_ready
from .scan import scan_module
from .symbols import ExportedFunc
from .zig import ensure_zig


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


def _is_supported_type(t: str, *, struct_types: set[str] | None = None) -> bool:
    scalars = {
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
    }
    if t in scalars:
        return True
    if t.startswith("*"):
        return _is_supported_type(t[1:], struct_types=struct_types)
    if t.startswith("[]"):
        # []byte is handled above as a special scalar.
        return _is_supported_type(t[2:], struct_types=struct_types)
    if t.startswith("map[string]"):
        vt = t[len("map[string]") :]
        return _is_supported_type(vt, struct_types=struct_types)
    if struct_types and t in struct_types:
        return True
    return False


def _is_supported_sig(fn: ExportedFunc, *, struct_types: set[str] | None = None) -> bool:
    if any(not _is_supported_type(t, struct_types=struct_types) for t in fn.params):
        return False
    if any(not _is_supported_type(t, struct_types=struct_types) and t != "error" for t in fn.results):
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
    scan = scan_module(module_dir=module_dir)
    exported = scan.funcs

    exported = [
        fn
        for fn in exported
        if _is_supported_sig(fn, struct_types=scan.struct_types_by_pkg.get(fn.pkg))
    ]

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

        write_bridge(
            bridge_dir=bridge_dir,
            module_path=module_path,
            functions=exported,
            struct_types_by_pkg=scan.struct_types_by_pkg,
        )

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
            expected_fp: str | None = None
            if artifact_version == "local":
                expected_fp = fingerprint_local_module_dir(module_dir)

            if not force and artifact_ready(out_leaf, expected_input_fingerprint=expected_fp):
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
                "schema": {
                    "structs": {
                        pkg: {
                            name: [{"name": f.name, "type": f.type} for f in fields]
                            for name, fields in scan.structs_by_pkg.get(pkg, {}).items()
                        }
                        for pkg in sorted(scan.structs_by_pkg.keys())
                    },
                    "symbols": [
                        {
                            "pkg": fn.pkg,
                            "name": fn.name,
                            "params": fn.params,
                            "results": fn.results,
                        }
                        for fn in exported
                    ],
                },
                "library": {"path": lib_name, "sha256": sha},
            }
            if expected_fp is not None:
                manifest["input_fingerprint"] = expected_fp

            manifest_path = out_leaf / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            return manifest_path

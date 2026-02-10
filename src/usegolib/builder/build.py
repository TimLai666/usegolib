from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from ..errors import BuildError
from .fingerprint import fingerprint_local_module_dir
from .lock import leaf_lock
from .resolve import resolve_module_target
from .reuse import artifact_ready
from .scan import scan_module
from .symbols import ExportedFunc, ExportedMethod, ExportedVar, GenericFuncDef, GenericInstantiation
from .zig import ensure_zig


_GO_TRANSIENT_NET_RE = re.compile(
    r"("
    r"proxy\.golang\.org"
    r"|sum\.golang\.org"
    r"|wsarecv"
    r"|connection (?:attempt failed|reset)"
    r"|i/o timeout"
    r"|tls handshake timeout"
    r"|unexpected eof"
    r"|temporary failure"
    r"|no such host"
    r"|502 bad gateway"
    r"|503 service unavailable"
    r"|504 gateway timeout"
    r")",
    re.IGNORECASE,
)


def _go_network_hint(out: str) -> str | None:
    if not _GO_TRANSIENT_NET_RE.search(out):
        return None
    return (
        "\n\nHint: Go module download failed due to a network/proxy error. "
        "Try re-running the command. If `proxy.golang.org` is blocked/unreliable "
        "in your environment, try setting `GOPROXY=direct` (or another reachable proxy) "
        "and retry."
    )


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    prog = cmd[0] if cmd else "<unknown>"

    # Go commands that touch the module graph frequently fail due to transient
    # proxy/network issues. Retry with a short backoff and optionally fall back
    # to GOPROXY=direct if the proxy is the failing hop.
    max_attempts = 1
    if prog == "go":
        max_attempts = 3

    base_env = env
    cur_env = env
    backoff_s = 0.5
    last_out = ""

    for attempt in range(max_attempts):
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(cwd),
                env=cur_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                check=False,
            )
        except FileNotFoundError as e:
            if prog == "go":
                raise BuildError(
                    "Go toolchain not found (`go` is missing from PATH). "
                    "Install Go and ensure `go` is available on PATH. "
                    "If you do not want auto-build on import, pass `build_if_missing=False` "
                    "(and use prebuilt artifacts/wheels)."
                ) from e
            raise BuildError(f"command not found: {prog}") from e

        stdout = (proc.stdout or b"").decode("utf-8", errors="replace")
        stderr = (proc.stderr or b"").decode("utf-8", errors="replace")
        out = "\n".join([s for s in [stdout.strip("\n"), stderr.strip("\n")] if s]) + "\n"
        last_out = out

        if proc.returncode == 0:
            return stdout

        # Retry only for `go` and only when we see a likely transient network error.
        if prog == "go" and attempt < max_attempts - 1 and _GO_TRANSIENT_NET_RE.search(out):
            # First retry: if the proxy seems to be the failing hop and GOPROXY is not
            # explicitly set, try falling back to GOPROXY=direct for the next attempt.
            if "proxy.golang.org" in out.lower():
                if base_env is None:
                    # Caller didn't pass env: copy process env so we can safely override.
                    next_env = dict(os.environ)
                else:
                    next_env = dict(base_env)
                if "GOPROXY" not in next_env:
                    next_env["GOPROXY"] = "direct"
                    cur_env = next_env
            time.sleep(backoff_s)
            backoff_s *= 2.0
            continue

        hint = _go_network_hint(out)
        if hint:
            out = out.rstrip("\n") + hint + "\n"
        raise BuildError(f"command failed: {' '.join(cmd)}\n{out}")

    # Defensive: loop always returns/raises, but keep a fallback.
    hint = _go_network_hint(last_out)
    if hint:
        last_out = last_out.rstrip("\n") + hint + "\n"
    raise BuildError(f"command failed: {' '.join(cmd)}\n{last_out}")


def _read_module_path(module_dir: Path) -> str:
    go_mod = module_dir / "go.mod"
    if not go_mod.exists():
        raise BuildError(f"go.mod not found in {module_dir}")
    for line in go_mod.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("module "):
            return line.split()[1]
    raise BuildError("failed to parse module path from go.mod")


def _list_packages(module_dir: Path, *, env: dict[str, str] | None = None) -> list[str]:
    out = _run(["go", "list", "./..."], cwd=module_dir, env=env)
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
    if t == "any":
        return True
    if t in scalars:
        return True
    if t == "time.Time":
        return True
    if t == "time.Duration":
        return True
    if t == "uuid.UUID":
        return True
    if t.startswith("*"):
        return _is_supported_type(t[1:], struct_types=struct_types)
    if t.startswith("[]"):
        # []byte is handled above as a special scalar.
        return _is_supported_type(t[2:], struct_types=struct_types)
    if t.startswith("..."):
        return _is_supported_type("[]" + t[3:], struct_types=struct_types)
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


def _is_supported_method_sig(m: ExportedMethod, *, struct_types: set[str] | None = None) -> bool:
    if any(not _is_supported_type(t, struct_types=struct_types) for t in m.params):
        return False
    if any(not _is_supported_type(t, struct_types=struct_types) and t != "error" for t in m.results):
        return False
    if len(m.results) > 2:
        return False
    if len(m.results) == 2 and m.results[1] != "error":
        return False
    return True


def _substitute_type(t: str, mapping: dict[str, str]) -> str:
    t = t.strip()
    if t.startswith("*"):
        return "*" + _substitute_type(t[1:], mapping)
    if t.startswith("[]"):
        return "[]" + _substitute_type(t[2:], mapping)
    if t.startswith("map[string]"):
        return "map[string]" + _substitute_type(t[len("map[string]") :], mapping)
    return mapping.get(t, t)


def _mangle_type_for_symbol(t: str) -> str:
    t = t.strip()
    # Stable-ish mangling for type argument tokens.
    t = t.replace("map[string]", "mapstr_")
    t = t.replace("[]", "slice_")
    t = t.replace("*", "ptr_")
    for ch in ["/", ".", "[", "]", " ", "{", "}", ",", ":", ";", "(", ")", "<", ">", "|", "~", "&", "!"]:
        t = t.replace(ch, "_")
    while "__" in t:
        t = t.replace("__", "_")
    return t.strip("_") or "T"


def _default_generic_symbol(name: str, type_args: list[str]) -> str:
    suffix = "_".join(_mangle_type_for_symbol(t) for t in type_args)
    return f"{name}__{suffix}" if suffix else f"{name}__inst"


def _load_generic_instantiations(
    *,
    generics: Path,
    defs: list[GenericFuncDef],
    struct_types_by_pkg: dict[str, set[str]],
) -> list[GenericInstantiation]:
    generics = Path(generics)
    if not generics.exists():
        raise BuildError(f"generics config not found: {generics}")
    try:
        obj = json.loads(generics.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        raise BuildError(f"failed to parse generics config JSON: {e}") from e
    insts = obj.get("instantiations") if isinstance(obj, dict) else None
    if not isinstance(insts, list):
        raise BuildError("generics config must be a JSON object with an 'instantiations' list")

    defs_by_pkg_name: dict[tuple[str, str], GenericFuncDef] = {}
    for d in defs:
        defs_by_pkg_name[(d.pkg, d.name)] = d

    out: list[GenericInstantiation] = []
    seen_symbols: set[tuple[str, str]] = set()
    ident_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    for item in insts:
        if not isinstance(item, dict):
            continue
        pkg = item.get("pkg")
        name = item.get("name")
        type_args = item.get("type_args")
        symbol = item.get("symbol")
        if not isinstance(pkg, str) or not isinstance(name, str):
            raise BuildError("generics instantiation entry must include 'pkg' and 'name' strings")
        if not isinstance(type_args, list) or not all(isinstance(x, str) for x in type_args):
            raise BuildError("generics instantiation entry must include 'type_args' list[str]")
        if symbol is None:
            symbol = _default_generic_symbol(name, list(type_args))
        if not isinstance(symbol, str) or not symbol:
            raise BuildError("generics instantiation 'symbol' must be a non-empty string when provided")
        if not ident_re.fullmatch(symbol):
            raise BuildError(
                f"generics instantiation 'symbol' must be a valid identifier (got {symbol!r})"
            )

        d = defs_by_pkg_name.get((pkg, name))
        if d is None:
            avail = sorted({f"{dp}.{dn}" for (dp, dn) in defs_by_pkg_name.keys()})
            raise BuildError(
                f"generic function not found: {pkg}.{name}. "
                f"available: {', '.join(avail) if avail else '(none)'}"
            )
        if len(type_args) != len(d.type_params):
            raise BuildError(
                f"generic instantiation arity mismatch for {pkg}.{name}: "
                f"expected {len(d.type_params)} type args, got {len(type_args)}"
            )

        # Validate type args: must be supported scalar/adapter/container or a named struct in the same pkg.
        struct_types = struct_types_by_pkg.get(pkg, set())
        for ta in type_args:
            base = ta.strip()
            while True:
                if base.startswith("*"):
                    base = base[1:].strip()
                    continue
                if base.startswith("[]"):
                    base = base[2:].strip()
                    continue
                if base.startswith("map[string]"):
                    base = base[len("map[string]") :].strip()
                    continue
                break
            if base in struct_types:
                continue
            if not _is_supported_type(ta, struct_types=struct_types):
                raise BuildError(f"unsupported generic type arg: {ta} (for {pkg}.{name})")

        mapping = {tp: ta for tp, ta in zip(d.type_params, type_args, strict=True)}
        inst_params = [_substitute_type(t, mapping) for t in d.params]
        inst_results = [_substitute_type(t, mapping) for t in d.results]

        gi = GenericInstantiation(
            pkg=pkg,
            generic_name=name,
            type_args=list(type_args),
            symbol=symbol,
            params=inst_params,
            results=inst_results,
            doc=d.doc,
        )
        if not _is_supported_sig(
            ExportedFunc(pkg=pkg, name=symbol, params=inst_params, results=inst_results),
            struct_types=struct_types_by_pkg.get(pkg),
        ):
            raise BuildError(f"generic instantiation produces unsupported signature: {pkg}:{symbol}")

        key = (pkg, symbol)
        if key in seen_symbols:
            raise BuildError(f"duplicate generic symbol: {pkg}:{symbol}")
        seen_symbols.add(key)
        out.append(gi)

    return out


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
    generics: Path | None = None,
    gomodcache_dir: Path | None = None,
    clean_gomodcache: bool = False,
) -> Path:
    env_base = dict(os.environ)
    if gomodcache_dir is not None:
        gomodcache_dir = Path(gomodcache_dir).resolve()
        if clean_gomodcache and gomodcache_dir.exists():
            shutil.rmtree(gomodcache_dir, ignore_errors=True)
        gomodcache_dir.mkdir(parents=True, exist_ok=True)
        env_base["GOMODCACHE"] = str(gomodcache_dir)

    resolved = resolve_module_target(target=str(module), version=version, env=env_base)
    module_dir = resolved.module_dir
    out_root = Path(out_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    module_path = resolved.module_path
    packages = _list_packages(module_dir, env=env_base)
    scan = scan_module(module_dir=module_dir, env=env_base)
    exported = scan.funcs
    methods = scan.methods
    generic_defs = scan.generic_funcs
    vars_ = scan.vars

    exported = [
        fn
        for fn in exported
        if _is_supported_sig(fn, struct_types=scan.struct_types_by_pkg.get(fn.pkg))
    ]
    methods = [
        m
        for m in methods
        if _is_supported_method_sig(m, struct_types=scan.struct_types_by_pkg.get(m.pkg))
    ]

    # Vars: only expose exported vars whose type is a named struct type in the same package.
    # This supports "namespace" patterns like `isr.DL.Of(...)`.
    usable_vars: list[ExportedVar] = []
    for v in vars_:
        base = v.type.strip()
        if base.startswith("*"):
            base = base[1:].strip()
        if not base:
            continue
        if "." in base or "/" in base:
            continue
        if base not in scan.struct_types_by_pkg.get(v.pkg, set()):
            continue
        usable_vars.append(v)

    # Methods for bridge wrappers require exported receiver type names (the bridge package
    # cannot reference unexported identifiers from imported packages). Unexported receiver
    # methods remain in the manifest schema and are invoked via reflective dispatch.
    methods_for_bridge = [m for m in methods if m.recv[:1].isupper()]

    generic_insts: list[GenericInstantiation] = []
    if generics is not None:
        generic_insts = _load_generic_instantiations(
            generics=Path(generics),
            defs=generic_defs,
            struct_types_by_pkg=scan.struct_types_by_pkg,
        )

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

        # Adapter types (stdlib or other well-known types) used by supported symbols/structs.
        adapter_types: set[str] = set()
        for fn in exported:
            if "time.Time" in fn.params or "time.Time" in fn.results:
                adapter_types.add("time.Time")
            if "time.Duration" in fn.params or "time.Duration" in fn.results:
                adapter_types.add("time.Duration")
            if "uuid.UUID" in fn.params or "uuid.UUID" in fn.results:
                adapter_types.add("uuid.UUID")
        for m in methods:
            if "time.Time" in m.params or "time.Time" in m.results:
                adapter_types.add("time.Time")
            if "time.Duration" in m.params or "time.Duration" in m.results:
                adapter_types.add("time.Duration")
            if "uuid.UUID" in m.params or "uuid.UUID" in m.results:
                adapter_types.add("uuid.UUID")
        for gi in generic_insts:
            if "time.Time" in gi.params or "time.Time" in gi.results:
                adapter_types.add("time.Time")
            if "time.Duration" in gi.params or "time.Duration" in gi.results:
                adapter_types.add("time.Duration")
            if "uuid.UUID" in gi.params or "uuid.UUID" in gi.results:
                adapter_types.add("uuid.UUID")
        for pkg, by_name in scan.structs_by_pkg.items():
            for _name, fields in by_name.items():
                for f in fields:
                    if "time.Time" in f.type:
                        adapter_types.add("time.Time")
                    if "time.Duration" in f.type:
                        adapter_types.add("time.Duration")
                    if "uuid.UUID" in f.type:
                        adapter_types.add("uuid.UUID")

        # Struct types discovered in the package, but with no exported fields in the
        # schema. For pointers to these types, we treat values as opaque object
        # handles (uint64 ids), so the returned value remains callable in Python.
        opaque_struct_types_by_pkg: dict[str, set[str]] = {}
        all_pkgs = set(scan.struct_types_by_pkg.keys()) | set(scan.structs_by_pkg.keys())
        for pkg in all_pkgs:
            all_structs = set(scan.struct_types_by_pkg.get(pkg, set()))
            with_fields = set(scan.structs_by_pkg.get(pkg, {}).keys())
            opaque = all_structs - with_fields
            # Unexported structs are always treated as opaque object handles.
            opaque |= {n for n in all_structs if not n[:1].isupper()}
            if opaque:
                opaque_struct_types_by_pkg[pkg] = opaque

        write_bridge(
            bridge_dir=bridge_dir,
            module_path=module_path,
            functions=exported,
            methods=methods_for_bridge,
            generic_instantiations=generic_insts,
            vars=usable_vars,
            struct_types_by_pkg=scan.struct_types_by_pkg,
            opaque_struct_types_by_pkg=opaque_struct_types_by_pkg,
            adapter_types=adapter_types,
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
            env = dict(env_base)
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

            all_symbol_entries: list[dict[str, Any]] = [
                {
                    "pkg": fn.pkg,
                    "name": fn.name,
                    "params": fn.params,
                    "results": fn.results,
                    "doc": fn.doc,
                }
                for fn in exported
            ]
            all_symbol_entries.extend(
                [
                    {
                        "pkg": gi.pkg,
                        "name": gi.symbol,
                        "params": gi.params,
                        "results": gi.results,
                        "doc": gi.doc,
                        "generic": {"name": gi.generic_name, "type_args": gi.type_args},
                    }
                    for gi in generic_insts
                ]
            )

            # Ensure schema includes struct entries for all discovered struct types,
            # even when a struct has zero exported fields (empty schema). This matters
            # for methods that return fluent receivers like `*DataList`.
            struct_schema: dict[str, dict[str, list[dict[str, Any]]]] = {}
            all_pkgs = set(scan.struct_types_by_pkg.keys()) | set(scan.structs_by_pkg.keys())
            for pkg in sorted(all_pkgs):
                names = set(scan.struct_types_by_pkg.get(pkg, set())) | set(
                    scan.structs_by_pkg.get(pkg, {}).keys()
                )
                by_name: dict[str, list[dict[str, Any]]] = {}
                for name in sorted(names):
                    # Treat unexported structs as opaque by default: even if they have
                    # exported fields (e.g. embedded pointers), passing them as record
                    # dicts breaks fluent/method APIs. They are represented as object handles.
                    if not name[:1].isupper():
                        fields = []
                    else:
                        fields = scan.structs_by_pkg.get(pkg, {}).get(name, [])
                    by_name[name] = [
                        {
                            "name": f.name,
                            "type": f.type,
                            "key": f.key,
                            "aliases": f.aliases,
                            "omitempty": f.omitempty,
                            "embedded": f.embedded,
                            "required": ((not f.type.strip().startswith("*")) and (not f.omitempty)),
                        }
                        for f in fields
                    ]
                if by_name:
                    struct_schema[pkg] = by_name

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
                "symbols": list(all_symbol_entries),
                "schema": {
                    "structs": struct_schema,
                    "symbols": list(all_symbol_entries),
                    "methods": [
                        {
                            "pkg": m.pkg,
                            "recv": m.recv,
                            "name": m.name,
                            "params": m.params,
                            "results": m.results,
                            "doc": m.doc,
                        }
                        for m in methods
                    ],
                    "generics": [
                        {
                            "pkg": gi.pkg,
                            "name": gi.generic_name,
                            "type_args": gi.type_args,
                            "symbol": gi.symbol,
                        }
                        for gi in generic_insts
                    ],
                    "vars": [
                        {
                            "pkg": v.pkg,
                            "name": v.name,
                            "type": v.type,
                            "doc": v.doc,
                        }
                        for v in usable_vars
                    ],
                },
                "library": {"path": lib_name, "sha256": sha},
            }
            if expected_fp is not None:
                manifest["input_fingerprint"] = expected_fp

            manifest_path = out_leaf / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            return manifest_path

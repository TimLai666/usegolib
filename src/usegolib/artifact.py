"""Artifact discovery and manifest parsing."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import AmbiguousArtifactError, ArtifactNotFoundError, LoadError
from .runtime.platform import host_goarch, host_goos


@dataclass(frozen=True)
class ArtifactManifest:
    manifest_version: int
    abi_version: int
    module: str
    version: str
    goos: str
    goarch: str
    packages: list[str]
    symbols: list[dict[str, Any]]
    schema: dict[str, Any] | None
    library_path: Path
    library_sha256: str


_INDEX_VERSION = 1
_INDEX_NAME = ".usegolib-index.json"


def _index_path(root: Path) -> Path:
    return Path(root) / _INDEX_NAME


def read_manifest(path_or_dir: Path) -> ArtifactManifest:
    path_or_dir = Path(path_or_dir)
    manifest_path = path_or_dir
    if manifest_path.is_dir():
        manifest_path = manifest_path / "manifest.json"

    if not manifest_path.exists():
        raise ArtifactNotFoundError(f"manifest.json not found at {manifest_path}")

    try:
        obj = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 - boundary parse
        raise LoadError(f"failed to parse manifest.json: {e}") from e

    try:
        manifest_version = int(obj["manifest_version"])
        abi_version = int(obj["abi_version"])
    except Exception as e:  # noqa: BLE001 - boundary parse
        raise LoadError(f"invalid manifest version fields: {e}") from e

    if manifest_version != 1:
        raise LoadError(f"unsupported manifest_version: {manifest_version}")
    if abi_version != 0:
        raise LoadError(f"unsupported abi_version: {abi_version}")

    lib = obj.get("library") or {}
    schema = obj.get("schema")
    if not isinstance(schema, dict):
        schema = None
    lib_path = Path(lib.get("path", ""))
    if not lib_path.is_absolute():
        lib_path = manifest_path.parent / lib_path

    try:
        return ArtifactManifest(
        manifest_version=manifest_version,
        abi_version=abi_version,
        module=str(obj["module"]),
        version=str(obj["version"]),
        goos=str(obj["goos"]),
        goarch=str(obj["goarch"]),
        packages=list(obj.get("packages", [])),
        symbols=list(obj.get("symbols", [])),
        schema=schema,
        library_path=lib_path,
        library_sha256=str(lib.get("sha256", "")),
    )
    except Exception as e:  # noqa: BLE001 - boundary parse
        raise LoadError(f"invalid manifest.json schema: {e}") from e


def load_artifact(path_or_dir: str | Path):
    # Imported from `__init__` to form the public API.
    from .handle import PackageHandle  # local import to avoid cycles

    manifest = read_manifest(Path(path_or_dir))
    return PackageHandle.from_manifest(manifest, package=manifest.module)


def _scan_manifest_dirs(artifact_root: Path) -> list[Path]:
    # Note: `rglob` cost is amortized via the index cache.
    return [p.parent for p in Path(artifact_root).rglob("manifest.json")]


def _build_index(artifact_root: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    root = Path(artifact_root)
    for d in _scan_manifest_dirs(root):
        try:
            m = read_manifest(d)
        except Exception:
            continue
        try:
            rel = d.relative_to(root).as_posix()
        except Exception:
            # Only index manifests under the artifact root.
            continue
        entries.append(
            {
                "manifest_dir": rel,
                "module": m.module,
                "version": m.version,
                "goos": m.goos,
                "goarch": m.goarch,
                "packages": m.packages,
            }
        )
    return {"index_version": _INDEX_VERSION, "entries": entries}


def _write_index_atomic(artifact_root: Path, index_obj: dict[str, Any]) -> None:
    root = Path(artifact_root)
    path = _index_path(root)
    root.mkdir(parents=True, exist_ok=True)

    # Atomic replace to be safe under concurrent writers.
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(root))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(index_obj, f, indent=2)
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except OSError:
            pass


def _load_index(artifact_root: Path) -> dict[str, Any] | None:
    path = _index_path(Path(artifact_root))
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    if obj.get("index_version") != _INDEX_VERSION:
        return None
    entries = obj.get("entries")
    if not isinstance(entries, list):
        return None
    return obj


def _resolve_from_index(
    artifact_root: Path, *, package: str, version: str | None, goos: str, goarch: str
) -> list[ArtifactManifest]:
    obj = _load_index(artifact_root)
    if obj is None:
        return []

    root = Path(artifact_root)
    candidates: list[ArtifactManifest] = []
    dirty = False
    for e in obj.get("entries", []):
        if not isinstance(e, dict):
            dirty = True
            continue
        if e.get("goos") != goos or e.get("goarch") != goarch:
            continue
        pkgs = e.get("packages")
        if not isinstance(pkgs, list) or package not in pkgs:
            continue
        if version is not None and e.get("version") != version:
            continue

        rel = e.get("manifest_dir")
        if not isinstance(rel, str) or not rel:
            dirty = True
            continue
        manifest_dir = root / Path(rel)
        try:
            m = read_manifest(manifest_dir)
        except Exception:
            dirty = True
            continue
        candidates.append(m)

    # If the index appears out-of-date, rebuild it for next time.
    if dirty:
        try:
            _write_index_atomic(root, _build_index(root))
        except Exception:
            pass
    return candidates


def resolve_manifest(
    artifact_root: Path, *, package: str, version: str | None
) -> ArtifactManifest:
    goos = host_goos()
    goarch = host_goarch()

    candidates: list[ArtifactManifest] = []
    # Index is a performance optimization. For `version=None`, correctness matters
    # more than speed: a stale index could hide ambiguity. In that case, fall back
    # to scan-based resolution.
    if version is not None:
        candidates.extend(
            _resolve_from_index(
                Path(artifact_root),
                package=package,
                version=version,
                goos=goos,
                goarch=goarch,
            )
        )

    if not candidates:
        # Fallback: scan the directory and rebuild the index.
        scanned: list[ArtifactManifest] = []
        for d in _scan_manifest_dirs(Path(artifact_root)):
            try:
                m = read_manifest(d)
            except Exception:
                continue
            if m.goos != goos or m.goarch != goarch:
                continue
            if package not in m.packages:
                continue
            if version is not None and m.version != version:
                continue
            scanned.append(m)
        candidates = scanned
        try:
            _write_index_atomic(Path(artifact_root), _build_index(Path(artifact_root)))
        except Exception:
            pass

    if not candidates:
        wanted = f"{package}@{version}" if version else package
        raise ArtifactNotFoundError(
            f"no matching artifact found for {wanted} on {goos}/{goarch} under {artifact_root}"
        )

    if version is None and len(candidates) != 1:
        versions = sorted({c.version for c in candidates})
        raise AmbiguousArtifactError(
            f"multiple artifacts found for {package} on {goos}/{goarch}: {versions}"
        )

    # version specified: take first (should be unique in a well-formed artifact dir)
    return candidates[0]

"""Artifact discovery and manifest parsing."""

from __future__ import annotations

import json
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


def resolve_manifest(
    artifact_root: Path, *, package: str, version: str | None
) -> ArtifactManifest:
    goos = host_goos()
    goarch = host_goarch()

    candidates: list[ArtifactManifest] = []
    for p in Path(artifact_root).rglob("manifest.json"):
        try:
            m = read_manifest(p.parent)
        except Exception:
            continue
        if m.goos != goos or m.goarch != goarch:
            continue
        if package not in m.packages:
            continue
        if version is not None and m.version != version:
            continue
        candidates.append(m)

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

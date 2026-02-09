"""Artifact discovery and manifest parsing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ArtifactNotFoundError


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
    library_path: Path
    library_sha256: str


def read_manifest(path_or_dir: Path) -> ArtifactManifest:
    path_or_dir = Path(path_or_dir)
    manifest_path = path_or_dir
    if manifest_path.is_dir():
        manifest_path = manifest_path / "manifest.json"

    if not manifest_path.exists():
        raise ArtifactNotFoundError(f"manifest.json not found at {manifest_path}")

    obj = json.loads(manifest_path.read_text(encoding="utf-8"))
    lib = obj.get("library") or {}
    lib_path = Path(lib.get("path", ""))
    if not lib_path.is_absolute():
        lib_path = manifest_path.parent / lib_path

    return ArtifactManifest(
        manifest_version=int(obj["manifest_version"]),
        abi_version=int(obj["abi_version"]),
        module=str(obj["module"]),
        version=str(obj["version"]),
        goos=str(obj["goos"]),
        goarch=str(obj["goarch"]),
        packages=list(obj.get("packages", [])),
        symbols=list(obj.get("symbols", [])),
        library_path=lib_path,
        library_sha256=str(lib.get("sha256", "")),
    )


def load_artifact(path_or_dir: str | Path):
    # Imported from `__init__` to form the public API.
    from .handle import ModuleHandle  # local import to avoid cycles

    manifest = read_manifest(Path(path_or_dir))
    return ModuleHandle.from_manifest(manifest)


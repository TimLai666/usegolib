from __future__ import annotations

import json
from pathlib import Path

from usegolib.artifact import delete_artifacts, find_manifest_dirs
from usegolib.runtime.platform import host_goarch, host_goos


def _write_manifest(dir_path: Path, *, module: str, version: str, packages: list[str]) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    obj = {
        "manifest_version": 1,
        "abi_version": 0,
        "module": module,
        "version": version,
        "goos": host_goos(),
        "goarch": host_goarch(),
        "packages": packages,
        "symbols": [],
        "schema": None,
        "library": {"path": "libusegolib.so", "sha256": "0" * 64},
    }
    (dir_path / "manifest.json").write_text(json.dumps(obj), encoding="utf-8")


def test_delete_artifacts_by_version(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    leaf1 = root / "example.com" / "p@v1.0.0" / f"{host_goos()}-{host_goarch()}"
    leaf2 = root / "example.com" / "p@v2.0.0" / f"{host_goos()}-{host_goarch()}"
    _write_manifest(leaf1, module="example.com/p", version="v1.0.0", packages=["example.com/p"])
    _write_manifest(leaf2, module="example.com/p", version="v2.0.0", packages=["example.com/p"])

    dirs = find_manifest_dirs(root, package="example.com/p", version="v1.0.0")
    assert leaf1 in dirs
    assert leaf2 not in dirs

    deleted = delete_artifacts(root, package="example.com/p", version="v1.0.0")
    assert leaf1 in deleted
    assert not leaf1.exists()
    assert leaf2.exists()


def test_delete_artifacts_all_versions(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    leaf1 = root / "example.com" / "p@v1.0.0" / f"{host_goos()}-{host_goarch()}"
    leaf2 = root / "example.com" / "p@v2.0.0" / f"{host_goos()}-{host_goarch()}"
    _write_manifest(leaf1, module="example.com/p", version="v1.0.0", packages=["example.com/p"])
    _write_manifest(leaf2, module="example.com/p", version="v2.0.0", packages=["example.com/p"])

    deleted = delete_artifacts(root, package="example.com/p", version=None, all_versions=True)
    assert leaf1 in deleted
    assert leaf2 in deleted
    assert not leaf1.exists()
    assert not leaf2.exists()


import hashlib
import json
from pathlib import Path

import pytest


def _host_platform():
    from usegolib.runtime.platform import host_goarch, host_goos

    return host_goos(), host_goarch()


def _ext(goos: str) -> str:
    if goos == "windows":
        return ".dll"
    if goos == "darwin":
        return ".dylib"
    return ".so"


def _write_artifact(
    leaf: Path,
    *,
    module: str,
    version: str,
    packages: list[str] | None = None,
) -> None:
    from usegolib.runtime.platform import host_goarch, host_goos

    goos = host_goos()
    goarch = host_goarch()
    ext = _ext(goos)
    if packages is None:
        packages = [module]

    leaf.mkdir(parents=True, exist_ok=True)
    lib_path = leaf / f"libusegolib{ext}"
    lib_bytes = b""
    lib_path.write_bytes(lib_bytes)
    sha = hashlib.sha256(lib_bytes).hexdigest()

    manifest = {
        "manifest_version": 1,
        "abi_version": 0,
        "module": module,
        "version": version,
        "goos": goos,
        "goarch": goarch,
        "packages": packages,
        "symbols": [],
        "library": {"path": lib_path.name, "sha256": sha},
    }
    (leaf / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_import_creates_index_file(tmp_path: Path):
    from usegolib.artifact import resolve_manifest

    _write_artifact(tmp_path / "a", module="example.com/mod", version="v1.0.0")
    m = resolve_manifest(tmp_path, package="example.com/mod", version="v1.0.0")
    assert m.module == "example.com/mod"
    assert (tmp_path / ".usegolib-index.json").exists()


def test_stale_index_falls_back_to_scan(tmp_path: Path):
    from usegolib.artifact import resolve_manifest

    leaf = tmp_path / "a"
    _write_artifact(leaf, module="example.com/mod", version="v1.0.0")

    # Create index.
    resolve_manifest(tmp_path, package="example.com/mod", version="v1.0.0")

    # Delete the leaf manifest to make the index stale.
    (leaf / "manifest.json").unlink()

    # Add a new valid leaf.
    leaf2 = tmp_path / "b"
    _write_artifact(leaf2, module="example.com/mod", version="v2.0.0")

    m = resolve_manifest(tmp_path, package="example.com/mod", version="v2.0.0")
    assert m.version == "v2.0.0"


def test_new_manifest_after_index_is_discovered(tmp_path: Path):
    from usegolib.artifact import resolve_manifest

    _write_artifact(tmp_path / "a", module="example.com/mod", version="v1.0.0")
    resolve_manifest(tmp_path, package="example.com/mod", version="v1.0.0")
    assert (tmp_path / ".usegolib-index.json").exists()

    # Add a new leaf after the index was created; the resolver should fall back and rebuild.
    _write_artifact(tmp_path / "b", module="example.com/mod", version="v2.0.0")

    m = resolve_manifest(tmp_path, package="example.com/mod", version="v2.0.0")
    assert m.version == "v2.0.0"

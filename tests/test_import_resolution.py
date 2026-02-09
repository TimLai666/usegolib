import json
from pathlib import Path

import pytest


def _write_manifest(
    dirpath: Path,
    *,
    module: str,
    version: str,
    goos: str = "windows",
    goarch: str = "amd64",
    packages: list[str] | None = None,
) -> None:
    if packages is None:
        packages = [module]
    manifest = {
        "manifest_version": 1,
        "abi_version": 0,
        "module": module,
        "version": version,
        "goos": goos,
        "goarch": goarch,
        "packages": packages,
        "symbols": [],
        "library": {"path": "libusegolib.dll", "sha256": "00" * 32},
    }
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_import_raises_ambiguous_when_multiple_versions(tmp_path: Path):
    import usegolib

    # Two artifacts for the same module, same platform, different versions.
    _write_manifest(tmp_path / "a", module="example.com/mod", version="v1.0.0")
    _write_manifest(tmp_path / "b", module="example.com/mod", version="v2.0.0")

    with pytest.raises(usegolib.errors.AmbiguousArtifactError):
        usegolib.import_("example.com/mod", artifact_dir=tmp_path)


def test_import_selects_requested_version(tmp_path: Path):
    import usegolib

    _write_manifest(tmp_path / "a", module="example.com/mod", version="v1.0.0")
    _write_manifest(tmp_path / "b", module="example.com/mod", version="v2.0.0")

    h = usegolib.import_("example.com/mod", version="v2.0.0", artifact_dir=tmp_path)
    assert h.module == "example.com/mod"
    assert h.version == "v2.0.0"


def test_import_subpackage_binds_package(tmp_path: Path):
    import usegolib

    _write_manifest(
        tmp_path / "x",
        module="example.com/mod",
        version="v1.0.0",
        packages=["example.com/mod", "example.com/mod/subpkg"],
    )

    h = usegolib.import_("example.com/mod/subpkg", version="v1.0.0", artifact_dir=tmp_path)
    assert h.package == "example.com/mod/subpkg"


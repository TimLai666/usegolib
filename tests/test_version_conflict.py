import json
from pathlib import Path


def _write_manifest(dirpath: Path, module: str, version: str) -> None:
    manifest = {
        "manifest_version": 1,
        "abi_version": 0,
        "module": module,
        "version": version,
        "goos": "windows",
        "goarch": "amd64",
        "packages": [module],
        "symbols": [],
        "library": {"path": "libusegolib.dll", "sha256": "00" * 32},
    }
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_version_conflict_is_rejected(tmp_path: Path):
    import usegolib

    a = tmp_path / "a"
    b = tmp_path / "b"
    _write_manifest(a, "example.com/mod", "v1.2.0")
    _write_manifest(b, "example.com/mod", "v1.3.0")

    usegolib.load_artifact(a)
    try:
        usegolib.load_artifact(b)
    except usegolib.errors.VersionConflictError:
        pass
    else:
        raise AssertionError("expected VersionConflictError")


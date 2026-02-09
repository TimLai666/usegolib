import json
import hashlib
from pathlib import Path


def test_load_artifact_reads_manifest(tmp_path: Path):
    import usegolib

    lib_bytes = b""
    lib_path = tmp_path / "libusegolib.dll"
    lib_path.write_bytes(lib_bytes)
    sha = hashlib.sha256(lib_bytes).hexdigest()

    manifest = {
        "manifest_version": 1,
        "abi_version": 0,
        "module": "example.com/mod",
        "version": "v1.2.3",
        "goos": "windows",
        "goarch": "amd64",
        "packages": ["example.com/mod"],
        "symbols": [],
        "library": {"path": "libusegolib.dll", "sha256": sha},
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    handle = usegolib.load_artifact(tmp_path)
    assert handle.module == "example.com/mod"
    assert handle.version == "v1.2.3"
    assert handle.abi_version == 0


def test_load_artifact_missing_manifest(tmp_path: Path):
    import usegolib

    try:
        usegolib.load_artifact(tmp_path)
    except usegolib.errors.ArtifactNotFoundError as e:
        assert "manifest.json" in str(e)
    else:
        raise AssertionError("expected ArtifactNotFoundError")

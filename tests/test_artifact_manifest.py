import json
import hashlib
from pathlib import Path


def test_load_artifact_reads_manifest(tmp_path: Path):
    import usegolib
    from usegolib.runtime.platform import host_goarch, host_goos

    goos = host_goos()
    goarch = host_goarch()
    ext = ".so"
    if goos == "windows":
        ext = ".dll"
    elif goos == "darwin":
        ext = ".dylib"

    lib_bytes = b""
    lib_path = tmp_path / f"libusegolib{ext}"
    lib_path.write_bytes(lib_bytes)
    sha = hashlib.sha256(lib_bytes).hexdigest()

    manifest = {
        "manifest_version": 1,
        "abi_version": 0,
        "module": "example.com/mod",
        "version": "v1.2.3",
        "goos": goos,
        "goarch": goarch,
        "packages": ["example.com/mod"],
        "symbols": [],
        "library": {"path": lib_path.name, "sha256": sha},
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

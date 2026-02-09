import hashlib
import json
from pathlib import Path

import pytest


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _write_manifest(tmp_path: Path, *, sha: str | None) -> Path:
    lib_bytes = b"not a real shared library"
    lib_path = tmp_path / "libusegolib.so"
    lib_path.write_bytes(lib_bytes)

    manifest = {
        "manifest_version": 1,
        "abi_version": 0,
        "module": "example.com/mod",
        "version": "v0.0.0",
        "goos": "linux",
        "goarch": "amd64",
        "packages": ["example.com/mod"],
        "symbols": [],
        "schema": None,
        "library": {"path": str(lib_path.name)},
    }
    if sha is not None:
        manifest["library"]["sha256"] = sha

    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path


def test_load_artifact_rejects_missing_sha256(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import usegolib.handle
    import usegolib
    import usegolib.errors

    class DummyClient:
        def __init__(self, _path: Path):
            raise AssertionError("SharedLibClient should not be created when sha256 is missing")

    monkeypatch.setattr(usegolib.handle, "SharedLibClient", DummyClient)

    _write_manifest(tmp_path, sha=None)
    with pytest.raises(usegolib.errors.LoadError, match=r"missing library\.sha256"):
        usegolib.load_artifact(tmp_path)


def test_load_artifact_rejects_invalid_sha256_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import usegolib.handle
    import usegolib
    import usegolib.errors

    class DummyClient:
        def __init__(self, _path: Path):
            raise AssertionError("SharedLibClient should not be created when sha256 is invalid")

    monkeypatch.setattr(usegolib.handle, "SharedLibClient", DummyClient)

    # Wrong length and uppercase to ensure format validation.
    _write_manifest(tmp_path, sha="ABC")
    with pytest.raises(usegolib.errors.LoadError, match=r"must be 64 lowercase hex"):
        usegolib.load_artifact(tmp_path)


def test_load_artifact_rejects_mismatched_sha256(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import usegolib.handle
    import usegolib
    import usegolib.errors

    created = {"ok": False}

    class DummyClient:
        def __init__(self, _path: Path):
            created["ok"] = True

    monkeypatch.setattr(usegolib.handle, "SharedLibClient", DummyClient)

    _write_manifest(tmp_path, sha="0" * 64)
    with pytest.raises(usegolib.errors.LoadError, match=r"sha256 mismatch"):
        usegolib.load_artifact(tmp_path)
    assert created["ok"] is False


def test_load_artifact_accepts_correct_sha256(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import usegolib.handle
    import usegolib

    created = {"path": None}

    class DummyClient:
        def __init__(self, path: Path):
            created["path"] = path

    monkeypatch.setattr(usegolib.handle, "SharedLibClient", DummyClient)

    lib_bytes = b"not a real shared library"
    want = _sha256_bytes(lib_bytes)
    leaf = _write_manifest(tmp_path, sha=want)

    # Ensure the file bytes match what we hashed.
    (leaf / "libusegolib.so").write_bytes(lib_bytes)

    h = usegolib.load_artifact(leaf)
    assert h.module == "example.com/mod"
    assert created["path"] is not None

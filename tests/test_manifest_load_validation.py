import hashlib
import json
from pathlib import Path

import pytest


def _ext(goos: str) -> str:
    if goos == "windows":
        return ".dll"
    if goos == "darwin":
        return ".dylib"
    return ".so"


def _write_artifact(
    tmp_path: Path,
    *,
    goos: str,
    goarch: str,
    manifest_version: int = 1,
    abi_version: int = 0,
) -> Path:
    ext = _ext(goos)
    lib_path = tmp_path / f"libusegolib{ext}"
    lib_bytes = b""
    lib_path.write_bytes(lib_bytes)
    sha = hashlib.sha256(lib_bytes).hexdigest()

    manifest = {
        "manifest_version": manifest_version,
        "abi_version": abi_version,
        "module": "example.com/mod",
        "version": "v0.0.0",
        "goos": goos,
        "goarch": goarch,
        "packages": ["example.com/mod"],
        "symbols": [],
        "library": {"path": lib_path.name, "sha256": sha},
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path


def test_load_artifact_rejects_unsupported_manifest_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import usegolib
    import usegolib.handle
    import usegolib.errors
    from usegolib.runtime.platform import host_goarch, host_goos

    class DummyClient:
        def __init__(self, _path: Path):
            raise AssertionError("SharedLibClient should not be created for invalid manifest")

    monkeypatch.setattr(usegolib.handle, "SharedLibClient", DummyClient)

    _write_artifact(tmp_path, goos=host_goos(), goarch=host_goarch(), manifest_version=2)
    with pytest.raises(usegolib.errors.LoadError, match=r"unsupported manifest_version"):
        usegolib.load_artifact(tmp_path)


def test_load_artifact_rejects_unsupported_abi_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import usegolib
    import usegolib.handle
    import usegolib.errors
    from usegolib.runtime.platform import host_goarch, host_goos

    class DummyClient:
        def __init__(self, _path: Path):
            raise AssertionError("SharedLibClient should not be created for invalid manifest")

    monkeypatch.setattr(usegolib.handle, "SharedLibClient", DummyClient)

    _write_artifact(tmp_path, goos=host_goos(), goarch=host_goarch(), abi_version=1)
    with pytest.raises(usegolib.errors.LoadError, match=r"unsupported abi_version"):
        usegolib.load_artifact(tmp_path)


def test_load_artifact_rejects_wrong_platform(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import usegolib
    import usegolib.handle
    import usegolib.errors
    from usegolib.runtime.platform import host_goarch, host_goos

    class DummyClient:
        def __init__(self, _path: Path):
            raise AssertionError("SharedLibClient should not be created for platform mismatch")

    monkeypatch.setattr(usegolib.handle, "SharedLibClient", DummyClient)

    host_os = host_goos()
    wrong_os = "linux" if host_os != "linux" else "windows"
    _write_artifact(tmp_path, goos=wrong_os, goarch=host_goarch())
    with pytest.raises(usegolib.errors.LoadError, match=r"platform mismatch"):
        usegolib.load_artifact(tmp_path)


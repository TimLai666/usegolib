import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _zip_bytes(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_ensure_zig_verifies_sha256(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import usegolib.builder.zig as zig

    # Make deterministic.
    monkeypatch.setattr(zig, "_cache_dir", lambda: tmp_path)
    monkeypatch.setattr(zig, "_pick_latest_stable_version", lambda _index: "0.0.0")
    monkeypatch.setattr(zig, "_zig_target", lambda: "x86_64-linux")

    # Build a minimal "zig" layout with adjacent lib/.
    archive = _zip_bytes(
        {
            "zig/zig": b"bin",
            "zig/zig.exe": b"bin",
            "zig/lib/dummy": b"x",
        }
    )
    good_sha = hashlib.sha256(archive).hexdigest()

    index = {"0.0.0": {"x86_64-linux": {"tarball": "https://ziglang.org/zig.zip", "shasum": good_sha}}}

    def fake_urlopen(url, timeout=0):  # noqa: ARG001
        if url.endswith("index.json"):
            return _Resp(json.dumps(index).encode("utf-8"))
        if url == "https://ziglang.org/zig.zip":
            return _Resp(archive)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(zig.urllib.request, "urlopen", fake_urlopen)

    p = zig.ensure_zig()
    assert p.exists()


def test_ensure_zig_rejects_sha256_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import usegolib.builder.zig as zig

    monkeypatch.setattr(zig, "_cache_dir", lambda: tmp_path)
    monkeypatch.setattr(zig, "_pick_latest_stable_version", lambda _index: "0.0.0")
    monkeypatch.setattr(zig, "_zig_target", lambda: "x86_64-linux")

    archive = _zip_bytes({"zig/zig": b"bin", "zig/lib/dummy": b"x"})
    index = {
        "0.0.0": {
            "x86_64-linux": {"tarball": "https://ziglang.org/zig.zip", "shasum": "0" * 64}
        }
    }

    def fake_urlopen(url, timeout=0):  # noqa: ARG001
        if url.endswith("index.json"):
            return _Resp(json.dumps(index).encode("utf-8"))
        if url == "https://ziglang.org/zig.zip":
            return _Resp(archive)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(zig.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(zig.BuildError, match=r"sha256 mismatch"):
        zig.ensure_zig()


def test_ensure_zig_rejects_unsafe_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import usegolib.builder.zig as zig

    monkeypatch.setattr(zig, "_cache_dir", lambda: tmp_path)
    monkeypatch.setattr(zig, "_pick_latest_stable_version", lambda _index: "0.0.0")
    monkeypatch.setattr(zig, "_zig_target", lambda: "x86_64-linux")

    archive = _zip_bytes(
        {
            "../pwn": b"x",
            "zig/zig": b"bin",
            "zig/lib/dummy": b"x",
        }
    )
    sha = hashlib.sha256(archive).hexdigest()
    index = {"0.0.0": {"x86_64-linux": {"tarball": "https://ziglang.org/zig.zip", "shasum": sha}}}

    def fake_urlopen(url, timeout=0):  # noqa: ARG001
        if url.endswith("index.json"):
            return _Resp(json.dumps(index).encode("utf-8"))
        if url == "https://ziglang.org/zig.zip":
            return _Resp(archive)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(zig.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(zig.BuildError, match=r"unsafe path"):
        zig.ensure_zig()


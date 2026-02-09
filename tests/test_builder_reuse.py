import json
from pathlib import Path


def test_artifact_ready_true_when_manifest_and_lib_exist(tmp_path: Path):
    from usegolib.builder.reuse import artifact_ready

    leaf = tmp_path / "leaf"
    leaf.mkdir()
    (leaf / "libusegolib.dll").write_bytes(b"")
    (leaf / "manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "abi_version": 0,
                "module": "example.com/mod",
                "version": "v1.2.3",
                "goos": "windows",
                "goarch": "amd64",
                "packages": ["example.com/mod"],
                "symbols": [],
                "library": {"path": "libusegolib.dll", "sha256": "00" * 32},
            }
        ),
        encoding="utf-8",
    )
    assert artifact_ready(leaf, expected_input_fingerprint=None) is True


def test_artifact_ready_false_when_manifest_missing(tmp_path: Path):
    from usegolib.builder.reuse import artifact_ready

    leaf = tmp_path / "leaf"
    leaf.mkdir()
    (leaf / "libusegolib.dll").write_bytes(b"")
    assert artifact_ready(leaf, expected_input_fingerprint=None) is False


def test_artifact_ready_false_when_fingerprint_mismatches(tmp_path: Path):
    from usegolib.builder.reuse import artifact_ready

    leaf = tmp_path / "leaf"
    leaf.mkdir()
    (leaf / "libusegolib.dll").write_bytes(b"")
    (leaf / "manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "abi_version": 0,
                "module": "example.com/mod",
                "version": "local",
                "goos": "windows",
                "goarch": "amd64",
                "packages": ["example.com/mod"],
                "symbols": [],
                "input_fingerprint": "abc",
                "library": {"path": "libusegolib.dll", "sha256": "00" * 32},
            }
        ),
        encoding="utf-8",
    )
    assert artifact_ready(leaf, expected_input_fingerprint="def") is False

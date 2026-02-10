from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


def test_go_mod_download_json_tolerates_non_utf8_prefix(monkeypatch):
    from usegolib.builder import resolve as rmod

    payload = b"\x88\x00" + json.dumps(
        {"Path": "example.com/mod", "Version": "v1.2.3", "Dir": "C:/tmp/x"}
    ).encode("utf-8")

    def fake_run(*args, **kwargs):  # noqa: ANN001
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout=payload)

    monkeypatch.setattr(subprocess, "run", fake_run)
    info = rmod._go_mod_download_json("example.com/mod@v1.2.3", env=None)  # noqa: SLF001
    assert info["Path"] == "example.com/mod"
    assert info["Version"] == "v1.2.3"


def test_scan_module_tolerates_non_utf8_prefix(monkeypatch, tmp_path: Path):
    from usegolib.builder.scan import scan_module

    obj = {
        "funcs": [],
        "methods": [],
        "generic_funcs": [],
        "struct_types": {},
        "structs": {},
    }
    payload = b"\x88\x00" + json.dumps(obj).encode("utf-8")

    def fake_run(*args, **kwargs):  # noqa: ANN001
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout=payload)

    monkeypatch.setattr(subprocess, "run", fake_run)

    # module_dir only needs to exist; scan_module calls subprocess.run which we patched.
    mod_dir = tmp_path / "gomod"
    mod_dir.mkdir()

    scan = scan_module(module_dir=mod_dir, env=None)
    assert scan.funcs == []
    assert scan.methods == []


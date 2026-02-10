from __future__ import annotations

import subprocess

import pytest


def test_builder_run_missing_go_raises_build_error(monkeypatch, tmp_path):
    from usegolib.builder import build
    from usegolib.errors import BuildError

    def fake_run(*args, **kwargs):  # noqa: ANN001
        raise FileNotFoundError("go")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(BuildError, match=r"Go toolchain not found"):
        build._run(["go", "version"], cwd=tmp_path)  # noqa: SLF001


def test_resolve_missing_go_raises_build_error(monkeypatch):
    from usegolib.builder import resolve
    from usegolib.errors import BuildError

    def fake_run(*args, **kwargs):  # noqa: ANN001
        raise FileNotFoundError("go")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(BuildError, match=r"Go toolchain not found"):
        resolve._go_mod_download_json("example.com/mod@v1.2.3")  # noqa: SLF001


def test_scan_missing_go_raises_build_error(monkeypatch, tmp_path):
    from usegolib.builder.scan import scan_module
    from usegolib.errors import BuildError

    def fake_run(*args, **kwargs):  # noqa: ANN001
        raise FileNotFoundError("go")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(BuildError, match=r"Go toolchain not found"):
        scan_module(module_dir=tmp_path)


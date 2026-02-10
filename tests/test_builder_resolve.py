from pathlib import Path


def test_resolve_local_module_dir(tmp_path: Path):
    from usegolib.builder.resolve import resolve_module_target

    mod_dir = tmp_path / "gomod"
    mod_dir.mkdir()
    (mod_dir / "go.mod").write_text("module example.com/localmod\n\ngo 1.22\n", encoding="utf-8")
    (mod_dir / "local.go").write_text("package localmod\n", encoding="utf-8")

    r = resolve_module_target(target=str(mod_dir), version=None)
    assert r.module_path == "example.com/localmod"
    assert r.version == "local"
    assert r.module_dir == mod_dir.resolve()


def test_resolve_local_module_subdir(tmp_path: Path):
    from usegolib.builder.resolve import resolve_module_target

    mod_dir = tmp_path / "gomod"
    sub_dir = mod_dir / "subpkg"
    sub_dir.mkdir(parents=True)
    (mod_dir / "go.mod").write_text("module example.com/localmod\n\ngo 1.22\n", encoding="utf-8")
    (mod_dir / "local.go").write_text("package localmod\n", encoding="utf-8")
    (sub_dir / "sub.go").write_text("package subpkg\n", encoding="utf-8")

    r = resolve_module_target(target=str(sub_dir), version=None)
    assert r.module_path == "example.com/localmod"
    assert r.version == "local"
    assert r.module_dir == mod_dir.resolve()


def test_resolve_remote_defaults_to_at_latest(monkeypatch):
    from usegolib.builder import resolve as rmod
    from usegolib.builder.resolve import resolve_module_target

    seen: list[str] = []

    def fake_download(arg: str) -> dict:
        seen.append(arg)
        return {"Path": "example.com/remote", "Version": "v1.2.3", "Dir": "/tmp/x"}

    monkeypatch.setattr(rmod, "_go_mod_download_json", fake_download)
    r = resolve_module_target(target="example.com/remote", version=None)
    assert r.module_path == "example.com/remote"
    assert r.version == "v1.2.3"
    assert seen == ["example.com/remote@latest"]


def test_resolve_remote_subpackage_trims_segments(monkeypatch):
    from usegolib.builder import resolve as rmod
    from usegolib.builder.resolve import resolve_module_target
    from usegolib.errors import BuildError

    calls: list[str] = []

    def fake_download(arg: str) -> dict:
        calls.append(arg)
        if arg.startswith("example.com/mod/subpkg@"):
            raise BuildError("fail")
        return {"Path": "example.com/mod", "Version": "v9.9.9", "Dir": "/tmp/m"}

    monkeypatch.setattr(rmod, "_go_mod_download_json", fake_download)
    r = resolve_module_target(target="example.com/mod/subpkg", version=None)
    assert r.module_path == "example.com/mod"
    assert r.version == "v9.9.9"
    assert calls[0].startswith("example.com/mod/subpkg@")
    assert calls[1].startswith("example.com/mod@")

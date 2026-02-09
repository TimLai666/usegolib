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

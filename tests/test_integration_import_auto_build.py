import os
from pathlib import Path

import pytest


def _write_go_module(mod_dir: Path, *, module_path: str) -> None:
    (mod_dir / "go.mod").write_text(
        "\n".join(
            [
                f"module {module_path}",
                "",
                "go 1.22",
                "",
            ]
        ),
        encoding="utf-8",
    )


@pytest.mark.skipif(
    os.environ.get("USEGOLIB_INTEGRATION") != "1",
    reason="set USEGOLIB_INTEGRATION=1 to run integration tests",
)
def test_import_auto_build_default_artifact_root(tmp_path: Path, monkeypatch):
    import usegolib

    mod_dir = tmp_path / "gomod"
    mod_dir.mkdir()
    _write_go_module(mod_dir, module_path="example.com/testauto")
    (mod_dir / "m.go").write_text(
        "\n".join(
            [
                "package testauto",
                "",
                "func AddInt(a int64, b int64) int64 {",
                "    return a + b",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    artifact_root = tmp_path / "artifacts"
    monkeypatch.setenv("USEGOLIB_ARTIFACT_DIR", str(artifact_root))

    h = usegolib.import_(str(mod_dir))
    assert h.package == "example.com/testauto"
    assert h.AddInt(1, 2) == 3


@pytest.mark.skipif(
    os.environ.get("USEGOLIB_INTEGRATION") != "1",
    reason="set USEGOLIB_INTEGRATION=1 to run integration tests",
)
def test_import_local_subpackage_dir_maps_package_path(tmp_path: Path, monkeypatch):
    import usegolib

    mod_dir = tmp_path / "gomodsub"
    sub_dir = mod_dir / "subpkg"
    sub_dir.mkdir(parents=True)

    _write_go_module(mod_dir, module_path="example.com/testautosub")
    (sub_dir / "s.go").write_text(
        "\n".join(
            [
                "package subpkg",
                "",
                "func AddInt(a int64, b int64) int64 {",
                "    return a + b",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    artifact_root = tmp_path / "artifacts"
    monkeypatch.setenv("USEGOLIB_ARTIFACT_DIR", str(artifact_root))

    h = usegolib.import_(str(sub_dir))
    assert h.package == "example.com/testautosub/subpkg"
    assert h.AddInt(10, 20) == 30

    # After building, importing by Go package path should work against the artifact root.
    h2 = usegolib.import_("example.com/testautosub/subpkg", artifact_dir=artifact_root)
    assert h2.AddInt(5, 6) == 11


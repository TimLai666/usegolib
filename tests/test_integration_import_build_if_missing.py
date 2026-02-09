import os
from pathlib import Path

import pytest


def _write_go_test_module(mod_dir: Path) -> None:
    (mod_dir / "go.mod").write_text(
        "\n".join(
            [
                "module example.com/testmoddev",
                "",
                "go 1.22",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (mod_dir / "testmoddev.go").write_text(
        "\n".join(
            [
                "package testmoddev",
                "",
                "func AddInt(a int64, b int64) int64 {",
                "    return a + b",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


@pytest.mark.skipif(
    os.environ.get("USEGOLIB_INTEGRATION") != "1",
    reason="set USEGOLIB_INTEGRATION=1 to run integration tests",
)
def test_import_build_if_missing_builds_then_calls(tmp_path: Path):
    import usegolib

    mod_dir = tmp_path / "gomod"
    mod_dir.mkdir()
    _write_go_test_module(mod_dir)

    out_root = tmp_path / "out"
    # First import should trigger build into out_root.
    h = usegolib.import_(str(mod_dir), artifact_dir=out_root, build_if_missing=True)
    assert h.AddInt(1, 2) == 3

    # Second import should reuse existing artifact (no rebuild); just sanity call.
    h2 = usegolib.import_(str(mod_dir), artifact_dir=out_root, build_if_missing=True)
    assert h2.AddInt(2, 3) == 5


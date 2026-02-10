import os
import subprocess
import sys
from pathlib import Path

import pytest


def _write_go_test_module(mod_dir: Path) -> None:
    (mod_dir / "go.mod").write_text(
        "\n".join(
            [
                "module example.com/retmod",
                "",
                "go 1.22",
                "",
            ]
        ),
        encoding="utf-8",
    )
    pkg = mod_dir / "p"
    pkg.mkdir()
    (pkg / "p.go").write_text(
        "\n".join(
            [
                "package p",
                "",
                "import \"fmt\"",
                "",
                "func Pair() (int64, string) {",
                "    return 7, \"ok\"",
                "}",
                "",
                "func Trio(ok bool) (int64, int64, error) {",
                "    if !ok {",
                "        return 0, 0, fmt.Errorf(\"no\")",
                "    }",
                "    return 1, 2, nil",
                "}",
                "",
                "type Box struct{}",
                "",
                "func (b *Box) Pair() (int64, string) {",
                "    return 8, \"box\"",
                "}",
                "",
                "func (b *Box) DuoErr(ok bool) (int64, string, error) {",
                "    if !ok {",
                "        return 0, \"\", fmt.Errorf(\"bad\")",
                "    }",
                "    return 9, \"yes\", nil",
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
def test_integration_multi_return_values(tmp_path: Path):
    import usegolib
    from usegolib.errors import GoError

    mod_dir = tmp_path / "gomod"
    mod_dir.mkdir()
    _write_go_test_module(mod_dir)

    out_dir = tmp_path / "artifact"
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "usegolib",
            "build",
            "--module",
            str(mod_dir),
            "--out",
            str(out_dir),
        ]
    )

    h = usegolib.import_("example.com/retmod/p", artifact_dir=out_dir)

    a, b = h.Pair()
    assert (a, b) == (7, "ok")

    x, y = h.Trio(True)
    assert (x, y) == (1, 2)

    with pytest.raises(GoError, match="no"):
        _ = h.Trio(False)

    box = h.object("Box")
    try:
        a2, b2 = box.Pair()
        assert (a2, b2) == (8, "box")

        c, d = box.DuoErr(True)
        assert (c, d) == (9, "yes")

        with pytest.raises(GoError, match="bad"):
            _ = box.DuoErr(False)
    finally:
        box.close()


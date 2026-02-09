import os
import subprocess
import sys
from pathlib import Path

import pytest


def _write_go_test_module(mod_dir: Path) -> None:
    (mod_dir / "go.mod").write_text(
        "\n".join(
            [
                "module example.com/testmod",
                "",
                "go 1.22",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (mod_dir / "testmod.go").write_text(
        "\n".join(
            [
                "package testmod",
                "",
                'import "errors"',
                "",
                "func AddInt(a int64, b int64) int64 {",
                "    return a + b",
                "}",
                "",
                "func EchoBytes(b []byte) []byte {",
                "    return b",
                "}",
                "",
                "func SumFloats(xs []float64) float64 {",
                "    var s float64",
                "    for _, x := range xs {",
                "        s += x",
                "    }",
                "    return s",
                "}",
                "",
                "func Fail(msg string) (string, error) {",
                "    return \"\", errors.New(msg)",
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
def test_build_and_call(tmp_path: Path):
    import usegolib

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

    h = usegolib.load_artifact(out_dir)
    assert h.AddInt(1, 2) == 3
    assert h.EchoBytes(b"abc") == b"abc"
    assert h.SumFloats([1.25, 2.5]) == pytest.approx(3.75)

    with pytest.raises(usegolib.errors.GoError):
        h.Fail("boom")

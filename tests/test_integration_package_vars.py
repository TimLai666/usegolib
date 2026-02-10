import os
import subprocess
import sys
from pathlib import Path

import pytest


def _write_go_test_module(mod_dir: Path) -> None:
    (mod_dir / "go.mod").write_text(
        "\n".join(
            [
                "module example.com/nsmod",
                "",
                "go 1.22",
                "",
            ]
        ),
        encoding="utf-8",
    )
    pkg = mod_dir / "isr"
    pkg.mkdir()
    (pkg / "isr.go").write_text(
        "\n".join(
            [
                "package isr",
                "",
                "// Use `DL.Of` to create a new list.",
                "var DL = dl{}",
                "",
                "type dl struct {",
                "    items []any",
                "}",
                "",
                "func (d dl) Of(items ...any) *dl {",
                "    x := dl{items: items}",
                "    return &x",
                "}",
                "",
                "func (l *dl) Push(items ...any) *dl {",
                "    l.items = append(l.items, items...)",
                "    return l",
                "}",
                "",
                "func (l *dl) Len() int64 {",
                "    return int64(len(l.items))",
                "}",
                "",
                "func (l *dl) At(i int64) any {",
                "    return l.items[i]",
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
def test_exported_package_var_namespace_methods(tmp_path: Path):
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

    h = usegolib.import_("example.com/nsmod/isr", artifact_dir=out_dir)

    # Exported var resolves to an object handle.
    ns = h.DL
    assert ns.type_name == "dl"

    dl = h.DL.Of(1, 2, 3)
    assert dl.type_name == "dl"
    assert dl.Len() == 3
    assert dl.At(0) == 1

    dl2 = dl.Push(4, 5)
    assert dl2.type_name == "dl"
    assert dl2.Len() == 5

    ns.close()
    dl.close()
    dl2.close()


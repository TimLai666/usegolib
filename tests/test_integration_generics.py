import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _write_go_test_module(mod_dir: Path) -> None:
    (mod_dir / "go.mod").write_text(
        "\n".join(
            [
                "module example.com/genericmod",
                "",
                "go 1.22",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (mod_dir / "genericmod.go").write_text(
        "\n".join(
            [
                "package genericmod",
                "",
                "type Person struct {",
                "    Name string `json:\"name\"`",
                "}",
                "",
                "func Id[T any](x T) T {",
                "    return x",
                "}",
                "",
                "func Wrap[T any](x T) map[string]T {",
                "    return map[string]T{\"x\": x}",
                "}",
                "",
                "func Pair[T any](a, b T) []T {",
                "    return []T{a, b}",
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
def test_build_and_call_generics(tmp_path: Path):
    import usegolib

    mod_dir = tmp_path / "gomod"
    mod_dir.mkdir()
    _write_go_test_module(mod_dir)

    generics_cfg = tmp_path / "generics.json"
    generics_cfg.write_text(
        json.dumps(
            {
                "instantiations": [
                    {"pkg": "example.com/genericmod", "name": "Id", "type_args": ["int64"]},
                    {"pkg": "example.com/genericmod", "name": "Id", "type_args": ["string"]},
                    {"pkg": "example.com/genericmod", "name": "Id", "type_args": ["Person"]},
                    {"pkg": "example.com/genericmod", "name": "Wrap", "type_args": ["int64"]},
                    {"pkg": "example.com/genericmod", "name": "Pair", "type_args": ["int64"]},
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

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
            "--generics",
            str(generics_cfg),
        ]
    )

    h = usegolib.import_("example.com/genericmod", artifact_dir=out_dir)

    assert h.Id__int64(1) == 1
    assert h.Id__string("x") == "x"
    assert h.Id__Person({"name": "bob"}) == {"name": "bob"}
    assert h.Wrap__int64(5) == {"x": 5}
    assert h.Pair__int64(1, 2) == [1, 2]

    assert h.generic("Id", ["int64"])(2) == 2

    th = h.typed()
    types = th.types

    p = types.Person(Name="alice")
    assert th.generic("Id", ["Person"])(p) == p


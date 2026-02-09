import os
import subprocess
import sys
from pathlib import Path

import pytest


def _write_go_test_module(mod_dir: Path) -> None:
    (mod_dir / "go.mod").write_text(
        "\n".join(
            [
                "module example.com/testmodschema",
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
                "package testmodschema",
                "",
                "type Person struct {",
                "    Name string",
                "    Age int64",
                "}",
                "",
                "func IsAdult(p Person) bool {",
                "    return p.Age >= 18",
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
def test_schema_validation_rejects_bad_field_type(tmp_path: Path):
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

    # Manifest schema should include Person fields.
    manifests = list(out_dir.rglob("manifest.json"))
    assert manifests, "expected manifest.json to be emitted"
    manifest_obj = manifests[0].read_text(encoding="utf-8")
    assert '"schema"' in manifest_obj
    assert '"Person"' in manifest_obj
    assert '"Age"' in manifest_obj

    h = usegolib.import_("example.com/testmodschema", artifact_dir=out_dir)
    # Age must be int64; schema validation should catch this before calling Go.
    with pytest.raises(usegolib.errors.UnsupportedTypeError, match=r"schema:"):
        h.IsAdult({"Name": "x", "Age": "not-an-int"})

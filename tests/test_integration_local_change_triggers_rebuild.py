import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _write_go_test_module(mod_dir: Path, *, body: str) -> None:
    (mod_dir / "go.mod").write_text(
        "\n".join(
            [
                "module example.com/testmodfp",
                "",
                "go 1.22",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (mod_dir / "testmodfp.go").write_text(body, encoding="utf-8")


def _read_fingerprint(manifest_dir: Path) -> str:
    obj = json.loads((manifest_dir / "manifest.json").read_text(encoding="utf-8"))
    return str(obj.get("input_fingerprint", ""))


@pytest.mark.skipif(
    os.environ.get("USEGOLIB_INTEGRATION") != "1",
    reason="set USEGOLIB_INTEGRATION=1 to run integration tests",
)
def test_local_source_change_triggers_rebuild(tmp_path: Path):
    mod_dir = tmp_path / "gomod"
    mod_dir.mkdir()

    _write_go_test_module(
        mod_dir,
        body="\n".join(
            [
                "package testmodfp",
                "",
                "func AddInt(a int64, b int64) int64 {",
                "    return a + b",
                "}",
                "",
            ]
        ),
    )

    out_root = tmp_path / "out"
    subprocess.check_call(
        [sys.executable, "-m", "usegolib", "build", "--module", str(mod_dir), "--out", str(out_root)]
    )

    # Find the leaf manifest dir.
    manifest_dirs = list(out_root.rglob("manifest.json"))
    assert len(manifest_dirs) == 1
    leaf = manifest_dirs[0].parent
    fp1 = _read_fingerprint(leaf)
    assert fp1

    # Change local source and rebuild; fingerprint should change.
    _write_go_test_module(
        mod_dir,
        body="\n".join(
            [
                "package testmodfp",
                "",
                "func AddInt(a int64, b int64) int64 {",
                "    return a + b + 1",
                "}",
                "",
            ]
        ),
    )

    subprocess.check_call(
        [sys.executable, "-m", "usegolib", "build", "--module", str(mod_dir), "--out", str(out_root)]
    )
    fp2 = _read_fingerprint(leaf)
    assert fp2
    assert fp2 != fp1


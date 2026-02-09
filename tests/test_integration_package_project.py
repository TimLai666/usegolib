import os
import subprocess
import sys
from pathlib import Path

import pytest
import shutil


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
                "func AddInt(a int64, b int64) int64 {",
                "    return a + b",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"

def _create_venv(venv_dir: Path) -> None:
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
        return
    except subprocess.CalledProcessError:
        # Some minimal Linux installs (including some WSL images) do not ship
        # ensurepip/python3-venv, making `python -m venv` unusable.
        if os.name == "nt":
            raise
        if shutil.which("uv") is None:
            pytest.skip("python -m venv failed and `uv` is not available on PATH")
        # `python -m venv` may have created the directory before failing. `uv venv -c`
        # will replace it. `--seed` ensures `pip` exists for subsequent installs.
        subprocess.check_call(["uv", "venv", "-c", "--seed", str(venv_dir)])


@pytest.mark.skipif(
    os.environ.get("USEGOLIB_INTEGRATION") != "1",
    reason="set USEGOLIB_INTEGRATION=1 to run integration tests",
)
def test_package_generates_installable_project(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]

    mod_dir = tmp_path / "gomod"
    mod_dir.mkdir()
    _write_go_test_module(mod_dir)

    out_root = tmp_path / "out"
    pkg_name = "mypkg"

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "usegolib",
            "package",
            "--module",
            str(mod_dir),
            "--python-package-name",
            pkg_name,
            "--out",
            str(out_root),
        ]
    )

    proj_dir = out_root / pkg_name
    assert (proj_dir / "pyproject.toml").exists()

    venv_dir = tmp_path / "venv"
    _create_venv(venv_dir)
    vpy = _venv_python(venv_dir)

    # Install usegolib (this repo) and then the generated package.
    subprocess.check_call([str(vpy), "-m", "pip", "install", "-e", str(repo_root)])
    subprocess.check_call([str(vpy), "-m", "pip", "install", "-e", str(proj_dir)])

    out = subprocess.check_output(
        [str(vpy), "-c", f"import {pkg_name}; print({pkg_name}.AddInt(1, 2))"],
        text=True,
    ).strip()
    assert out == "3"

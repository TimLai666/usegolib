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


def _runtime_env_without_go(base_env: dict[str, str]) -> dict[str, str]:
    env = dict(base_env)
    path = env.get("PATH", "")

    # Keep a minimal PATH for system basics; do not rely on `go` being present.
    if os.name == "nt":
        sysroot = env.get("SystemRoot", r"C:\Windows")
        minimal = [str(Path(sysroot) / "System32"), sysroot]
        env["PATH"] = os.pathsep.join(minimal)
    else:
        env["PATH"] = "/usr/bin:/bin"

    # Also prevent Go toolchain selection via env (belt and suspenders).
    env.pop("GOTOOLCHAIN", None)
    env.pop("GOROOT", None)
    env.pop("GOPATH", None)

    # Keep value for debugging if needed.
    env["USEGOLIB_ORIG_PATH_LEN"] = str(len(path))
    return env


@pytest.mark.skipif(
    os.environ.get("USEGOLIB_INTEGRATION") != "1",
    reason="set USEGOLIB_INTEGRATION=1 to run integration tests",
)
def test_generated_wheel_installs_and_runs_without_go_on_path(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]

    mod_dir = tmp_path / "gomod"
    mod_dir.mkdir()
    _write_go_test_module(mod_dir)

    out_root = tmp_path / "out"
    pkg_name = "mypkgwheel"

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
    dist_dir = proj_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    build_venv = tmp_path / "venv_build"
    subprocess.check_call([sys.executable, "-m", "venv", str(build_venv)])
    bpy = _venv_python(build_venv)

    # Build environment: install usegolib + build wheel for generated project.
    subprocess.check_call([str(bpy), "-m", "pip", "install", "-e", str(repo_root)])
    # Build only this wheel. Dependencies (usegolib) are installed separately in the runtime venv.
    subprocess.check_call(
        [str(bpy), "-m", "pip", "wheel", "--no-deps", ".", "-w", str(dist_dir)],
        cwd=str(proj_dir),
    )

    wheels = sorted(dist_dir.glob("*.whl"))
    assert wheels, "expected wheel to be built"
    wheel_path = wheels[0]

    run_venv = tmp_path / "venv_run"
    subprocess.check_call([sys.executable, "-m", "venv", str(run_venv)])
    rpy = _venv_python(run_venv)

    # Runtime environment: install usegolib runtime + install wheel.
    subprocess.check_call([str(rpy), "-m", "pip", "install", "-e", str(repo_root)])
    subprocess.check_call([str(rpy), "-m", "pip", "install", str(wheel_path)])

    env = _runtime_env_without_go(os.environ)
    out = subprocess.check_output(
        [str(rpy), "-c", f"import {pkg_name}; print({pkg_name}.AddInt(1, 2))"],
        env=env,
        text=True,
    ).strip()
    assert out == "3"

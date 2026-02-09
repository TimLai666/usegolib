from __future__ import annotations

import shutil
from pathlib import Path


def generate_project(
    *,
    python_package_name: str,
    module: str,
    artifact_root: Path,
    out_dir: Path,
) -> Path:
    """Generate a Python package project embedding a usegolib artifact root.

    Parameters
    ----------
    python_package_name:
        Name of the generated Python package (and project folder).
    module:
        Go module/package path to bind in the generated package's __init__.py.
    artifact_root:
        Root directory containing one or more artifacts (manifest.json + libs).
    out_dir:
        Output directory to place the generated project folder.
    """
    out_dir = Path(out_dir)
    artifact_root = Path(artifact_root)

    proj_dir = out_dir / python_package_name
    src_pkg_dir = proj_dir / "src" / python_package_name
    embedded_root = src_pkg_dir / "_usegolib_artifacts"

    proj_dir.mkdir(parents=True, exist_ok=False)
    src_pkg_dir.mkdir(parents=True, exist_ok=True)

    (proj_dir / "pyproject.toml").write_text(
        _pyproject_toml(python_package_name),
        encoding="utf-8",
    )

    (src_pkg_dir / "__init__.py").write_text(
        _init_py(module),
        encoding="utf-8",
    )

    # Copy artifacts verbatim preserving layout under the embedded root.
    shutil.copytree(artifact_root, embedded_root)
    return proj_dir


def _pyproject_toml(python_package_name: str) -> str:
    return "\n".join(
        [
            "[build-system]",
            'requires = ["setuptools>=69", "wheel"]',
            'build-backend = "setuptools.build_meta"',
            "",
            "[project]",
            f'name = "{python_package_name}"',
            'version = "0.0.0"',
            f'description = "Generated package embedding Go artifacts for {python_package_name}."',
            'requires-python = ">=3.10"',
            'dependencies = ["usegolib>=0.0.0"]',
            "",
            "[tool.setuptools]",
            'package-dir = {"" = "src"}',
            "",
            "[tool.setuptools.packages.find]",
            'where = ["src"]',
            "",
            "[tool.setuptools.package-data]",
            f'"{python_package_name}" = ["_usegolib_artifacts/**"]',
            "",
        ]
    )


def _init_py(module: str) -> str:
    # Lazy import so tools can import the package even if the artifact cannot load.
    return "\n".join(
        [
            '"""Generated package that forwards calls to an embedded Go artifact."""',
            "",
            "from __future__ import annotations",
            "",
            "from pathlib import Path",
            "from typing import Any",
            "",
            "import usegolib",
            "",
            f"_USEGOLIB_MODULE = {module!r}",
            "_HANDLE = None",
            "",
            "",
            "def _get_handle():",
            "    global _HANDLE",
            "    if _HANDLE is None:",
            "        artifact_root = Path(__file__).resolve().parent / '_usegolib_artifacts'",
            "        _HANDLE = usegolib.import_(_USEGOLIB_MODULE, artifact_dir=artifact_root)",
            "    return _HANDLE",
            "",
            "",
            "def __getattr__(name: str) -> Any:",
            "    return getattr(_get_handle(), name)",
            "",
        ]
    )


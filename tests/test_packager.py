import json
from pathlib import Path


def _write_fake_artifact_root(root: Path) -> tuple[str, str, str]:
    module = "example.com/mod"
    version = "v1.2.3"
    plat = "windows-amd64"
    leaf = root / "example.com" / f"mod@{version}" / plat
    leaf.mkdir(parents=True, exist_ok=True)
    lib_name = "libusegolib.dll"
    (leaf / lib_name).write_bytes(b"")
    manifest = {
        "manifest_version": 1,
        "abi_version": 0,
        "module": module,
        "version": version,
        "goos": "windows",
        "goarch": "amd64",
        "packages": [module],
        "symbols": [],
        "library": {"path": lib_name, "sha256": "00" * 32},
    }
    (leaf / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return module, version, plat


def test_packager_generates_project_with_embedded_artifacts(tmp_path: Path):
    artifact_root = tmp_path / "artifacts"
    module, version, plat = _write_fake_artifact_root(artifact_root)

    out = tmp_path / "out"
    from usegolib.packager.generate import generate_project

    generate_project(
        python_package_name="mypkg",
        module=module,
        artifact_root=artifact_root,
        out_dir=out,
    )

    proj = out / "mypkg"
    assert (proj / "pyproject.toml").exists()
    assert (proj / "src" / "mypkg" / "__init__.py").exists()

    embedded_leaf = (
        proj
        / "src"
        / "mypkg"
        / "_usegolib_artifacts"
        / "example.com"
        / f"mod@{version}"
        / plat
    )
    assert (embedded_leaf / "manifest.json").exists()
    assert (embedded_leaf / "libusegolib.dll").exists()


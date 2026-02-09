from __future__ import annotations

import json
import os
import platform
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from ..errors import BuildError


def _cache_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return Path(base) / "usegolib" / "toolchains"
    return Path(os.path.expanduser("~/.cache/usegolib/toolchains"))


def ensure_zig() -> Path:
    env_path = os.environ.get("USEGOLIB_ZIG") or os.environ.get("ZIG")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    found = shutil.which("zig")
    if found:
        return Path(found)

    cache = _cache_dir()
    cache.mkdir(parents=True, exist_ok=True)

    # Select "latest" stable from zig's index.json at runtime.
    index_url = "https://ziglang.org/download/index.json"
    try:
        with urllib.request.urlopen(index_url, timeout=30) as r:  # noqa: S310
            index = json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        raise BuildError(f"failed to fetch Zig download index: {e}") from e

    version = _pick_latest_stable_version(index)
    target = _zig_target()
    try:
        entry = index[version][target]
        url = entry["tarball"]
    except Exception as e:  # noqa: BLE001
        raise BuildError(f"Zig index missing entry for {version}/{target}: {e}") from e

    dest_dir = cache / "zig" / version / target
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Zig expects its lib/ directory relative to the binary. Do not move the
    # executable out of the extracted folder.
    zig_name = "zig.exe" if os.name == "nt" else "zig"
    for p in dest_dir.rglob(zig_name):
        if p.is_file():
            # Zig needs its adjacent lib/ directory.
            if (p.parent / "lib").is_dir():
                return p

    _download_and_extract(url, dest_dir)

    for p in dest_dir.rglob(zig_name):
        if p.is_file():
            if (p.parent / "lib").is_dir():
                return p

    raise BuildError("failed to locate zig binary after extraction")


def _pick_latest_stable_version(index: dict) -> str:
    # Heuristic: keys are versions + "master". Pick highest semver-like key.
    versions: list[tuple[int, int, int, str]] = []
    for k in index.keys():
        if k == "master":
            continue
        parts = k.split(".")
        if len(parts) != 3:
            continue
        try:
            major, minor, patch = (int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            continue
        versions.append((major, minor, patch, k))
    if not versions:
        raise BuildError("no stable Zig versions found in index")
    versions.sort()
    return versions[-1][3]


def _zig_target() -> str:
    machine = platform.machine().lower()
    if machine in {"amd64", "x86_64"}:
        arch = "x86_64"
    elif machine in {"arm64", "aarch64"}:
        arch = "aarch64"
    else:
        raise BuildError(f"unsupported machine architecture: {platform.machine()}")

    sys_platform = platform.system().lower()
    if "windows" in sys_platform:
        osname = "windows"
    elif "darwin" in sys_platform or "mac" in sys_platform:
        osname = "macos"
    elif "linux" in sys_platform:
        osname = "linux"
    else:
        raise BuildError(f"unsupported OS: {platform.system()}")
    return f"{arch}-{osname}"


def _download_and_extract(url: str, dest_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="usegolib-zig-") as td:
        td_path = Path(td)
        archive = td_path / "zig_archive"
        try:
            with urllib.request.urlopen(url, timeout=120) as r:  # noqa: S310
                archive.write_bytes(r.read())
        except Exception as e:  # noqa: BLE001
            raise BuildError(f"failed to download Zig: {e}") from e

        # Best-effort detection.
        if url.endswith(".zip"):
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(dest_dir)  # noqa: S202
        else:
            # tar.xz / tar.gz
            with tarfile.open(archive) as tf:
                tf.extractall(dest_dir)  # noqa: S202

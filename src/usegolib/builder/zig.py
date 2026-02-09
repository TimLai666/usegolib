from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import tarfile
import tempfile
import urllib.request
import urllib.parse
import zipfile
from pathlib import Path

from ..errors import BuildError


_ZIG_ALLOWED_HOSTS = {"ziglang.org"}


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
    _validate_download_url(index_url)
    try:
        with urllib.request.urlopen(index_url, timeout=30) as r:  # noqa: S310
            index = json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        raise BuildError(f"failed to fetch Zig download index: {e}") from e

    pinned_version = os.environ.get("USEGOLIB_ZIG_VERSION")
    if pinned_version:
        version = pinned_version.strip()
        if version.startswith("v"):
            version = version[1:]
        if version not in index:
            raise BuildError(f"Zig index missing version: {version}")
    else:
        version = _pick_latest_stable_version(index)
    target = _zig_target()
    try:
        entry = index[version][target]
        url = entry["tarball"]
        sha256 = entry.get("shasum") or entry.get("sha256")
    except Exception as e:  # noqa: BLE001
        raise BuildError(f"Zig index missing entry for {version}/{target}: {e}") from e

    _validate_download_url(url)
    if not isinstance(sha256, str) or len(sha256.strip()) != 64:
        raise BuildError(f"Zig index missing sha256 digest for {version}/{target}")
    sha256 = sha256.strip().lower()

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

    _download_and_extract(url, dest_dir, expected_sha256=sha256)

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


def _download_and_extract(url: str, dest_dir: Path, *, expected_sha256: str | None) -> None:
    with tempfile.TemporaryDirectory(prefix="usegolib-zig-") as td:
        td_path = Path(td)
        archive = td_path / "zig_archive"
        try:
            with urllib.request.urlopen(url, timeout=120) as r:  # noqa: S310
                archive.write_bytes(r.read())
        except Exception as e:  # noqa: BLE001
            raise BuildError(f"failed to download Zig: {e}") from e

        got = _sha256_file(archive)
        if expected_sha256 is not None and got != expected_sha256:
            raise BuildError(
                f"Zig archive sha256 mismatch: expected {expected_sha256}, got {got}"
            )

        # Best-effort detection.
        if url.endswith(".zip"):
            with zipfile.ZipFile(archive) as zf:
                _extract_zip_safe(zf, dest_dir)
        else:
            # tar.xz / tar.gz
            with tarfile.open(archive) as tf:
                _extract_tar_safe(tf, dest_dir)


def _validate_download_url(url: str) -> None:
    try:
        u = urllib.parse.urlparse(url)
    except Exception as e:  # noqa: BLE001
        raise BuildError(f"invalid Zig download URL: {e}") from e
    if u.scheme != "https":
        raise BuildError(f"Zig download URL must use https: {url}")
    if not u.netloc or u.netloc not in _ZIG_ALLOWED_HOSTS:
        raise BuildError(f"Zig download host not allowed: {url}")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_safe_path(dest_dir: Path, member_path: str) -> bool:
    # Reject absolute paths and path traversal.
    if not member_path or member_path.startswith(("/", "\\")):
        return False
    # Normalize separators.
    p = Path(member_path)
    if any(part == ".." for part in p.parts):
        return False
    try:
        resolved = (dest_dir / p).resolve()
        base = dest_dir.resolve()
    except Exception:
        return False
    try:
        resolved.relative_to(base)
        return True
    except Exception:
        return False


def _extract_zip_safe(zf: zipfile.ZipFile, dest_dir: Path) -> None:
    dest_dir = Path(dest_dir)
    for name in zf.namelist():
        if not _is_safe_path(dest_dir, name):
            raise BuildError(f"unsafe path in zip archive: {name}")
    zf.extractall(dest_dir)  # noqa: S202 - validated above


def _extract_tar_safe(tf: tarfile.TarFile, dest_dir: Path) -> None:
    dest_dir = Path(dest_dir)
    for m in tf.getmembers():
        if not _is_safe_path(dest_dir, m.name):
            raise BuildError(f"unsafe path in tar archive: {m.name}")
    tf.extractall(dest_dir)  # noqa: S202 - validated above

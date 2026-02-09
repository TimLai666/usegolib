from __future__ import annotations

import os
import platform
import sys

from ..errors import UseGoLibError


def host_goos() -> str:
    override = os.environ.get("USEGOLIB_GOOS")
    if override:
        return override

    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform.startswith("linux"):
        return "linux"
    raise UseGoLibError(f"unsupported platform: {sys.platform}")


def host_goarch() -> str:
    override = os.environ.get("USEGOLIB_GOARCH")
    if override:
        return override

    m = platform.machine().lower()
    if m in {"amd64", "x86_64"}:
        return "amd64"
    if m in {"arm64", "aarch64"}:
        return "arm64"
    raise UseGoLibError(f"unsupported machine architecture: {platform.machine()}")


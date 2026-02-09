from __future__ import annotations

import os
from pathlib import Path


def default_artifact_root() -> Path:
    """Return the default artifact root directory.

    Override with `USEGOLIB_ARTIFACT_DIR`.
    """
    override = os.environ.get("USEGOLIB_ARTIFACT_DIR")
    if override:
        return Path(override)

    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return Path(base) / "usegolib" / "artifacts"
    return Path(os.path.expanduser("~/.cache/usegolib/artifacts"))


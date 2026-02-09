from __future__ import annotations

from pathlib import Path

from ..artifact import read_manifest


def artifact_ready(leaf_dir: Path) -> bool:
    """Return True if the artifact leaf directory appears complete enough to reuse."""
    leaf_dir = Path(leaf_dir)
    try:
        manifest = read_manifest(leaf_dir)
    except Exception:
        return False

    return manifest.library_path.exists()


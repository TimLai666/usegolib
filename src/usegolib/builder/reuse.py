from __future__ import annotations

from pathlib import Path

import json

from ..artifact import read_manifest


def artifact_ready(leaf_dir: Path, *, expected_input_fingerprint: str | None) -> bool:
    """Return True if the artifact leaf directory appears complete enough to reuse."""
    leaf_dir = Path(leaf_dir)
    try:
        manifest = read_manifest(leaf_dir)
    except Exception:
        return False

    if not manifest.library_path.exists():
        return False

    if expected_input_fingerprint is None:
        return True

    # Read raw json for optional fields.
    try:
        obj = json.loads((leaf_dir / "manifest.json").read_text(encoding="utf-8"))
    except Exception:
        return False

    return str(obj.get("input_fingerprint", "")) == expected_input_fingerprint

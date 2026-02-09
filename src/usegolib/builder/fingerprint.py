from __future__ import annotations

import hashlib
from pathlib import Path


def fingerprint_local_module_dir(module_dir: Path) -> str:
    """Compute a content fingerprint for local module directory builds.

    Includes:
    - go.mod, go.sum (if present)
    - all *.go files under the module directory (excluding vendor/)
    """
    module_dir = Path(module_dir).resolve()
    h = hashlib.sha256()

    def add_file(p: Path) -> None:
        rel = p.relative_to(module_dir).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(b"\x00")
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        h.update(b"\x00")

    go_mod = module_dir / "go.mod"
    if go_mod.exists():
        add_file(go_mod)

    go_sum = module_dir / "go.sum"
    if go_sum.exists():
        add_file(go_sum)

    files = sorted(
        [
            p
            for p in module_dir.rglob("*.go")
            if "vendor" not in p.parts and ".git" not in p.parts
        ],
        key=lambda p: p.as_posix(),
    )
    for p in files:
        add_file(p)

    return h.hexdigest()


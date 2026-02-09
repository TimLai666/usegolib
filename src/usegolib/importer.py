"""Public import API for Go modules (v0)."""

from __future__ import annotations

from pathlib import Path

from .errors import ArtifactNotFoundError


def import_(
    module: str,
    version: str | None = None,
    *,
    artifact_dir: str | Path | None = None,
    build_if_missing: bool = False,
):
    """Import a Go module by loading a prebuilt artifact.

    For v0, this function requires a prebuilt artifact to exist on disk unless
    `build_if_missing=True` is used (builder is implemented in later milestones).
    """
    from .artifact import resolve_manifest
    from .handle import PackageHandle

    if artifact_dir is None:
        raise ArtifactNotFoundError("artifact_dir is required in v0 runtime mode")

    if build_if_missing:
        raise NotImplementedError("build_if_missing is not supported yet")

    manifest = resolve_manifest(Path(artifact_dir), package=module, version=version)
    return PackageHandle.from_manifest(manifest, package=module)

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

    By default, this function requires a prebuilt artifact to exist on disk.
    In development workflows, `build_if_missing=True` can be used to build into
    `artifact_dir` and then import the newly built artifact.
    """
    from .artifact import resolve_manifest
    from .handle import PackageHandle

    if artifact_dir is None:
        raise ArtifactNotFoundError("artifact_dir is required in v0 runtime mode")

    # Convenience for dev: allow passing a local module directory path.
    # When `module` is a directory, resolve its module path and import that.
    runtime_pkg = module
    build_target = module
    if Path(module).is_dir():
        from .builder.resolve import resolve_module_target

        resolved = resolve_module_target(target=module, version=version)
        runtime_pkg = resolved.module_path

    artifact_root = Path(artifact_dir)
    try:
        manifest = resolve_manifest(artifact_root, package=runtime_pkg, version=version)
    except ArtifactNotFoundError:
        if not build_if_missing:
            raise
        from .builder.build import build_artifact

        # Dev mode: build into the provided artifact root and retry resolution.
        build_artifact(module=build_target, out_dir=artifact_root, version=version)
        manifest = resolve_manifest(artifact_root, package=runtime_pkg, version=version)

    return PackageHandle.from_manifest(manifest, package=runtime_pkg)

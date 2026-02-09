"""Public import API for Go modules (v0)."""

from __future__ import annotations

from pathlib import Path

from .errors import ArtifactNotFoundError


def import_(
    module: str,
    version: str | None = None,
    *,
    artifact_dir: str | Path | None = None,
    build_if_missing: bool | None = None,
):
    """Import a Go module by loading a prebuilt artifact.

    If `artifact_dir` is omitted, a default artifact root is used.

    `build_if_missing` is tri-state:
    - True: build missing artifacts into the selected artifact root.
    - False: never build; missing artifacts raise ArtifactNotFoundError.
    - None (auto): build only when `artifact_dir` is omitted.
    """
    from .artifact import resolve_manifest
    from .handle import PackageHandle
    from .paths import default_artifact_root

    auto_root = artifact_dir is None
    artifact_root = Path(artifact_dir) if artifact_dir is not None else default_artifact_root()
    artifact_root.mkdir(parents=True, exist_ok=True)

    if build_if_missing is None:
        build_if_missing = auto_root

    # Convenience for dev: allow passing a local module directory path.
    # When `module` is a directory, resolve its module path and import that,
    # including mapping subdirectories to subpackage import paths.
    runtime_pkg = module
    build_target = module
    module_path_arg = Path(module)
    if module_path_arg.exists() and module_path_arg.is_dir():
        from .builder.resolve import resolve_module_target

        resolved = resolve_module_target(target=module, version=version)
        build_target = str(resolved.module_dir)
        # If `module` points to a subdirectory of the module, treat it as a
        # subpackage import path under the module.
        rel = module_path_arg.resolve().relative_to(resolved.module_dir)
        if str(rel) == ".":
            runtime_pkg = resolved.module_path
        else:
            suffix = "/".join(rel.parts)
            runtime_pkg = f"{resolved.module_path}/{suffix}"

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

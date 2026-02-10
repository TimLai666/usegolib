from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(prog="usegolib")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("version", help="Print usegolib version.")

    p_build = sub.add_parser("build", help="Build a Go module into an artifact directory.")
    p_build.add_argument(
        "--module",
        required=True,
        help="Go module directory path OR Go module/package import path (v0).",
    )
    p_build.add_argument("--out", required=True, help="Output artifact directory.")
    p_build.add_argument("--version", default=None, help="Go module version (remote only; default: @latest).")
    p_build.add_argument("--force", action="store_true", help="Force rebuild even if artifact exists.")
    p_build.add_argument(
        "--gomodcache",
        default=None,
        help="Optional Go module cache root (sets GOMODCACHE for the build).",
    )
    p_build.add_argument(
        "--redownload",
        action="store_true",
        help="Re-download Go modules before building (implies --force).",
    )
    p_build.add_argument(
        "--generics",
        default=None,
        help="Path to generics instantiation config JSON (optional).",
    )

    p_pkg = sub.add_parser(
        "package",
        help="Generate a Python package project embedding the built artifact (v0).",
    )
    p_pkg.add_argument(
        "--module",
        required=True,
        help="Go module directory path OR Go module/package import path (v0).",
    )
    p_pkg.add_argument("--python-package-name", required=True, help="Python package name to generate.")
    p_pkg.add_argument("--out", required=True, help="Output directory for the generated project.")
    p_pkg.add_argument("--version", default=None, help="Go module version (remote only; default: @latest).")

    p_art = sub.add_parser("artifact", help="Manage the local artifact cache.")
    art = p_art.add_subparsers(dest="artifact_cmd", required=True)

    p_art_rm = art.add_parser("rm", help="Delete cached artifacts for a module/package.")
    p_art_rm.add_argument(
        "--module",
        required=True,
        help="Same value you pass to usegolib.import_: local module dir OR import path.",
    )
    p_art_rm.add_argument(
        "--artifact-dir",
        default=None,
        help="Artifact root directory (default: USEGOLIB_ARTIFACT_DIR or OS cache).",
    )
    p_art_rm.add_argument(
        "--version",
        default=None,
        help="Artifact version to delete (required unless --all-versions).",
    )
    p_art_rm.add_argument(
        "--all-versions",
        action="store_true",
        help="Delete all versions for this module/package on the current platform.",
    )
    p_art_rm.add_argument(
        "--yes",
        action="store_true",
        help="Actually perform deletion. Without --yes, prints the matched directories.",
    )

    p_art_rebuild = art.add_parser("rebuild", help="Rebuild artifacts into an artifact root.")
    p_art_rebuild.add_argument(
        "--module",
        required=True,
        help="Local module dir OR import path (module or package).",
    )
    p_art_rebuild.add_argument(
        "--artifact-dir",
        default=None,
        help="Artifact root directory (default: USEGOLIB_ARTIFACT_DIR or OS cache).",
    )
    p_art_rebuild.add_argument("--version", default=None, help="Go module version (remote only; default: @latest).")
    p_art_rebuild.add_argument(
        "--redownload",
        action="store_true",
        help="Re-download Go modules before rebuilding (uses an isolated GOMODCACHE under the artifact root).",
    )
    p_art_rebuild.add_argument(
        "--clean",
        action="store_true",
        help="Delete any existing matching artifacts before rebuilding.",
    )

    p_gen = sub.add_parser(
        "gen",
        help="Generate a static Python bindings module from an artifact manifest schema.",
    )
    p_gen.add_argument("--artifact-dir", required=True, help="Artifact root directory containing manifest.json.")
    p_gen.add_argument("--package", required=True, help="Go package import path to generate bindings for.")
    p_gen.add_argument("--out", required=True, help="Output .py file path.")
    p_gen.add_argument("--version", default=None, help="Artifact version to resolve (optional).")

    args = parser.parse_args()
    if args.cmd == "version":
        try:
            print(importlib.metadata.version("usegolib"))
        except Exception:
            # Best-effort fallback for editable/local-only contexts.
            print("0.0.0")
        return

    if args.cmd == "build":
        from .builder.build import build_artifact

        gomodcache = Path(args.gomodcache) if args.gomodcache else None
        clean_gomodcache = False
        force = bool(args.force)
        if args.redownload:
            force = True
            clean_gomodcache = True
            if gomodcache is None:
                # Use a deterministic isolated cache directory under the output root.
                h = hashlib.sha256(f"{args.module}@{args.version or '@latest'}".encode("utf-8")).hexdigest()
                gomodcache = Path(args.out) / ".usegolib-gomodcache" / h

        build_artifact(
            module=args.module,
            out_dir=Path(args.out),
            version=args.version,
            force=force,
            generics=Path(args.generics) if args.generics else None,
            gomodcache_dir=gomodcache,
            clean_gomodcache=clean_gomodcache,
        )
        return

    if args.cmd == "package":
        from .builder.build import build_artifact
        from .artifact import read_manifest
        from .packager.generate import generate_project

        module_dir = args.module
        out_dir = Path(args.out)

        # Build artifacts into a temporary root, then embed them into the project.
        tmp_root = out_dir / f".usegolib_tmp_artifacts_{args.python_package_name}"
        if tmp_root.exists():
            raise SystemExit(f"temporary artifact dir already exists: {tmp_root}")
        try:
            manifest_path = build_artifact(module=module_dir, out_dir=tmp_root, version=args.version)
            manifest = read_manifest(manifest_path.parent)
            generate_project(
                python_package_name=args.python_package_name,
                module=manifest.module,
                artifact_root=tmp_root,
                out_dir=out_dir,
            )
        finally:
            if tmp_root.exists():
                # Best-effort cleanup. The generated project contains its own copy.
                import shutil

                shutil.rmtree(tmp_root, ignore_errors=True)
        return

    if args.cmd == "artifact":
        from .artifact import delete_artifacts, find_manifest_dirs
        from .paths import default_artifact_root

        artifact_root = Path(args.artifact_dir) if args.artifact_dir else default_artifact_root()
        artifact_root.mkdir(parents=True, exist_ok=True)

        # Match import_ behavior for local paths: map a module subdir to a subpackage import path.
        runtime_pkg = args.module
        module_path_arg = Path(args.module)
        if module_path_arg.exists() and module_path_arg.is_dir():
            from .builder.resolve import resolve_module_target

            resolved = resolve_module_target(target=args.module, version=args.version, env=None)
            rel = module_path_arg.resolve().relative_to(resolved.module_dir)
            if str(rel) == ".":
                runtime_pkg = resolved.module_path
            else:
                runtime_pkg = f"{resolved.module_path}/{'/'.join(rel.parts)}"

        if args.artifact_cmd == "rm":
            if args.version is None and not args.all_versions:
                raise SystemExit("artifact rm requires --version unless --all-versions is set")
            dirs = find_manifest_dirs(
                artifact_root,
                package=runtime_pkg,
                version=args.version,
                all_versions=bool(args.all_versions),
            )
            if not dirs:
                print("no matching artifacts found")
                return
            if not args.yes:
                print("matched artifact directories (use --yes to delete):")
                for d in dirs:
                    print(str(d))
                raise SystemExit(2)
            deleted = delete_artifacts(
                artifact_root,
                package=runtime_pkg,
                version=args.version,
                all_versions=bool(args.all_versions),
            )
            for d in deleted:
                print(f"deleted: {d}")
            return

        if args.artifact_cmd == "rebuild":
            if getattr(args, "clean", False):
                _ = delete_artifacts(
                    artifact_root,
                    package=runtime_pkg,
                    version=args.version,
                    all_versions=(args.version is None),
                )

            gomodcache = None
            clean_gomodcache = False
            if getattr(args, "redownload", False):
                clean_gomodcache = True
                h = hashlib.sha256(f"{args.module}@{args.version or '@latest'}".encode("utf-8")).hexdigest()
                gomodcache = artifact_root / ".usegolib-gomodcache" / h

            from .builder.build import build_artifact

            manifest_path = build_artifact(
                module=args.module,
                out_dir=artifact_root,
                version=args.version,
                force=True,
                gomodcache_dir=gomodcache,
                clean_gomodcache=clean_gomodcache,
            )
            print(str(manifest_path))
            return

    if args.cmd == "gen":
        from .artifact import resolve_manifest
        from .bindgen import BindgenOptions, generate_python_bindings
        from .schema import Schema

        artifact_root = Path(args.artifact_dir)
        manifest = resolve_manifest(artifact_root, package=args.package, version=args.version)
        schema = Schema.from_manifest(manifest.schema)
        if schema is None:
            raise SystemExit("manifest schema is missing; rebuild artifact with schema exchange enabled")

        generate_python_bindings(
            schema=schema,
            pkg=args.package,
            out_file=Path(args.out),
            opts=BindgenOptions(package=args.package),
        )
        return

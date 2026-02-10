from __future__ import annotations

import argparse
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

        build_artifact(
            module=args.module,
            out_dir=Path(args.out),
            version=args.version,
            force=bool(args.force),
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

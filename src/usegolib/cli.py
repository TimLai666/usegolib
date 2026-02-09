from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(prog="usegolib")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("version", help="Print usegolib version.")

    p_build = sub.add_parser("build", help="Build a Go module into an artifact directory.")
    p_build.add_argument("--module", required=True, help="Go module directory path (v0).")
    p_build.add_argument("--out", required=True, help="Output artifact directory.")
    p_build.add_argument("--version", default=None, help="Go module version (remote only; default: @latest).")
    p_build.add_argument("--force", action="store_true", help="Force rebuild even if artifact exists.")

    p_pkg = sub.add_parser(
        "package",
        help="Generate a Python package project embedding the built artifact (v0).",
    )
    p_pkg.add_argument("--module", required=True, help="Go module directory path (v0).")
    p_pkg.add_argument("--python-package-name", required=True, help="Python package name to generate.")
    p_pkg.add_argument("--out", required=True, help="Output directory for the generated project.")
    p_pkg.add_argument("--version", default=None, help="Go module version (remote only; default: @latest).")

    args = parser.parse_args()
    if args.cmd == "version":
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

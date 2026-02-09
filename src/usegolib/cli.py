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

    args = parser.parse_args()
    if args.cmd == "version":
        print("0.0.0")
        return

    if args.cmd == "build":
        from .builder.build import build_artifact

        build_artifact(module=Path(args.module), out_dir=Path(args.out))
        return

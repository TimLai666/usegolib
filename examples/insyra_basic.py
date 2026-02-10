from __future__ import annotations

import usegolib


def main() -> None:
    # Build artifacts first:
    #   python -m usegolib build --module github.com/HazelnutParadise/insyra --out out/artifact
    insyra = usegolib.import_("github.com/HazelnutParadise/insyra", artifact_dir="out/artifact")

    col, ok = insyra.CalcColIndex(28)
    print("CalcColIndex(28) ->", col, ok)

    n, ok = insyra.ParseColIndex("AB")
    print('ParseColIndex("AB") ->', n, ok)


if __name__ == "__main__":
    main()


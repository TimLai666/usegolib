from __future__ import annotations

import usegolib


def main() -> None:
    # Dev-mode auto build:
    # - Downloads the Go module
    # - Builds a shared library artifact into usegolib's default artifact root
    #
    # Requirements (dev-mode only):
    # - Go toolchain installed (insyra@v0.2.14 requires go >= 1.25)
    # - Network access (module download)
    #
    # For end-users without Go, use a prebuilt wheel produced by `usegolib package`.
    insyra = usegolib.import_("github.com/HazelnutParadise/insyra", version="v0.2.14")

    # --- DataList (object handle + variadic any) ---
    dl = insyra.object("DataList")
    dl.Append(1, 2, 3, 4, 5)  # Go: Append(values ...any)
    print("DataList.Sum() ->", dl.Sum())
    print("DataList.Mean() ->", dl.Mean())
    print("DataList.Data() ->", dl.Data())

    # --- DataTable (variadic map[string]any + variadic bool) ---
    dt = insyra.object("DataTable")
    dt.AppendRowsByColIndex({"A": 1, "B": 2}, {"A": 3, "B": 4})
    print("DataTable.NumRows() ->", dt.NumRows())
    print("DataTable.NumCols() ->", dt.NumCols())
    print("DataTable.Data(True) ->", dt.Data(True))


if __name__ == "__main__":
    main()

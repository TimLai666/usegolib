from __future__ import annotations

import usegolib


def main() -> None:
    # Auto-build on import (developer convenience):
    # - Downloads the Go module
    # - Builds a shared library artifact into usegolib's default artifact root
    #
    # Requirements (for auto-build):
    # - Go toolchain installed (insyra@v0.2.14 requires go >= 1.25)
    # - Network access (module download)
    #
    # If you want to disable auto-build, pass `build_if_missing=False` (and usually an explicit `artifact_dir`).
    #
    # For end-users without Go, ship a prebuilt wheel produced by `usegolib package`.
    insyra = usegolib.import_("github.com/HazelnutParadise/insyra", version="v0.2.14")

    # --- DataList (object handle + variadic any) ---
    dl = insyra.NewDataList(1,2,3)  # Go: NewDataList() -> *DataList
    dl.Append(1, 2, 3, 4, 5)  # Go: Append(values ...any)
    print("DataList.Sum() ->", dl.Sum())
    print("DataList.Mean() ->", dl.Mean())
    print("DataList.Data() ->", dl.Data())
    print("DataList.Show() ->")
    dl.Show()
    
    # --- DataTable (variadic map[string]any + variadic bool) ---
    dt = insyra.NewDataTable()
    dt.AppendRowsByColIndex({"A": 1, "B": 2}, {"A": 3, "B": 4})
    print("DataTable.NumRows() ->", dt.NumRows())
    print("DataTable.NumCols() ->", dt.NumCols())
    print("DataTable.Data(True) ->", dt.Data(True))
    print("DataTable.Show() ->")
    dt.Show()
    dt.ToCSV("output.csv", True, False, False)

if __name__ == "__main__":
    main()

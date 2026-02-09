# spec0.md（第一版工程級草稿）

````markdown
# usegolib

**usegolib** lets Python directly use Go libraries —  
no C code, no daemon, no RPC.

> One Python process. One Go shared library. Zero glue code written by you.

---

## What problem does this solve?

- You have a Go library
- You want Python users to call it like a native Python module
- You do NOT want:
  - C/C++ glue code
  - gopy-style heavy bindings
  - running a Go server or subprocess

**usegolib** builds the Go module into a shared library and loads it directly
into the Python process.

---

## Key features

- 0 lines of C code
- No background Go process
- One Go module = one runtime per Python process
- Root package and subpackages supported
- MessagePack-based ABI (fast, structured)
- Go module versioning respected

---

## Example

```python
import usegolib

insyra = usegolib.import_("github.com/HazelnutParadise/insyra")
stats  = usegolib.import_("github.com/HazelnutParadise/insyra/stats")

dt = insyra.ReadCSV("data.csv")
print(stats.Mean(dt, "price"))
````

---

## Version rules (important)

* One Go module = one version per Python process
* If a module is already loaded, all subpackages must use the same version
* `version=None` defaults to `@latest`

```python
usegolib.import_("github.com/you/mod")              # @latest
usegolib.import_("github.com/you/mod/stats")        # same version

usegolib.import_("github.com/you/mod", "v1.2.0")
usegolib.import_("github.com/you/mod/stats", "v1.3.0")
# -> VersionConflictError
```

---

## How it works (high level)

1. Resolve Go module and version (`@latest` if omitted)
2. Build a Go bridge runtime (`-buildmode=c-shared`)
3. Load the shared library into Python
4. Exchange data via MessagePack
5. Call Go functions through namespaces

---

## Requirements

* Python 3.9+
* Go (build-time only)

End users can use prebuilt wheels without Go installed.


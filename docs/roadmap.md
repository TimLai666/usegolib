# usegolib Roadmap (Spec-Driven)

This document is the project-level roadmap. It is written to support "pause and resume" development: every milestone has clear deliverables, tests, and OpenSpec changes so work can be picked up later without re-deciding fundamentals.

## Summary

The project has two independent but compatible tracks:

- **Runtime (end-user / production)**: Python loads a prebuilt Go shared library into the Python process and calls into it via a MessagePack ABI. No daemon, no RPC, no subprocess. Production/end-user machines do **not** need the Go toolchain.
- **Build (CI / build machine)**: uses a Go toolchain and an auto-provisioned C compiler (Zig) to build Go modules into shared libraries, emitting a `manifest.json` that the runtime can load.

## Milestones

### Milestone 0 (Project Scaffold + Specs) -> v0.0.1

- `openspec/specs/usegolib-core/spec.md` (current truth)
- `docs/roadmap.md` (this file)
- `docs/abi.md` (MessagePack ABI + memory/free rules + error format)
- CI skeleton: lint/test matrix (Windows/macOS/Linux + Python 3.10-3.13)

OpenSpec changes (recommended):
- `add-project-scaffold`
- `add-abi-v0-spec`

### Milestone 1 (Runtime Loader + Calls) -> v0.1.0

- Python package `usegolib` (runtime loader + ABI client)
- `ModuleHandle` proxy: `usegolib.import_(...) -> ModuleHandle`, `handle.FuncName(...)` via ABI `call`
- Error taxonomy (see `docs/abi.md`)
- Level 1 type bridge: `nil/bool/int/float/str/bytes + slices`

Tests:
- Unit tests for ABI encoding/decoding and manifest parsing
- Integration tests: load an artifact and call into a test Go module (bytes/ints/floats/slices/error/panic)

OpenSpec change:
- `implement-runtime-loader-v0`

### Milestone 2 (Builder + Manifest + Zig Bootstrap) -> v0.2.0

- `usegolib build` CLI:
  - Resolve module/version (`@latest` or pinned)
  - Determine accessible packages (root + subpackages; excludes Go `internal/` packages)
  - Scan exported functions for supported signatures (Level 1 only)
  - Generate a Go bridge runtime + registry
  - Build with `go build -buildmode=c-shared`
  - Emit `manifest.json` including symbols and hashes
- Zig auto-provisioning (download/cache Zig; set `CC="zig cc"` for cgo)

Tests:
- CI builds artifacts on all 3 OSes and runs runtime integration tests against them

OpenSpec changes:
- `implement-builder-v0`
- `add-zig-toolchain-bootstrap`

### Milestone 3 (Packager -> Wheel Layout) -> v0.3.0

- `usegolib package` to generate a Python package skeleton embedding artifacts + manifest
- Wheel build flow where end-user `pip install` does not require Go

OpenSpec change:
- `add-packager-and-wheel-layout`

### Milestone 4 (Hardening + Type Levels) -> v0.4 - v0.6

- v0.4: caching + file locking + concurrency safety
- v0.5: Type bridge Level 2 (`map[string]T`)
- v0.6: Type bridge Level 3 Phase A (record structs)

### Milestone 6 (API Expansion: Methods + Generics) -> v0.7 - v0.9

Current v0.x behavior: exported methods and generic functions are ignored by the build scanner.

- v0.7: Exported method support
  - allow calling exported methods by generating wrapper functions in the bridge (receiver passed explicitly)
  - define naming and overload rules in schema/manifest (avoid collisions)
- v0.8: Generic function support (Phase A)
  - support calling generic functions by generating concrete instantiations at build time for a configured set of type arguments
  - avoid implicit type inference across the ABI (must be explicit in schema/bindings)
- v0.9: Generics (Phase B)
  - expand supported instantiation patterns and improve Python typing/bindgen output

### Milestone 5 (ABI Stability + Compatibility Policy) -> v1.0

- ABI/manfiest versioning policy
- security hardening (hash verification, restricted downloads)
- production documentation (troubleshooting, compatibility matrix)

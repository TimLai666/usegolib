## Context

`usegolib` aims to let Python code call Go libraries directly, without C glue code, without a background Go process, and without RPC. The boundary must be stable, fast, and debuggable.

## Goals / Non-Goals

- Goals:
  - A single Python API that imports a Go module and exposes its packages/namespaces.
  - One Go runtime per Go module per Python process (version-consistent).
  - A structured, language-agnostic ABI for calls and results (MessagePack).
  - V0 type bridge is limited and predictable (Level 1).
- Non-Goals (for v0):
  - Automatic encoding/decoding of arbitrary structs or rich custom types (Level 3).
  - Supporting multiple versions of the same Go module within one Python process.

## Decisions

- ABI encoding uses MessagePack.
- Type support is defined in levels:
  - Level 1 (v0): `nil`, `bool`, integers, floats, `string`, `bytes`, and slices of these.
  - Level 2 (planned): add `map[string]T` where `T` is Level 1 or slice-of-Level-1.
  - Level 3 (planned): add struct/custom type support.

## Upgrade Roadmap (Level 1 -> 3)

This roadmap is intentionally staged to preserve backward compatibility:

1. Add Level 2 without changing Level 1 encodings.
   - Introduce `map[string]T` with explicit key type (`string`) and limited value types.
   - Add tests ensuring Level 1 payloads decode identically before/after.
2. Add Level 3 in two phases:
   - Phase A: "Record structs" (interop-first).
     - Represent structs as MessagePack maps of exported field names to values.
     - Optionally include type metadata (e.g., fully-qualified Go type name) as an opt-in envelope field.
   - Phase B: "Typed structs" (correctness-first).
     - Add a schema or signature exchange step (at import time) describing structs and method signatures.
     - Enforce field types and support nested structs by schema recursion.

Compatibility rule: new levels MUST NOT change the meaning of existing Level 1 payloads.

## Risks / Trade-offs

- Level 3 typed support adds complexity (schema versioning, compatibility, and drift management).
- Schema exchange requires tight coordination between the Go bridge and Python loader; keep it optional until needed.


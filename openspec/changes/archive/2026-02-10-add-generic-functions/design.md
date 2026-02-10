## Context

Go generic (type parameter) functions cannot be called through the current v0 bridge because:
- the scanner intentionally skips generic declarations
- the bridge registers only concrete (non-generic) symbols

However, many generic functions become callable if we choose a concrete instantiation at build time.

## Goals / Non-Goals

**Goals:**
- Scan exported top-level generic functions and capture their (generic) signature shape.
- Allow build-time instantiation via an explicit config file to avoid implicit inference.
- Generate concrete bridge wrappers that call `Fn[T1,T2,...](...)`.
- Record the mapping in `manifest.json` schema so runtime can resolve and validate calls.
- Provide a runtime helper API for calling generic instantiations.

**Non-Goals:**
- Auto-infer generic type arguments at runtime.
- Support generic methods (receiver + type params) in this change.
- Support arbitrary constraint analysis; compilation is the final authority.

## Decisions

- **Explicit configuration**: generic instantiations are selected by `usegolib build --generics <path>`.
  - Rationale: avoids guesswork and unstable heuristics; keeps ABI unchanged.
- **Concrete symbol export**: each instantiation becomes a normal callable symbol with a stable, mangled name.
  - Rationale: reuses existing `call` op and schema validation; no ABI changes.
- **Schema mapping**: store `schema.generics` as a list of mapping entries so runtime can resolve `generic(name, type_args)`.
  - Rationale: avoids relying on name-mangling in user code and allows future bindgen improvements.

## Config Format

JSON file with an `instantiations` list:

```json
{
  "instantiations": [
    {"pkg": "example.com/mod", "name": "Id", "type_args": ["int64"]},
    {"pkg": "example.com/mod", "name": "Id", "type_args": ["Person"], "symbol": "Id__Person"}
  ]
}
```

If `symbol` is omitted, the builder generates a stable name based on type arguments.

## Risks / Trade-offs

- [Many instantiations] → Mitigation: require explicit config, do not default to “instantiate everything”.
- [Type argument mismatch / build failure] → Mitigation: validate arity and fail fast with actionable BuildError.
- [Schema missing] → Mitigation: runtime generic helper requires schema; otherwise users can only call concrete symbol names directly.


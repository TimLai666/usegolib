## Context

Current scanner/type-bridge intentionally excluded `any` and variadic parameters. That made the system safe and simple, but it also excludes a large class of practical APIs (especially data libraries).

## Goals / Non-Goals

**Goals:**
- Recognize variadic parameters in scanning and bridge generation.
- Support `any` values (and `[]any`, `map[string]any`) across the ABI.
- Preserve existing ABI v0 and existing behavior for non-variadic, non-`any` symbols.

**Non-Goals:**
- Support arbitrary map key types (e.g. `map[any]any`).
- Provide strict schema validation for `any` beyond "MessagePack-compatible".

## Decisions

- Represent variadic parameters in schema as `...T`.
  - Rationale: keeps the information in the manifest without needing a separate boolean.
- Transport shape for variadic:
  - Runtime packs Python varargs into a single list value for the last parameter.
  - Bridge wrapper expands that slice when calling Go (`arg...`).
- Validation:
  - `any` is treated as permissive; when schema says `any`, validation accepts any value.

## Risks / Trade-offs

- [More permissive typing] → Mitigation: keep `any` opt-in by signature; callers still get validation for non-`any` types.
- [Ambiguity for already-packed list] → Mitigation: runtime treats "exact arity and last arg is list/tuple" as already-packed.


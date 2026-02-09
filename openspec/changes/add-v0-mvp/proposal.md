# Change: V0 MVP Spec For `usegolib`

## Why

Define a concrete, testable MVP spec for `usegolib` so implementation can proceed with clear behavior, errors, and compatibility guarantees.

## What Changes

- Add the initial capability spec for `usegolib` (Python API, module/version rules, build/load behavior, ABI, and supported cross-language types).
- Define a staged upgrade path from type support Level 1 to Level 3 (recorded as a roadmap, not required for v0).

## Impact

- Affected specs: `usegolib-core`
- Affected code (future): Python package API surface, Go build/load pipeline, ABI encoding/decoding, error mapping, caching layout.


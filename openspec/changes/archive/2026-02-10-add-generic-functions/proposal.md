## Why

Go 1.18+ generic (type parameter) functions are currently ignored by the builder scanner, so they cannot be called from Python even when their concrete instantiations would be safe under the v0 type bridge.

## What Changes

- Builder scans exported generic functions (top-level) and allows **explicit build-time instantiation** into callable bridge symbols.
- `usegolib build` accepts a generics instantiation config file to select concrete type arguments.
- Artifacts embed a schema mapping from generic function + type arguments to the generated concrete symbol name.
- Runtime exposes a helper API to call generic instantiations without relying on ad-hoc name mangling.
- Bindgen includes generated functions for instantiated generic symbols (Phase A/B usability).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `usegolib-core`: add requirements for build-time generic instantiation + runtime calling support

## Impact

- Affected code:
  - builder scanner (`src/usegolib/builder/scan.py`)
  - builder artifact build + manifest schema (`src/usegolib/builder/build.py`)
  - Go bridge generator (`src/usegolib/builder/gobridge.py`)
  - runtime API (`src/usegolib/handle.py`, `src/usegolib/schema.py`)
  - CLI surface (`src/usegolib/cli.py`)
  - bindgen (`src/usegolib/bindgen.py`)
- CLI: new optional `usegolib build --generics <path>` flag
- Manifest schema: adds `schema.generics` mapping (non-breaking; additive)

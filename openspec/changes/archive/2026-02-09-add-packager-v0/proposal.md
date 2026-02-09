## Why

To achieve the "numpy-like" distribution model, Go artifacts should be built on a build machine and shipped inside a Python wheel. End users should be able to `pip install` a package and call Go functions without having the Go toolchain installed.

## What Changes

- Add `usegolib package` command that generates a Python package project embedding:
  - `manifest.json`
  - the Go shared library for the current platform
- The generated package depends on `usegolib` runtime loader and exposes a simple import surface.

## Capabilities

### New Capabilities
- `usegolib-packager`: generating a distributable Python package that embeds artifacts

### Modified Capabilities
- *(none)*

## Impact

- New CLI command: `usegolib package`
- New docs for generated package layout
- Adds tests that verify the generated project structure and that embedded artifacts can be loaded at runtime (local install)


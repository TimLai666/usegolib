# Versioning Policy

This document defines versioning and compatibility rules for:
- the on-disk artifact manifest (`manifest.json`)
- the wire ABI between Python and the Go shared library (MessagePack payloads)
- schema exchange (types, record structs, typed adapters)

## Terms

- **Runtime**: the Python package `usegolib` that loads artifacts and performs calls.
- **Artifact**: a built shared library plus `manifest.json` (and any embedded schema).
- **ABI version**: `abi_version` in the manifest; a major compatibility marker for the MessagePack call protocol + C entrypoints.
- **Manifest version**: `manifest_version` in the manifest; a compatibility marker for `manifest.json` schema.

## Runtime <-> Artifact Compatibility

An artifact is loadable only if:
- `manifest_version` is supported by the runtime
- `abi_version` is supported by the runtime
- artifact `goos/goarch` matches the current host
- the shared library SHA256 matches `manifest.json` (integrity check)

If any of the above fails, the runtime rejects loading with `LoadError`.

## ABI Versioning

`abi_version` is bumped when the wire protocol or exported C ABI changes in a way that older runtimes cannot safely interpret.

Compatible changes within a fixed `abi_version` include:
- adding new optional keys to request/response maps
- adding new error `type` strings
- adding new schema features, provided older runtimes fail fast (reject) rather than mis-decoding

Breaking changes that require a new `abi_version` include:
- changing the meaning of existing request/response keys
- changing required keys in a way that makes older runtimes accept but behave incorrectly
- changing C entrypoint signatures (`usegolib_call`, `usegolib_free`)

## Manifest Versioning

`manifest_version` is bumped when the manifest schema changes incompatibly.

Compatible changes within a fixed `manifest_version` include:
- adding new optional fields
- adding new symbol/type metadata fields that older runtimes can ignore

Breaking changes that require a new `manifest_version` include:
- removing or renaming fields that existing runtimes require
- changing field semantics in a way that could cause silent misbehavior

## Schema Exchange Evolution

Schema exchange (symbols, type graph, struct fields, typed adapters) may evolve in v0.x.

Rule: adding new schema features is allowed if older runtimes reject artifacts that require those features (no silent downgrade).


## Why

The v0 builder currently scans exported functions by parsing `go doc` text output. This is brittle and fails for valid Go syntax like grouped parameters (e.g. `func F(a, b int64) int64`), which causes callable symbols to be silently skipped.

Level 3 (record structs) also needs a more robust foundation for extracting function signatures and referenced type names.

## What Changes

- Replace `go doc` text parsing with a scanner that parses Go source (AST) to discover exported top-level functions and their parameter/return types.
- Ensure grouped parameters are correctly expanded into positional arguments.

## Impact

- Builder function scanning becomes robust to formatting and multi-line signatures.
- The set of callable symbols may increase (previously-missed functions become available).


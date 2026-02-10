# Change: Return Opaque Pointer Results As Object Handles

## Why
Many Go libraries (e.g. Insyra) use fluent APIs that return pointers to structs whose fields are unexported (opaque). When `usegolib` exports `*T` as a record-struct dict, the Python result becomes `{}` and users cannot call methods on it.

## What Changes
- If a function/method returns `*T` where `T` is a struct type with **no exported fields** in the manifest schema, the bridge returns an **object id** instead of exporting a dict.
- The Python runtime wraps that id as a `GoObject` so users can call methods naturally.

## Impact
- Affected specs: `usegolib-core`
- Affected code: bridge generator, schema validation, runtime handle conversion, integration tests


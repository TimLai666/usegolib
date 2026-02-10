# Proposal: Support `error`-Only Returns

## Why
Some Go APIs return only `error` to signal success/failure (for example `ToCSV(...) error`).
For a successful call, the value is `nil` and there is no meaningful return payload.

Without explicit support, schema validation rejects `error` as an "unknown type", and the bridge
may attempt to serialize non-nil error interfaces as values.

## What Changes
- `error` is treated as a special result type: on success it is represented as `nil`.
- If an `error`-only return is non-nil, the bridge reports it as `GoError` via the ABI error envelope.


## Why

Schema exchange (Phase B) is in place, but typed structs are still incomplete:

- Record struct conversion only matches Go exported field names, not common struct tags (`json`, `msgpack`).
- Runtime validates args via schema but does not validate results, so type drift is harder to detect.

To make typed structs practical, we need tag-aware key mapping plus schema validation for results.

## What Changes

- Extend the builder schema to include canonical struct keys and key aliases derived from struct tags (`msgpack`, then `json`).
- Extend Go bridge record struct conversion to accept dict keys by exported field name or tag name.
- Extend Go bridge struct export to use canonical keys (tag name preferred).
- Extend runtime schema validation to:
  - accept tag aliases when validating dict keys
  - validate call results against the schema

## Impact

- More ergonomic Python dict shapes (tag-based keys) for typed structs.
- Better correctness and debuggability (schema-driven result validation).


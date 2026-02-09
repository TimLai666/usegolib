## Why

Builder reuse currently treats "artifact exists" as a cache hit. This breaks local development because source changes in a local module directory are not detected, so builds can incorrectly reuse stale artifacts. We need a lightweight input fingerprint to determine whether reuse is safe.

## What Changes

- Builder computes an input fingerprint for local module directory builds and writes it into `manifest.json`.
- Reuse logic compares the current fingerprint to the fingerprint recorded in `manifest.json`; mismatch triggers rebuild.

## Capabilities

### New Capabilities
- *(none)*

### Modified Capabilities
- `usegolib-core`: caching semantics for local module directory builds

## Impact

- Artifact manifest gains a new field for local builds: `input_fingerprint`.
- Adds an integration test (gated) that verifies a local source change triggers rebuild.


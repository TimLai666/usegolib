# Change: Verify Shared Library SHA256 Before Load

## Why
Artifacts include a `library.sha256` field in `manifest.json`, but the runtime currently trusts the file on disk.
Verifying the hash before loading makes artifact loading safer and catches corrupted or tampered artifacts early.

## What Changes
- Runtime verifies that the shared library file's SHA256 matches `manifest.json` before `dlopen`/`LoadLibrary`.
- If the hash is missing, invalid, or mismatched, the runtime raises `LoadError`.

## Impact
- Affected specs: `usegolib-core`
- Affected code: `src/usegolib/handle.py`, `src/usegolib/artifact.py`
- Tests: add unit tests that validate behavior without loading a real shared library (via monkeypatch).


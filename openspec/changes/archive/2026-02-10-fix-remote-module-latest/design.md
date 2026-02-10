# Design: Remote Version Defaulting

## Rule

- If `version is None`: use `@latest`.
- If `version == "latest"`: treat as `@latest`.
- If `version` already starts with `@`: pass through.
- Otherwise: pass through as-is (e.g. `v1.2.3`, pseudo-versions).

## Testing

Add unit tests that monkeypatch the internal `_go_mod_download_json` to capture the argument string passed to `go mod download -json`, verifying the `@latest` default without requiring `go` in unit tests.


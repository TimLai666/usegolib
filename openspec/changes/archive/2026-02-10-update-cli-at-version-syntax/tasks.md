## 1. Specs And Validation

- [x] 1.1 Update usegolib-dev spec to reflect module@version CLI syntax
- [x] 1.2 Run `openspec validate update-cli-at-version-syntax --type change --strict --no-interactive`

## 2. Implementation

- [x] 2.1 Builder: parse `target@version` in resolve logic
- [x] 2.2 CLI: remove `--version` flags and accept `@version` for build/package/artifact/gen
- [x] 2.3 Docs: update CLI docs/examples

## 3. Tests

- [x] 3.1 Unit: resolve parses inline @version

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run `openspec validate --all --strict --no-interactive`

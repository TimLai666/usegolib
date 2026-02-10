## 1. Specs And Validation

- [x] 1.1 Run `openspec validate update-go-not-found-hint --strict --no-interactive`

## 2. Builder Errors

- [x] 2.1 Wrap missing `go` executable in a `BuildError` with an actionable hint (builder command runner)
- [x] 2.2 Wrap missing `go` executable in a `BuildError` for module resolution (`go mod download`)
- [x] 2.3 Wrap missing `go` executable in a `BuildError` for scanning (`go run` scanner)

## 3. Tests

- [x] 3.1 Add unit tests that simulate missing `go` and assert `BuildError` message contains guidance

## 4. Verification

- [x] 4.1 Run `python -m pytest -q`
- [x] 4.2 Run `openspec validate --all --strict --no-interactive`

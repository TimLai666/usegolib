# Proposal: Use `module@version` Syntax In CLI

## Why
The Go ecosystem commonly specifies versions inline using `@` (for example `go get module@vX.Y.Z`).
Using the same convention in `usegolib` reduces friction and avoids an extra `--version` flag across commands.

## What Changes
- CLI commands accept `@version` as part of the `--module` / `--package` values.
- CLI no longer exposes a separate `--version` flag for those commands.


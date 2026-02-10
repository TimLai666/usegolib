# Proposal: CLI Remote Build + Artifact Cache Management

## Summary
Add developer-facing CLI commands to:
- build artifacts from remote Go module import paths (via `go mod download`)
- force rebuild and optionally re-download module sources
- delete or rebuild cached artifacts in the default artifact root

Also add documentation describing CLI installation and usage.

## Motivation
Users relying on auto-build or local artifact caching need a supported way to:
- rebuild a cached artifact (including re-downloading the Go module inputs)
- delete stale/ambiguous cached versions without manually spelunking the cache directory

## Non-Goals
- Publishing prebuilt artifacts to a public registry (handled by wheel packaging flows)
- Deleting Go's global module cache (`go clean -modcache`) system-wide

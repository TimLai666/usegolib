# Design: README Clarity For Go Requirement

This is a documentation-only change.

Key points to capture:
- `import_` can auto-build when `artifact_dir` is omitted.
- Auto-build requires a Go toolchain (Zig is bootstrapped automatically for cgo).
- End-users can avoid Go by using prebuilt artifacts or wheels embedding artifacts.


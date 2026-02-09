# Design: Policy Docs For v0.x -> v1.0 Readiness

This change is documentation-only. The design here defines where policy information lives and what it must cover.

## Docs Added

- `docs/versioning.md`: ABI + manifest versioning rules, compatibility expectations, and breaking-change definitions.
- `docs/compatibility.md`: supported OS/arch and Python versions; pinned toolchain versions and overrides.
- `docs/security.md`: threat model and what `usegolib` does and does not verify.
- `docs/reproducible-builds.md`: guidance for repeatable artifact builds (pins, environment, hashing).

## README Integration

README should link to the above docs from a "Policies" section so they are discoverable.


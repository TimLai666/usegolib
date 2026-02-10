## ADDED Requirements

### Requirement: README Clarifies Go Toolchain Requirement
The repository SHALL document in `README.md` when the Go toolchain is required (auto-build/build workflows) versus when it is not required (runtime with prebuilt artifacts/wheels).

#### Scenario: README includes a "Do users need Go?" section
- **WHEN** a developer reads `README.md`
- **THEN** it contains a section explaining that end-users do not need Go when using prebuilt artifacts/wheels
- **AND THEN** it explains that auto-build (downloading/building missing artifacts) requires a Go toolchain


## 1. Specification
- [ ] 1.1 Review `openspec/changes/add-v0-mvp/specs/usegolib-core/spec.md` and confirm requirement wording + scenarios
- [ ] 1.2 Decide naming for the Python API (`import_` vs `import_module`) and freeze it in the spec
- [ ] 1.3 Confirm error taxonomy names (e.g., `VersionConflictError`, `BuildError`) and freeze in the spec

## 2. Implementation (Future, After Spec Approval)
- [ ] 2.1 Create Python package skeleton (`usegolib/`, packaging metadata, minimal docs)
- [ ] 2.2 Implement module+version resolution (`@latest` default, pinned versions, conflict detection)
- [ ] 2.3 Implement build pipeline (Go `-buildmode=c-shared`) with caching and file locking
- [ ] 2.4 Implement dynamic loading of the shared library into the Python process
- [ ] 2.5 Implement MessagePack request/response ABI and dispatch
- [ ] 2.6 Implement Level 1 type bridge (nil/bool/int/float/str/bytes + slices)
- [ ] 2.7 Add conformance tests for all scenarios in `usegolib-core` spec


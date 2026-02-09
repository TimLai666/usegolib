## Context

`usegolib` already provides:

- A runtime loader that can import from an artifact root by scanning manifests.
- A builder that can emit artifacts for a local Go module directory.

Packaging is the missing glue: generate a distributable Python package that embeds the artifact directory tree and forwards calls.

## Goals / Non-Goals

**Goals:**
- Implement `usegolib package` for local Go module directories (v0).
- Generated project includes artifacts under `src/<pkg>/_usegolib_artifacts/` preserving the builder's layout.
- Generated `__init__.py` binds to the module root package and forwards attribute access.

**Non-Goals:**
- Multi-platform wheel building in one run (the generator outputs a project for the current platform).
- Publishing to PyPI (out of scope; user can build/install locally).

## Decisions

- The generated package will depend on `usegolib` (runtime) as a normal Python dependency.
- Artifact root inside package: `Path(__file__).resolve().parent / "_usegolib_artifacts"`.
- Forwarding model: module handle created lazily on first attribute access to avoid import-time failures in tooling.

## Risks / Trade-offs

- Depending on `usegolib` means the generated package is not standalone.
  - Mitigation: later milestone can vendor a minimal runtime into the generated package.


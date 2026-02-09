## Why

The packager's end goal is "numpy-like" distribution: end users install a wheel and run without the Go toolchain. We need a spec + automated integration test that builds a wheel from the generated project, installs it, and successfully calls into the embedded Go artifact without `go` on PATH.

## What Changes

- Extend `usegolib-packager` spec with an explicit wheel-install scenario (no Go toolchain at runtime).
- Add an integration test that:
  - runs `usegolib package` to generate a project
  - builds a wheel from that project
  - installs the wheel into a fresh venv
  - executes a call with a sanitized PATH (no `go` available)

## Capabilities

### New Capabilities
- *(none)*

### Modified Capabilities
- `usegolib-packager`: add wheel-install runtime requirement + scenario

## Impact

- Test suite gains another integration test gated behind `USEGOLIB_INTEGRATION=1`.
- Confirms the distribution contract (wheel contains artifacts and runs without Go toolchain).


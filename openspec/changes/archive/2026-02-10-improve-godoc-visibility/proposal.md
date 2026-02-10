# Proposal: Ensure GoDoc Is Visible In Python For All Callables

## Why
Users rely on Python introspection (`help()`, IDE hover, `.__doc__`) to discover APIs.
When importing Go modules dynamically, docstrings should be consistently available for every exported function/method.

## What Changes
- When schema is present, the runtime always sets `__doc__` for exported functions and methods:
  - prefers extracted GoDoc
  - falls back to a Go signature string when GoDoc is missing
- Typed wrappers preserve the underlying docstrings.
- Generic instantiation symbols include doc metadata when available.


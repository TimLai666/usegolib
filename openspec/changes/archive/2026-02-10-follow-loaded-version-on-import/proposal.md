# Proposal: Follow Loaded Module Version When Importing Subpackages

## Why
Users commonly import a root module with an explicit version and then import subpackages without repeating the version.
If multiple artifact versions exist on disk, omitting `version=` currently raises `AmbiguousArtifactError` before the runtime can
apply the per-process "single module version" rule.

## What Changes
- If a module has already been loaded in the current Python process, `usegolib.import_(..., version=None)` will follow that loaded version.
- This applies to both the root module import path and any subpackage import paths under that module.


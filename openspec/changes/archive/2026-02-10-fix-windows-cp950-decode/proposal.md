# Proposal: Fix Windows Locale Decode Errors In Builder

## Why
On Windows, Python may default to a non-UTF8 locale encoding (for example `cp950`).
Go tools typically emit UTF-8 output. When `subprocess.run(..., text=True)` is used,
Python attempts to decode stdout using the locale encoding and can raise `UnicodeDecodeError`.

This breaks auto-build and scanning on some Windows environments.

## What Changes
- Capture Go tool output as bytes and decode as UTF-8 with `errors="replace"` to avoid crashes.
- When JSON output is expected, tolerate non-JSON prefix lines by extracting the first JSON object.


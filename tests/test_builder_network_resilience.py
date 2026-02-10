from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


def test_go_command_retries_and_falls_back_to_goproxy_direct(monkeypatch: pytest.MonkeyPatch):
    # BuildError logs in the wild show transient failures fetching from proxy.golang.org.
    # We retry and (when GOPROXY isn't explicitly set) fall back to GOPROXY=direct.
    import usegolib.builder.build as b

    calls: list[dict[str, str] | None] = []

    def fake_run(*args, **kwargs):  # noqa: ANN001
        calls.append(kwargs.get("env"))
        if len(calls) == 1:
            return SimpleNamespace(
                returncode=1,
                stdout=b"",
                stderr=(
                    b'read "https://proxy.golang.org/x/y/@v/v0.0.0.zip": wsarecv: '
                    b"A connection attempt failed because the connected party did not properly respond"
                ),
            )
        return SimpleNamespace(returncode=0, stdout=b"ok\n", stderr=b"")

    monkeypatch.setattr(b.subprocess, "run", fake_run)
    monkeypatch.setattr(b.time, "sleep", lambda _s: None)

    out = b._run(["go", "list", "./..."], cwd=Path("."), env={})
    assert out == "ok\n"
    assert len(calls) == 2
    assert calls[1] is not None
    assert calls[1].get("GOPROXY") == "direct"


def test_go_command_failure_includes_actionable_hint(monkeypatch: pytest.MonkeyPatch):
    import usegolib.builder.build as b
    from usegolib.errors import BuildError

    def fake_run(*args, **kwargs):  # noqa: ANN001
        return SimpleNamespace(
            returncode=1,
            stdout=b"",
            stderr=b'read "https://proxy.golang.org/x/y/@v/v0.0.0.zip": i/o timeout',
        )

    monkeypatch.setattr(b.subprocess, "run", fake_run)
    monkeypatch.setattr(b.time, "sleep", lambda _s: None)

    with pytest.raises(BuildError) as ei:
        b._run(["go", "list", "./..."], cwd=Path("."), env={})

    msg = str(ei.value)
    assert "GOPROXY=direct" in msg


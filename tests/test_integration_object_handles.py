import os
import subprocess
import sys
from pathlib import Path

import pytest


def _write_go_test_module(mod_dir: Path) -> None:
    (mod_dir / "go.mod").write_text(
        "\n".join(
            [
                "module example.com/objmod",
                "",
                "go 1.22",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (mod_dir / "objmod.go").write_text(
        "\n".join(
            [
                "package objmod",
                "",
                'import (',
                '    "errors"',
                ')',
                "",
                "type AddReq struct {",
                "    Delta int64 `json:\"delta\"`",
                "}",
                "",
                "type Snapshot struct {",
                "    N int64 `json:\"n\"`",
                "}",
                "",
                "type Counter struct {",
                "    N int64 `json:\"n\"`",
                "}",
                "",
                "func (c *Counter) Inc(delta int64) int64 {",
                "    c.N += delta",
                "    return c.N",
                "}",
                "",
                "func (c *Counter) AddReq(req AddReq) int64 {",
                "    c.N += req.Delta",
                "    return c.N",
                "}",
                "",
                "func (c *Counter) Snapshot() Snapshot {",
                "    return Snapshot{N: c.N}",
                "}",
                "",
                "func (c *Counter) AddAndGet(delta int64) (int64, error) {",
                "    if delta < 0 {",
                "        return 0, errors.New(\"negative\")",
                "    }",
                "    c.N += delta",
                "    return c.N, nil",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


@pytest.mark.skipif(
    os.environ.get("USEGOLIB_INTEGRATION") != "1",
    reason="set USEGOLIB_INTEGRATION=1 to run integration tests",
)
def test_object_handles(tmp_path: Path):
    import usegolib
    from usegolib.errors import UseGoLibError

    mod_dir = tmp_path / "gomod"
    mod_dir.mkdir()
    _write_go_test_module(mod_dir)

    out_dir = tmp_path / "artifact"
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "usegolib",
            "build",
            "--module",
            str(mod_dir),
            "--out",
            str(out_dir),
        ]
    )

    h = usegolib.import_("example.com/objmod", artifact_dir=out_dir)

    with h.object("Counter", {"n": 1}) as c:
        assert c.Inc(2) == 3
        assert c.AddReq({"delta": 5}) == 8
        assert c.Snapshot() == {"n": 8}
        assert c.AddAndGet(1) == 9
        with pytest.raises(usegolib.errors.GoError):
            c.AddAndGet(-1)

    with pytest.raises(UseGoLibError) as ei:
        c.Inc(1)  # type: ignore[misc]  # closed object
    assert "closed" in str(ei.value)

    th = h.typed()
    types = th.types
    with th.object("Counter", types.Counter(N=10)) as tc:
        assert tc.Inc(1) == 11
        assert tc.AddReq(types.AddReq(Delta=2)) == 13
        snap = tc.Snapshot()
        assert snap == types.Snapshot(N=13)

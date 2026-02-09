import os
import subprocess
import sys
from pathlib import Path

import pytest


def _write_go_test_module(mod_dir: Path) -> None:
    (mod_dir / "go.mod").write_text(
        "\n".join(
            [
                "module example.com/testmod",
                "",
                "go 1.22",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (mod_dir / "testmod.go").write_text(
        "\n".join(
            [
                "package testmod",
                "",
                'import "errors"',
                "",
                "type Person struct {",
                "    Name string",
                "    Age int64",
                "    Data []byte",
                "    Meta map[string]int64",
                "}",
                "",
                "func MakePerson(name string, age int64) Person {",
                "    return Person{Name: name, Age: age, Data: []byte(name), Meta: map[string]int64{\"age\": age}}",
                "}",
                "",
                "func EchoPerson(p Person) Person {",
                "    return p",
                "}",
                "",
                "func IsAdult(p Person) bool {",
                "    return p.Age >= 18",
                "}",
                "",
                "func AddInt(a int64, b int64) int64 {",
                "    return a + b",
                "}",
                "",
                "func AddGrouped(a, b int64) int64 {",
                "    return a + b",
                "}",
                "",
                "func SumMap(m map[string]int64) int64 {",
                "    var s int64",
                "    for _, v := range m {",
                "        s += v",
                "    }",
                "    return s",
                "}",
                "",
                "func SumMapSlices(m map[string][]int64) int64 {",
                "    var s int64",
                "    for _, xs := range m {",
                "        for _, v := range xs {",
                "            s += v",
                "        }",
                "    }",
                "    return s",
                "}",
                "",
                "func ReturnMapBytes() map[string][]byte {",
                "    return map[string][]byte{",
                '        "a": []byte("abc"),',
                '        "b": []byte{0, 1, 2},',
                "    }",
                "}",
                "",
                "func EchoBytes(b []byte) []byte {",
                "    return b",
                "}",
                "",
                "func SumFloats(xs []float64) float64 {",
                "    var s float64",
                "    for _, x := range xs {",
                "        s += x",
                "    }",
                "    return s",
                "}",
                "",
                "func Fail(msg string) (string, error) {",
                "    return \"\", errors.New(msg)",
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
def test_build_and_call(tmp_path: Path):
    import usegolib

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

    h = usegolib.import_("example.com/testmod", artifact_dir=out_dir)
    assert h.AddInt(1, 2) == 3
    assert h.AddGrouped(10, 20) == 30
    assert h.MakePerson("bob", 20) == {"Name": "bob", "Age": 20, "Data": b"bob", "Meta": {"age": 20}}
    assert h.EchoPerson({"Name": "alice", "Age": 17, "Data": b"x", "Meta": {"age": 17}}) == {
        "Name": "alice",
        "Age": 17,
        "Data": b"x",
        "Meta": {"age": 17},
    }
    assert h.IsAdult({"Name": "z", "Age": 18, "Data": b"", "Meta": {}}) is True
    assert h.IsAdult({"Name": "z"}) is False
    assert h.SumMap({"a": 1, "b": 2}) == 3
    assert h.SumMapSlices({"x": [1, 2], "y": [3]}) == 6
    assert h.ReturnMapBytes() == {"a": b"abc", "b": bytes([0, 1, 2])}
    assert h.EchoBytes(b"abc") == b"abc"
    assert h.SumFloats([1.25, 2.5]) == pytest.approx(3.75)

    with pytest.raises(usegolib.errors.GoError):
        h.Fail("boom")

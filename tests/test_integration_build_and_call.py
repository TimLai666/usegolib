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
                'import (',
                '    "errors"',
                '    "time"',
                '    gouuid "github.com/google/uuid"',
                ')',
                "",
                "type Person struct {",
                "    Name string `json:\"name\"`",
                "    Age int64 `msgpack:\"age\"`",
                "    ID *gouuid.UUID `json:\"id,omitempty\"`",
                "    Nick string `json:\"nick,omitempty\"`",
                "    Secret string `json:\"-\"`",
                "    Data []byte",
                "    Meta map[string]int64",
                "}",
                "",
                "type Wrapper struct {",
                "    Person",
                "    Title string `json:\"title\"`",
                "}",
                "",
                "type Company struct {",
                "    CEO Person `json:\"ceo\"`",
                "    Employees []Person",
                "    VP *Person",
                "    Teams map[string]Person",
                "    Founded time.Time `json:\"founded\"`",
                "    Timeout time.Duration `json:\"timeout\"`",
                "}",
                "",
                "func MakePerson(name string, age int64) Person {",
                "    id := gouuid.MustParse(\"123e4567-e89b-12d3-a456-426614174000\")",
                "    return Person{Name: name, Age: age, ID: &id, Nick: \"\", Secret: \"shh\", Data: []byte(name), Meta: map[string]int64{\"age\": age}}",
                "}",
                "",
                "func MakeWrapper() Wrapper {",
                "    p := MakePerson(\"w\", 1)",
                "    return Wrapper{Person: p, Title: \"t\"}",
                "}",
                "",
                "func MakeCompany() Company {",
                "    ceo := Person{Name: \"ceo\", Age: 40, Data: []byte(\"ceo\"), Meta: map[string]int64{\"age\": 40}}",
                "    vp := Person{Name: \"vp\", Age: 35, Data: []byte(\"vp\"), Meta: map[string]int64{\"age\": 35}}",
                "    e1 := Person{Name: \"e1\", Age: 20, Data: []byte(\"e1\"), Meta: map[string]int64{\"age\": 20}}",
                "    e2 := Person{Name: \"e2\", Age: 21, Data: []byte(\"e2\"), Meta: map[string]int64{\"age\": 21}}",
                "    founded := time.Date(2020, 1, 2, 3, 4, 5, 6, time.UTC)",
                "    return Company{CEO: ceo, VP: &vp, Employees: []Person{e1, e2}, Teams: map[string]Person{\"a\": e1}, Founded: founded, Timeout: 5*time.Second}",
                "}",
                "",
                "func EchoCompany(c Company) Company {",
                "    return c",
                "}",
                "",
                "func EchoWrapper(w Wrapper) Wrapper {",
                "    return w",
                "}",
                "",
                "func EchoUUID(id gouuid.UUID) gouuid.UUID {",
                "    return id",
                "}",
                "",
                "func After(t0 time.Time, t1 time.Time) bool {",
                "    return t1.After(t0)",
                "}",
                "",
                "func AddOneDay(t time.Time) time.Time {",
                "    return t.Add(24 * time.Hour)",
                "}",
                "",
                "func AddDuration(d time.Duration, ns int64) time.Duration {",
                "    return d + time.Duration(ns)",
                "}",
                "",
                "func CountEmployees(cs []Company) int64 {",
                "    var n int64",
                "    for _, c := range cs {",
                "        n += int64(len(c.Employees))",
                "    }",
                "    return n",
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
    import usegolib.artifact
    import usegolib.bindgen
    import usegolib.schema
    import importlib.util

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
    assert h.MakePerson("bob", 20) == {
        "name": "bob",
        "age": 20,
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "Data": b"bob",
        "Meta": {"age": 20},
    }
    assert h.MakeWrapper() == {
        "Person": {
            "name": "w",
            "age": 1,
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "Data": b"w",
            "Meta": {"age": 1},
        },
        "title": "t",
    }
    assert h.MakeCompany() == {
        "ceo": {"name": "ceo", "age": 40, "Data": b"ceo", "Meta": {"age": 40}},
        "Employees": [
            {"name": "e1", "age": 20, "Data": b"e1", "Meta": {"age": 20}},
            {"name": "e2", "age": 21, "Data": b"e2", "Meta": {"age": 21}},
        ],
        "VP": {"name": "vp", "age": 35, "Data": b"vp", "Meta": {"age": 35}},
        "Teams": {"a": {"name": "e1", "age": 20, "Data": b"e1", "Meta": {"age": 20}}},
        "founded": "2020-01-02T03:04:05.000000006Z",
        "timeout": 5_000_000_000,
    }
    assert h.After("2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z") is True
    assert h.AddOneDay("2020-01-01T00:00:00Z") == "2020-01-02T00:00:00Z"
    assert h.AddDuration(1_000_000_000, 2_000_000_000) == 3_000_000_000
    assert h.EchoUUID("123e4567-e89b-12d3-a456-426614174000") == "123e4567-e89b-12d3-a456-426614174000"
    assert h.EchoCompany(
        {
            "ceo": {"name": "x", "age": 1, "Data": b"x", "Meta": {"age": 1}},
            "Employees": [{"name": "y", "age": 2, "Data": b"y", "Meta": {}}],
            "VP": None,
            "Teams": {},
            "founded": "2020-01-02T03:04:05.000000006Z",
            "timeout": 123,
        }
    ) == {
        "ceo": {"name": "x", "age": 1, "Data": b"x", "Meta": {"age": 1}},
        "Employees": [{"name": "y", "age": 2, "Data": b"y", "Meta": {}}],
        "VP": None,
        "Teams": {},
        "founded": "2020-01-02T03:04:05.000000006Z",
        "timeout": 123,
    }
    assert h.CountEmployees(
        [
            {
                "ceo": {"name": "x", "age": 1, "Data": b"x", "Meta": {}},
                "Employees": [{"name": "y", "age": 2, "Data": b"y", "Meta": {}}],
                "VP": None,
                "Teams": {},
                "founded": "2020-01-02T03:04:05.000000006Z",
                "timeout": 0,
            }
        ]
    ) == 1
    assert h.EchoPerson({"name": "alice", "age": 17, "Data": b"x", "Meta": {"age": 17}}) == {
        "name": "alice",
        "age": 17,
        "Data": b"x",
        "Meta": {"age": 17},
    }
    assert h.IsAdult({"name": "z", "age": 18, "Data": b"", "Meta": {}}) is True
    with pytest.raises(usegolib.errors.UnsupportedTypeError, match=r"schema:"):
        h.IsAdult({"name": "z"})
    with pytest.raises(usegolib.errors.UnsupportedTypeError, match=r"schema:"):
        h.EchoWrapper({"title": "t"})
    assert h.SumMap({"a": 1, "b": 2}) == 3
    assert h.SumMapSlices({"x": [1, 2], "y": [3]}) == 6
    assert h.ReturnMapBytes() == {"a": b"abc", "b": bytes([0, 1, 2])}
    assert h.EchoBytes(b"abc") == b"abc"
    assert h.SumFloats([1.25, 2.5]) == pytest.approx(3.75)

    with pytest.raises(usegolib.errors.GoError):
        h.Fail("boom")

    # Typed wrapper: decode record-struct results into dataclasses and accept dataclasses as inputs.
    ht = h.typed()
    p = ht.MakePerson("bob", 20)
    assert p.Name == "bob"
    assert p.Age == 20
    assert p.ID == "123e4567-e89b-12d3-a456-426614174000"
    assert p.Nick is None  # omitted by omitempty
    assert p.Data == b"bob"
    assert p.Meta == {"age": 20}
    assert ht.EchoPerson(p) == p

    w = ht.MakeWrapper()
    assert w.Title == "t"
    assert w.Person.Name == "w"

    # Static bindings generator: emit a Python module and call through it.
    manifest = usegolib.artifact.resolve_manifest(out_dir, package="example.com/testmod", version=None)
    schema = usegolib.schema.Schema.from_manifest(manifest.schema)
    assert schema is not None

    bind_path = tmp_path / "bindings_testmod.py"
    usegolib.bindgen.generate_python_bindings(
        schema=schema,
        pkg="example.com/testmod",
        out_file=bind_path,
        opts=usegolib.bindgen.BindgenOptions(package="example.com/testmod"),
    )
    spec = importlib.util.spec_from_file_location("bindings_testmod", bind_path)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    import sys as _sys

    _sys.modules[spec.name] = m
    spec.loader.exec_module(m)  # type: ignore[attr-defined]

    api = m.load(artifact_dir=out_dir)
    assert api.AddInt(1, 2) == 3

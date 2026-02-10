from __future__ import annotations

from pathlib import Path


def test_bindgen_emits_docstrings(tmp_path: Path):
    from usegolib.bindgen import BindgenOptions, generate_python_bindings
    from usegolib.schema import Schema

    manifest_schema = {
        "structs": {},
        "symbols": [
            {
                "pkg": "example.com/p",
                "name": "Add",
                "params": ["int64", "int64"],
                "results": ["int64"],
                "doc": "Add returns a+b.\n\nThis is a test doc.",
            }
        ],
        "methods": [],
        "generics": [],
    }
    schema = Schema.from_manifest(manifest_schema)
    assert schema is not None
    assert schema.symbol_docs_by_pkg["example.com/p"]["Add"].startswith("Add returns")

    out = tmp_path / "bindings.py"
    generate_python_bindings(
        schema=schema,
        pkg="example.com/p",
        out_file=out,
        opts=BindgenOptions(package="example.com/p"),
    )

    txt = out.read_text(encoding="utf-8")
    assert 'def Add(' in txt
    assert '"""' in txt
    assert "Add returns a+b." in txt
    assert "This is a test doc." in txt


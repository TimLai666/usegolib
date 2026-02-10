from __future__ import annotations


def test_schema_parses_vars_base_type():
    from usegolib.schema import Schema

    s = Schema.from_manifest(
        {
            "vars": [
                {"pkg": "example.com/p", "name": "DL", "type": "dl", "doc": "doc"},
                {"pkg": "example.com/p", "name": "PDL", "type": "*dl", "doc": ""},
            ]
        }
    )
    assert s is not None
    assert s.vars_by_pkg["example.com/p"]["DL"] == "dl"
    assert s.vars_by_pkg["example.com/p"]["PDL"] == "dl"
    assert s.var_docs_by_pkg["example.com/p"]["DL"] == "doc"


from __future__ import annotations


def test_schema_parses_generics_mapping():
    from usegolib.schema import Schema

    manifest_schema = {
        "structs": {},
        "symbols": [
            {
                "pkg": "example.com/mod",
                "name": "Id__int64",
                "params": ["int64"],
                "results": ["int64"],
            }
        ],
        "generics": [
            {
                "pkg": "example.com/mod",
                "name": "Id",
                "type_args": ["int64"],
                "symbol": "Id__int64",
            }
        ],
    }

    schema = Schema.from_manifest(manifest_schema)
    assert schema is not None
    assert schema.generics_by_pkg["example.com/mod"]["Id"][("int64",)] == "Id__int64"


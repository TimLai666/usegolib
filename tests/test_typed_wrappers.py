from __future__ import annotations

from usegolib.schema import Schema
from usegolib.typed import decode_value, encode_value, make_package_types


def test_typed_wrappers_encode_decode_roundtrip():
    schema = Schema.from_manifest(
        {
            "structs": {
                "example.com/p": {
                    "Person": [
                        {"name": "Name", "type": "string", "key": "name", "required": True},
                        {"name": "Age", "type": "int64", "key": "age", "required": True},
                        {"name": "Nick", "type": "string", "key": "nick", "omitempty": True, "required": False},
                        {"name": "Data", "type": "[]byte", "key": "Data", "required": True},
                        {"name": "Meta", "type": "map[string]int64", "key": "Meta", "required": True},
                    ]
                }
            },
            "symbols": [
                {
                    "pkg": "example.com/p",
                    "name": "EchoPerson",
                    "params": ["Person"],
                    "results": ["Person"],
                }
            ],
        }
    )
    assert schema is not None

    types = make_package_types(schema=schema, pkg="example.com/p")
    Person = types.Person

    p = Person(Name="x", Age=1, Data=b"x", Meta={"age": 1})
    enc = encode_value(schema=schema, pkg="example.com/p", v=p)
    assert enc == {"name": "x", "age": 1, "Data": b"x", "Meta": {"age": 1}}

    dec = decode_value(types=types, go_type="Person", v=enc)
    assert dec == p


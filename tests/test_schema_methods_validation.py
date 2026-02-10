from __future__ import annotations

import pytest


def test_schema_methods_roundtrip_and_validation():
    from usegolib.schema import (
        Schema,
        UnsupportedTypeError,
        validate_method_args,
        validate_method_result,
        validate_struct_value,
    )

    manifest_schema = {
        "structs": {
            "example.com/mod": {
                "Counter": [
                    {
                        "name": "N",
                        "type": "int64",
                        "key": "n",
                        "aliases": ["N", "n"],
                        "omitempty": False,
                        "embedded": False,
                        "required": True,
                    }
                ]
            }
        },
        "symbols": [],
        "methods": [
            {
                "pkg": "example.com/mod",
                "recv": "Counter",
                "name": "Inc",
                "params": ["int64"],
                "results": ["int64"],
            }
        ],
    }

    schema = Schema.from_manifest(manifest_schema)
    assert schema is not None

    validate_struct_value(schema=schema, pkg="example.com/mod", struct="Counter", value={"n": 1})

    validate_method_args(schema=schema, pkg="example.com/mod", recv="Counter", method="Inc", args=[1])
    validate_method_result(schema=schema, pkg="example.com/mod", recv="Counter", method="Inc", result=2)

    with pytest.raises(UnsupportedTypeError):
        validate_method_args(schema=schema, pkg="example.com/mod", recv="Counter", method="Inc", args=["x"])


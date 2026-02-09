from __future__ import annotations

import pytest

from usegolib.errors import UnsupportedTypeError
from usegolib.schema import Schema, validate_call_args


def test_schema_validation_accepts_uuid_uuid_as_string():
    schema = Schema.from_manifest(
        {
            "structs": {},
            "symbols": [
                {
                    "pkg": "example.com/p",
                    "name": "EchoUUID",
                    "params": ["uuid.UUID"],
                    "results": ["uuid.UUID"],
                }
            ],
        }
    )
    assert schema is not None

    validate_call_args(
        schema=schema, pkg="example.com/p", fn="EchoUUID", args=["123e4567-e89b-12d3-a456-426614174000"]
    )
    with pytest.raises(UnsupportedTypeError, match=r"expected UUID string"):
        validate_call_args(schema=schema, pkg="example.com/p", fn="EchoUUID", args=[123])


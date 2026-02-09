from __future__ import annotations

import pytest

from usegolib.errors import UnsupportedTypeError
from usegolib.schema import Schema, validate_call_args


def test_schema_validation_rejects_missing_required_fields():
    schema = Schema.from_manifest(
        {
            "structs": {
                "example.com/p": {
                    "Person": [
                        {"name": "Name", "type": "string"},
                        {"name": "Age", "type": "int64"},
                        {"name": "Nick", "type": "string", "key": "nick", "omitempty": True},
                    ]
                }
            },
            "symbols": [
                {"pkg": "example.com/p", "name": "IsAdult", "params": ["Person"], "results": ["bool"]}
            ],
        }
    )
    assert schema is not None

    # Missing required Age should be rejected.
    with pytest.raises(UnsupportedTypeError, match=r"missing required field"):
        validate_call_args(schema=schema, pkg="example.com/p", fn="IsAdult", args=[{"Name": "x"}])

    # Omitempty fields are optional.
    validate_call_args(schema=schema, pkg="example.com/p", fn="IsAdult", args=[{"Name": "x", "Age": 18}])


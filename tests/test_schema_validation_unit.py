from __future__ import annotations

import pytest

from usegolib.errors import UnsupportedTypeError
from usegolib.schema import (
    Schema,
    validate_call_args,
    validate_call_result,
    validate_method_result,
)


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


def test_schema_allows_opaque_pointer_handles_as_int_ids():
    schema = Schema.from_manifest(
        {
            "structs": {"example.com/p": {"Opaque": []}},
            "symbols": [{"pkg": "example.com/p", "name": "NewOpaque", "params": [], "results": ["*Opaque"]}],
            "methods": [{"pkg": "example.com/p", "recv": "Opaque", "name": "Self", "params": [], "results": ["*Opaque"]}],
        }
    )

    validate_call_result(schema=schema, pkg="example.com/p", fn="NewOpaque", result=1)
    validate_method_result(schema=schema, pkg="example.com/p", recv="Opaque", method="Self", result=2)


def test_schema_error_only_result_is_nil():
    schema = Schema.from_manifest(
        {
            "structs": {"example.com/p": {}},
            "symbols": [{"pkg": "example.com/p", "name": "Do", "params": [], "results": ["error"]}],
        }
    )

    validate_call_result(schema=schema, pkg="example.com/p", fn="Do", result=None)

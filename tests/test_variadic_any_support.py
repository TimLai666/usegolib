from __future__ import annotations


def test_pack_variadic_args():
    from usegolib.handle import _pack_variadic_args

    assert _pack_variadic_args(params=["...any"], args=[]) == [[]]
    assert _pack_variadic_args(params=["...any"], args=[1, 2]) == [[1, 2]]
    assert _pack_variadic_args(params=["int64", "...any"], args=[1]) == [1, []]
    assert _pack_variadic_args(params=["int64", "...any"], args=[1, 2, 3]) == [1, [2, 3]]
    assert _pack_variadic_args(params=["int64", "...any"], args=[1, [2, 3]]) == [1, [2, 3]]


def test_schema_accepts_any_and_variadic():
    from usegolib.schema import Schema, validate_call_args

    schema = Schema.from_manifest(
        {
            "structs": {},
            "symbols": [
                {"pkg": "example.com/p", "name": "VarAny", "params": ["...any"], "results": []},
                {"pkg": "example.com/p", "name": "EchoAny", "params": ["any"], "results": ["any"]},
                {"pkg": "example.com/p", "name": "EchoAnySlice", "params": ["[]any"], "results": ["[]any"]},
                {
                    "pkg": "example.com/p",
                    "name": "EchoAnyMap",
                    "params": ["map[string]any"],
                    "results": ["map[string]any"],
                },
            ],
            "methods": [],
            "generics": [],
        }
    )
    assert schema is not None

    validate_call_args(schema=schema, pkg="example.com/p", fn="VarAny", args=[[]])
    validate_call_args(schema=schema, pkg="example.com/p", fn="VarAny", args=[[1, "x", {"k": 1}]])

    validate_call_args(schema=schema, pkg="example.com/p", fn="EchoAny", args=[{"k": 1}])
    validate_call_args(schema=schema, pkg="example.com/p", fn="EchoAnySlice", args=[[1, {"k": 1}]])
    validate_call_args(schema=schema, pkg="example.com/p", fn="EchoAnyMap", args=[{"k": 1, "x": [1, 2]}])


from __future__ import annotations

import pytest

from usegolib.handle import GoObject, PackageHandle, TypedGoObject, TypedPackageHandle
from usegolib.schema import Schema


class _DummyClient:
    def call(self, req: bytes) -> bytes:  # noqa: ARG002
        raise RuntimeError("not used")


def test_runtime_attaches_godoc_and_signature_to_function_callables():
    schema = Schema.from_manifest(
        {
            "structs": {"example.com/p": {}},
            "symbols": [
                {
                    "pkg": "example.com/p",
                    "name": "Add",
                    "params": ["int64", "int64"],
                    "results": ["int64"],
                    "doc": "Add returns a+b.",
                },
                {"pkg": "example.com/p", "name": "NoDoc", "params": [], "results": ["int64"]},
            ],
            "methods": [],
            "generics": [],
        }
    )
    assert schema is not None
    h = PackageHandle(
        module="example.com/p",
        version="v0.0.0",
        abi_version=0,
        package="example.com/p",
        _client=_DummyClient(),  # type: ignore[arg-type]
        _schema=schema,
    )

    f = h.Add
    assert f.__doc__ is not None
    assert "Add returns a+b." in f.__doc__
    assert "Go:" in f.__doc__

    g = h.NoDoc
    assert g.__doc__ is not None
    assert g.__doc__.startswith("Go:")


def test_runtime_attaches_godoc_and_signature_to_method_callables():
    schema = Schema.from_manifest(
        {
            "structs": {"example.com/p": {"T": []}},
            "symbols": [],
            "methods": [
                {
                    "pkg": "example.com/p",
                    "recv": "T",
                    "name": "M",
                    "params": ["int64"],
                    "results": [],
                    "doc": "M does a thing.",
                },
                {"pkg": "example.com/p", "recv": "T", "name": "NoDoc", "params": [], "results": ["int64"]},
            ],
            "generics": [],
        }
    )
    assert schema is not None
    h = PackageHandle(
        module="example.com/p",
        version="v0.0.0",
        abi_version=0,
        package="example.com/p",
        _client=_DummyClient(),  # type: ignore[arg-type]
        _schema=schema,
    )

    obj = GoObject(_pkg=h, _type="T", _id=1)
    m = obj.M
    assert m.__doc__ is not None
    assert "M does a thing." in m.__doc__
    assert "Go:" in m.__doc__

    nd = obj.NoDoc
    assert nd.__doc__ is not None
    assert nd.__doc__.startswith("Go:")


def test_typed_wrappers_preserve_docstrings():
    schema = Schema.from_manifest(
        {
            "structs": {"example.com/p": {"T": []}},
            "symbols": [{"pkg": "example.com/p", "name": "NoDoc", "params": [], "results": ["int64"]}],
            "methods": [{"pkg": "example.com/p", "recv": "T", "name": "NoDoc", "params": [], "results": ["int64"]}],
            "generics": [],
        }
    )
    assert schema is not None
    h = PackageHandle(
        module="example.com/p",
        version="v0.0.0",
        abi_version=0,
        package="example.com/p",
        _client=_DummyClient(),  # type: ignore[arg-type]
        _schema=schema,
    )

    th = TypedPackageHandle(h)
    assert isinstance(th.NoDoc.__doc__, str)
    assert th.NoDoc.__doc__.startswith("Go:")

    obj = GoObject(_pkg=h, _type="T", _id=1)
    tobj = TypedGoObject(_base=obj, _types=th.types, _schema=schema, _pkg="example.com/p")
    assert isinstance(tobj.NoDoc.__doc__, str)
    assert tobj.NoDoc.__doc__.startswith("Go:")


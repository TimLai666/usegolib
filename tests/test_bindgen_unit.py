from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from usegolib.bindgen import BindgenOptions, generate_python_bindings
from usegolib.schema import Schema


def _import_from_path(path: Path):
    spec = importlib.util.spec_from_file_location("usegolib_bindings_test", path)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def test_bindgen_generates_importable_module(tmp_path: Path):
    schema = Schema.from_manifest(
        {
            "structs": {
                "example.com/p": {
                    "Person": [
                        {"name": "Name", "type": "string", "key": "name", "required": True},
                        {"name": "Age", "type": "int64", "key": "age", "required": True},
                        {"name": "ID", "type": "*uuid.UUID", "key": "id", "required": False, "omitempty": True},
                    ]
                }
            },
            "symbols": [
                {
                    "pkg": "example.com/p",
                    "name": "EchoPerson",
                    "params": ["Person"],
                    "results": ["Person"],
                },
                {
                    "pkg": "example.com/p",
                    "name": "Pair",
                    "params": [],
                    "results": ["int64", "string"],
                },
            ],
        }
    )
    assert schema is not None

    out = tmp_path / "bindings.py"
    generate_python_bindings(
        schema=schema,
        pkg="example.com/p",
        out_file=out,
        opts=BindgenOptions(package="example.com/p"),
    )
    mod = _import_from_path(out)
    assert hasattr(mod, "Person")
    assert hasattr(mod, "API")
    assert getattr(mod.API.Pair, "__annotations__", {}).get("return") == "tuple[int, str]"

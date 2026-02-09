from __future__ import annotations

from dataclasses import MISSING, dataclass, fields, is_dataclass, make_dataclass
from typing import Any, Optional, TypeVar

from .schema import Schema, _parse_type

T = TypeVar("T")


def _py_type_for_go(schema: Schema, pkg: str, go_type: str) -> Any:
    base, ops = _parse_type(go_type)

    # Stdlib adapters.
    if base == "time.Time":
        ty: Any = str
    elif base == "time.Duration":
        ty = int
    elif base == "uuid.UUID":
        ty = str
    elif base == "[]byte":
        ty = bytes
        ops = []  # treat as scalar
    elif base in {"bool"}:
        ty = bool
    elif base in {"string"}:
        ty = str
    elif base in {"float32", "float64"}:
        ty = float
    elif base in {"int", "int8", "int16", "int32", "int64"}:
        ty = int
    elif base in schema.structs_by_pkg.get(pkg, {}):
        # Forward reference to struct dataclass name.
        ty = base
    else:
        ty = Any

    for op in reversed(ops):
        if op == "*":
            ty = Optional[ty]
        elif op == "[]":
            ty = list[ty]  # type: ignore[valid-type]
        elif op == "map[string]":
            ty = dict[str, ty]  # type: ignore[valid-type]
        else:
            ty = Any
    return ty


@dataclass(frozen=True)
class PackageTypes:
    pkg: str
    schema: Schema
    structs: dict[str, type]

    def __getattr__(self, name: str) -> type:
        try:
            return self.structs[name]
        except KeyError:
            raise AttributeError(name) from None


def make_package_types(*, schema: Schema, pkg: str) -> PackageTypes:
    by_name = schema.structs_by_pkg.get(pkg, {})

    # Create shells first so forward references can resolve via globals later.
    created: dict[str, type] = {}

    # First pass: build field specs using forward refs (strings) for nested structs.
    for struct_name, st in by_name.items():
        required_fields: list[tuple] = []
        optional_fields: list[tuple] = []
        for go_field_name, fs in st.fields_by_name.items():
            py_t = _py_type_for_go(schema, pkg, fs.type)
            meta = {"key": fs.key, "omitempty": fs.omitempty, "go_type": fs.type}
            if fs.required:
                required_fields.append((go_field_name, py_t, dataclass_field(meta)))
            else:
                optional_fields.append((go_field_name, py_t, dataclass_field(meta, default=None)))
        # dataclasses require non-default fields before default fields
        specs = required_fields + optional_fields
        cls = make_dataclass(struct_name, specs, frozen=True)
        # Marker for runtime encoding/decoding.
        setattr(cls, "__usegolib_pkg__", pkg)
        setattr(cls, "__usegolib_struct__", struct_name)
        created[struct_name] = cls

    return PackageTypes(pkg=pkg, schema=schema, structs=created)


def dataclass_field(meta: dict[str, Any], *, default: Any = MISSING):
    # Small wrapper so we can attach per-field metadata.
    from dataclasses import field as dc_field

    if default is MISSING:
        return dc_field(metadata=meta)
    return dc_field(default=default, metadata=meta)


def encode_value(*, schema: Schema, pkg: str, v: Any) -> Any:
    """Encode generated dataclasses into record-struct dicts (recursively)."""
    if is_dataclass(v) and hasattr(v, "__usegolib_pkg__") and hasattr(v, "__usegolib_struct__"):
        if getattr(v, "__usegolib_pkg__") != pkg:
            # Cross-package struct values are not supported in v0.
            return v
        struct_name = getattr(v, "__usegolib_struct__")
        st = schema.structs_by_pkg.get(pkg, {}).get(struct_name)
        if st is None:
            return v
        out: dict[str, Any] = {}
        for f in fields(v):
            go_field_name = f.name
            fs = st.fields_by_name.get(go_field_name)
            if fs is None:
                continue
            val = getattr(v, go_field_name)
            if val is None and (not fs.required):
                # Optional field omitted.
                continue
            out[fs.key] = encode_value(schema=schema, pkg=pkg, v=val)
        return out

    if isinstance(v, (list, tuple)):
        return [encode_value(schema=schema, pkg=pkg, v=item) for item in v]
    if isinstance(v, dict):
        return {k: encode_value(schema=schema, pkg=pkg, v=vv) for k, vv in v.items()}
    return v


def decode_value(*, types: PackageTypes, go_type: str, v: Any) -> Any:
    """Decode record-struct values into generated dataclasses (recursively)."""
    schema = types.schema
    pkg = types.pkg
    base, ops = _parse_type(go_type)

    # Apply container ops outer-to-inner.
    if ops and ops[0] == "*":
        if v is None:
            return None
        return decode_value(types=types, go_type=go_type[1:].strip(), v=v)
    if ops and ops[0] == "[]":
        inner = go_type[2:].strip()
        if not isinstance(v, list):
            return v
        return [decode_value(types=types, go_type=inner, v=item) for item in v]
    if ops and ops[0] == "map[string]":
        inner = go_type[len("map[string]") :].strip()
        if not isinstance(v, dict):
            return v
        return {k: decode_value(types=types, go_type=inner, v=vv) for k, vv in v.items()}

    # Scalar adapters or plain scalars: return as-is.
    if base in {
        "bool",
        "string",
        "int",
        "int8",
        "int16",
        "int32",
        "int64",
        "float32",
        "float64",
        "[]byte",
        "time.Time",
        "time.Duration",
        "uuid.UUID",
    }:
        return v

    st = schema.structs_by_pkg.get(pkg, {}).get(base)
    cls = types.structs.get(base)
    if st is None or cls is None or not isinstance(v, dict):
        return v

    values_by_name: dict[str, Any] = {}
    for k, vv in v.items():
        if not isinstance(k, str):
            continue
        go_field_name = st.key_to_name.get(k)
        if go_field_name is None:
            continue
        fs = st.fields_by_name.get(go_field_name)
        if fs is None:
            continue
        values_by_name[go_field_name] = decode_value(types=types, go_type=fs.type, v=vv)

    # Fill missing optional fields with None.
    for go_field_name, fs in st.fields_by_name.items():
        if go_field_name not in values_by_name:
            if fs.required:
                raise ValueError(f"missing required field {go_field_name}")
            values_by_name[go_field_name] = None

    return cls(**values_by_name)

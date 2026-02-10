from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import UnsupportedTypeError


_INT_RANGES = {
    "int8": (-(2**7), 2**7 - 1),
    "int16": (-(2**15), 2**15 - 1),
    "int32": (-(2**31), 2**31 - 1),
    "int64": (-(2**63), 2**63 - 1),
    # Treat `int` as 64-bit (CI targets include amd64; this matches our ABI intents for v0).
    "int": (-(2**63), 2**63 - 1),
}


def _split_prefix(t: str) -> tuple[str, str]:
    t = t.strip()
    if t.startswith("*"):
        return "*", t[1:].strip()
    if t.startswith("..."):
        return "...", t[3:].strip()
    if t.startswith("[]"):
        return "[]", t[2:].strip()
    if t.startswith("map[string]"):
        return "map[string]", t[len("map[string]") :].strip()
    return "", t


def _parse_type(t: str) -> tuple[str, list[str]]:
    t = t.strip()
    ops: list[str] = []
    while True:
        p, rest = _split_prefix(t)
        if not p:
            return rest, ops
        ops.append(p)
        t = rest


@dataclass(frozen=True)
class StructSchema:
    # key/alias -> goFieldName
    key_to_name: dict[str, str]

    # goFieldName -> field metadata
    fields_by_name: dict[str, "FieldSchema"]


@dataclass(frozen=True)
class FieldSchema:
    type: str
    required: bool
    key: str
    omitempty: bool


@dataclass(frozen=True)
class Schema:
    # pkg -> structName -> schema
    structs_by_pkg: dict[str, dict[str, StructSchema]]
    symbols_by_pkg: dict[str, dict[str, tuple[list[str], list[str]]]]
    symbol_docs_by_pkg: dict[str, dict[str, str]]
    # pkg -> recvType -> methodName -> (params, results)
    methods_by_pkg: dict[str, dict[str, dict[str, tuple[list[str], list[str]]]]]
    method_docs_by_pkg: dict[str, dict[str, dict[str, str]]]
    # pkg -> genericName -> typeArgsTuple -> concreteSymbolName
    generics_by_pkg: dict[str, dict[str, dict[tuple[str, ...], str]]]
    generic_docs_by_pkg: dict[str, dict[str, str]]
    vars_by_pkg: dict[str, dict[str, str]]
    var_docs_by_pkg: dict[str, dict[str, str]]

    @classmethod
    def from_manifest(cls, manifest_schema: dict[str, Any] | None) -> "Schema | None":
        if not manifest_schema:
            return None
        structs: dict[str, dict[str, StructSchema]] = {}
        raw_structs = manifest_schema.get("structs")
        if isinstance(raw_structs, dict):
            for pkg, by_name in raw_structs.items():
                if not isinstance(pkg, str) or not isinstance(by_name, dict):
                    continue
                pkg_out: dict[str, StructSchema] = {}
                for name, fields in by_name.items():
                    if not isinstance(name, str) or not isinstance(fields, list):
                        continue
                    key_to_name: dict[str, str] = {}
                    fields_by_name: dict[str, tuple[str, bool]] = {}
                    if not fields:
                        # Allow empty struct schemas to represent "opaque" structs that
                        # have no exported fields. This prevents runtime validation from
                        # failing with "unknown type" for fluent APIs that return `*T`.
                        pkg_out[name] = StructSchema(key_to_name={}, fields_by_name={})
                        continue
                    for f in fields:
                        if not isinstance(f, dict):
                            continue
                        fn = f.get("name")
                        ft = f.get("type")
                        fk = f.get("key")
                        fa = f.get("aliases")
                        fr = f.get("required")
                        fo = f.get("omitempty")
                        fe = f.get("embedded")
                        if not (isinstance(fn, str) and isinstance(ft, str) and fn and ft):
                            continue
                        key = fk if isinstance(fk, str) and fk else fn
                        aliases: list[str] = []
                        if isinstance(fa, list) and all(isinstance(x, str) for x in fa):
                            aliases = [x for x in fa if x]

                        omitempty = bool(fo) if isinstance(fo, bool) else False
                        embedded = bool(fe) if isinstance(fe, bool) else False
                        if isinstance(fr, bool):
                            required = fr
                        else:
                            required = not ft.strip().startswith("*")
                        if omitempty:
                            required = False
                        fields_by_name[fn] = FieldSchema(
                            type=ft, required=required, key=key, omitempty=omitempty
                        )

                        # Always accept exported field name and canonical key.
                        all_keys = {fn, key, *aliases}
                        for k in all_keys:
                            if not k:
                                continue
                            existing = key_to_name.get(k)
                            if existing is not None and existing != fn:
                                # Ambiguous alias; drop it rather than picking a wrong field.
                                continue
                            key_to_name[k] = fn

                    if key_to_name and fields_by_name:
                        pkg_out[name] = StructSchema(key_to_name=key_to_name, fields_by_name=fields_by_name)
                if pkg_out:
                    structs[pkg] = pkg_out

        symbols_by_pkg: dict[str, dict[str, tuple[list[str], list[str]]]] = {}
        symbol_docs_by_pkg: dict[str, dict[str, str]] = {}
        raw_symbols = manifest_schema.get("symbols")
        if isinstance(raw_symbols, list):
            for s in raw_symbols:
                if not isinstance(s, dict):
                    continue
                pkg = s.get("pkg")
                name = s.get("name")
                params = s.get("params")
                results = s.get("results")
                doc = s.get("doc")
                if not isinstance(pkg, str) or not isinstance(name, str):
                    continue
                if not isinstance(params, list) or not isinstance(results, list):
                    continue
                if not all(isinstance(x, str) for x in params) or not all(
                    isinstance(x, str) for x in results
                ):
                    continue
                symbols_by_pkg.setdefault(pkg, {})[name] = (list(params), list(results))
                if isinstance(doc, str) and doc.strip():
                    symbol_docs_by_pkg.setdefault(pkg, {})[name] = doc.strip()

        methods_by_pkg: dict[str, dict[str, dict[str, tuple[list[str], list[str]]]]] = {}
        method_docs_by_pkg: dict[str, dict[str, dict[str, str]]] = {}
        raw_methods = manifest_schema.get("methods")
        if isinstance(raw_methods, list):
            for m in raw_methods:
                if not isinstance(m, dict):
                    continue
                pkg = m.get("pkg")
                recv = m.get("recv")
                name = m.get("name")
                params = m.get("params")
                results = m.get("results")
                doc = m.get("doc")
                if not (isinstance(pkg, str) and isinstance(recv, str) and isinstance(name, str)):
                    continue
                if not isinstance(params, list) or not isinstance(results, list):
                    continue
                if not all(isinstance(x, str) for x in params) or not all(
                    isinstance(x, str) for x in results
                ):
                    continue
                methods_by_pkg.setdefault(pkg, {}).setdefault(recv, {})[name] = (
                    list(params),
                    list(results),
                )
                if isinstance(doc, str) and doc.strip():
                    method_docs_by_pkg.setdefault(pkg, {}).setdefault(recv, {})[name] = doc.strip()

        generics_by_pkg: dict[str, dict[str, dict[tuple[str, ...], str]]] = {}
        generic_docs_by_pkg: dict[str, dict[str, str]] = {}
        raw_generics = manifest_schema.get("generics")
        if isinstance(raw_generics, list):
            for g in raw_generics:
                if not isinstance(g, dict):
                    continue
                pkg = g.get("pkg")
                name = g.get("name")
                type_args = g.get("type_args")
                symbol = g.get("symbol")
                doc = g.get("doc")
                if not (isinstance(pkg, str) and isinstance(name, str) and isinstance(symbol, str)):
                    continue
                if not isinstance(type_args, list) or not all(isinstance(x, str) for x in type_args):
                    continue
                generics_by_pkg.setdefault(pkg, {}).setdefault(name, {})[tuple(type_args)] = symbol
                if isinstance(doc, str) and doc.strip():
                    generic_docs_by_pkg.setdefault(pkg, {})[name] = doc.strip()

        vars_by_pkg: dict[str, dict[str, str]] = {}
        var_docs_by_pkg: dict[str, dict[str, str]] = {}
        raw_vars = manifest_schema.get("vars")
        if isinstance(raw_vars, list):
            for v in raw_vars:
                if not isinstance(v, dict):
                    continue
                pkg = v.get("pkg")
                name = v.get("name")
                typ = v.get("type")
                doc = v.get("doc")
                if not (isinstance(pkg, str) and isinstance(name, str) and isinstance(typ, str)):
                    continue
                if not pkg or not name or not typ:
                    continue
                base = typ.strip()
                if base.startswith("*"):
                    base = base[1:].strip()
                if base:
                    vars_by_pkg.setdefault(pkg, {})[name] = base
                if isinstance(doc, str) and doc.strip():
                    var_docs_by_pkg.setdefault(pkg, {})[name] = doc.strip()

        return cls(
            structs_by_pkg=structs,
            symbols_by_pkg=symbols_by_pkg,
            symbol_docs_by_pkg=symbol_docs_by_pkg,
            methods_by_pkg=methods_by_pkg,
            method_docs_by_pkg=method_docs_by_pkg,
            generics_by_pkg=generics_by_pkg,
            generic_docs_by_pkg=generic_docs_by_pkg,
            vars_by_pkg=vars_by_pkg,
            var_docs_by_pkg=var_docs_by_pkg,
        )


def validate_struct_value(*, schema: Schema, pkg: str, struct: str, value: Any) -> None:
    try:
        _validate_value(schema=schema, pkg=pkg, t=struct, v=value)
    except UnsupportedTypeError as e:
        raise UnsupportedTypeError(f"schema: {struct}: {e}") from None


def validate_call_args(*, schema: Schema, pkg: str, fn: str, args: list[Any]) -> None:
    sig = schema.symbols_by_pkg.get(pkg, {}).get(fn)
    if sig is None:
        return
    params, _results = sig
    if len(args) != len(params):
        raise UnsupportedTypeError(f"schema: wrong arity (expected {len(params)}, got {len(args)})")
    for i, (t, v) in enumerate(zip(params, args, strict=True)):
        try:
            _validate_value(schema=schema, pkg=pkg, t=t, v=v)
        except UnsupportedTypeError as e:
            raise UnsupportedTypeError(f"schema: arg{i} ({t}): {e}") from None


def validate_call_result(*, schema: Schema, pkg: str, fn: str, result: Any) -> None:
    sig = schema.symbols_by_pkg.get(pkg, {}).get(fn)
    if sig is None:
        return
    _params, results = sig
    if not results:
        if result is not None:
            raise UnsupportedTypeError("schema: expected nil result")
        return
    # (T, error) is represented as a single successful result in the ABI.
    t0 = results[0]
    try:
        _validate_value(schema=schema, pkg=pkg, t=t0, v=result)
    except UnsupportedTypeError as e:
        raise UnsupportedTypeError(f"schema: result ({t0}): {e}") from None


def validate_method_args(
    *, schema: Schema, pkg: str, recv: str, method: str, args: list[Any]
) -> None:
    sig = schema.methods_by_pkg.get(pkg, {}).get(recv, {}).get(method)
    if sig is None:
        return
    params, _results = sig
    if len(args) != len(params):
        raise UnsupportedTypeError(f"schema: wrong arity (expected {len(params)}, got {len(args)})")
    for i, (t, v) in enumerate(zip(params, args, strict=True)):
        try:
            _validate_value(schema=schema, pkg=pkg, t=t, v=v)
        except UnsupportedTypeError as e:
            raise UnsupportedTypeError(f"schema: arg{i} ({t}): {e}") from None


def validate_method_result(
    *, schema: Schema, pkg: str, recv: str, method: str, result: Any
) -> None:
    sig = schema.methods_by_pkg.get(pkg, {}).get(recv, {}).get(method)
    if sig is None:
        return
    _params, results = sig
    if not results:
        if result is not None:
            raise UnsupportedTypeError("schema: expected nil result")
        return
    t0 = results[0]
    try:
        _validate_value(schema=schema, pkg=pkg, t=t0, v=result)
    except UnsupportedTypeError as e:
        raise UnsupportedTypeError(f"schema: result ({t0}): {e}") from None


def _validate_value(*, schema: Schema, pkg: str, t: str, v: Any) -> None:
    t = t.strip()

    if t == "any":
        return
    if t == "error":
        # For v0 we represent successful `error` results as nil. Non-nil errors
        # are reported via the ABI error envelope instead of as values.
        if v is not None:
            raise UnsupportedTypeError("expected nil")
        return

    # Special-case `[]byte`: represented as bytes, not list[int].
    if t == "[]byte":
        if not isinstance(v, (bytes, bytearray)):
            raise UnsupportedTypeError("expected bytes")
        return
    if t == "time.Time":
        if not isinstance(v, str):
            raise UnsupportedTypeError("expected RFC3339 string")
        return
    if t == "time.Duration":
        if not isinstance(v, int) or isinstance(v, bool):
            raise UnsupportedTypeError("expected int (nanoseconds)")
        lo, hi = _INT_RANGES["int64"]
        if v < lo or v > hi:
            raise UnsupportedTypeError("int out of range")
        return
    if t == "uuid.UUID":
        if not isinstance(v, str):
            raise UnsupportedTypeError("expected UUID string")
        return

    if t.startswith("*"):
        if v is None:
            return
        inner = t[1:].strip()
        # Opaque pointer handles: if the pointed-to struct exists in schema but has
        # no exported fields, allow passing/returning a uint64-ish object id (int).
        st = schema.structs_by_pkg.get(pkg, {}).get(inner)
        if st is not None and not st.fields_by_name:
            if isinstance(v, int) and not isinstance(v, bool):
                return
        _validate_value(schema=schema, pkg=pkg, t=inner, v=v)
        return

    if t.startswith("..."):
        if not isinstance(v, (list, tuple)):
            raise UnsupportedTypeError("expected list")
        inner = t[3:].strip()
        for item in v:
            _validate_value(schema=schema, pkg=pkg, t=inner, v=item)
        return

    if t.startswith("[]"):
        if not isinstance(v, (list, tuple)):
            raise UnsupportedTypeError("expected list")
        inner = t[2:].strip()
        for item in v:
            _validate_value(schema=schema, pkg=pkg, t=inner, v=item)
        return

    if t.startswith("map[string]"):
        if not isinstance(v, dict):
            raise UnsupportedTypeError("expected dict")
        if not all(isinstance(k, str) for k in v.keys()):
            raise UnsupportedTypeError("expected dict with str keys")
        inner = t[len("map[string]") :].strip()
        for vv in v.values():
            _validate_value(schema=schema, pkg=pkg, t=inner, v=vv)
        return

    # Scalars
    if t == "bool":
        if not isinstance(v, bool):
            raise UnsupportedTypeError("expected bool")
        return
    if t == "string":
        if not isinstance(v, str):
            raise UnsupportedTypeError("expected str")
        return
    if t in _INT_RANGES:
        if not isinstance(v, int) or isinstance(v, bool):
            raise UnsupportedTypeError("expected int")
        lo, hi = _INT_RANGES[t]
        if v < lo or v > hi:
            raise UnsupportedTypeError("int out of range")
        return
    if t in {"float64", "float32"}:
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise UnsupportedTypeError("expected float")
        return

    # Struct (record)
    st = schema.structs_by_pkg.get(pkg, {}).get(t)
    if st is None:
        raise UnsupportedTypeError("unknown type")
    if v is None:
        raise UnsupportedTypeError("expected dict")
    if not isinstance(v, dict):
        raise UnsupportedTypeError("expected dict")
    seen_fields: set[str] = set()
    for k in v.keys():
        if not isinstance(k, str):
            raise UnsupportedTypeError("expected str keys")
        if k not in st.key_to_name:
            raise UnsupportedTypeError(f"unknown field {k}")
    for k, vv in v.items():
        field_name = st.key_to_name[k]
        field_type = st.fields_by_name[field_name].type
        if field_name in seen_fields:
            raise UnsupportedTypeError(f"duplicate field {field_name}")
        seen_fields.add(field_name)
        try:
            _validate_value(schema=schema, pkg=pkg, t=field_type, v=vv)
        except UnsupportedTypeError as e:
            raise UnsupportedTypeError(f"field {k} ({field_type}): {e}") from None

    missing = sorted(
        name for name, fs in st.fields_by_name.items() if fs.required and name not in seen_fields
    )
    if missing:
        raise UnsupportedTypeError(f"missing required field(s): {', '.join(missing)}")

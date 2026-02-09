from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import Schema, _parse_type


@dataclass(frozen=True)
class BindgenOptions:
    package: str
    module_name: str = "usegolib_bindings"
    api_class_name: str = "API"


def _py_type_expr(*, schema: Schema, pkg: str, go_type: str) -> str:
    base, ops = _parse_type(go_type)

    # Stdlib adapters.
    if base in {"time.Time", "uuid.UUID", "string"}:
        expr = "str"
    elif base == "time.Duration":
        expr = "int"
    elif base == "[]byte":
        expr = "bytes"
        ops = []  # treat as scalar
    elif base == "bool":
        expr = "bool"
    elif base in {"float32", "float64"}:
        expr = "float"
    elif base in {"int", "int8", "int16", "int32", "int64"}:
        expr = "int"
    elif base in schema.structs_by_pkg.get(pkg, {}):
        expr = base
    else:
        expr = "Any"

    # ops are inner->outer in Schema parsing; rebuild outer wrappers.
    for op in reversed(ops):
        if op == "*":
            expr = f"{expr} | None"
        elif op == "[]":
            expr = f"list[{expr}]"
        elif op == "map[string]":
            expr = f"dict[str, {expr}]"
        else:
            expr = "Any"
    return expr


def generate_python_bindings(*, schema: Schema, pkg: str, out_file: Path, opts: BindgenOptions) -> None:
    """Generate a static Python module from manifest schema for a package."""
    structs = schema.structs_by_pkg.get(pkg, {})
    symbols = schema.symbols_by_pkg.get(pkg, {})
    if not symbols:
        raise ValueError(f"no symbols found for package {pkg}")

    lines: list[str] = []
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from dataclasses import dataclass")
    lines.append("from pathlib import Path")
    lines.append("from typing import Any")
    lines.append("")
    lines.append("import usegolib")
    lines.append("import usegolib.typed")
    lines.append("from usegolib.handle import PackageHandle")
    lines.append("")

    # Dataclasses for named structs
    for struct_name, st in structs.items():
        lines.append("@dataclass(frozen=True)")
        lines.append(f"class {struct_name}:")
        lines.append(f"    __usegolib_pkg__ = {pkg!r}")
        lines.append(f"    __usegolib_struct__ = {struct_name!r}")
        required_fields: list[tuple[str, Any]] = []
        optional_fields: list[tuple[str, Any]] = []
        for go_field_name, fs in st.fields_by_name.items():
            if fs.required:
                required_fields.append((go_field_name, fs))
            else:
                optional_fields.append((go_field_name, fs))

        for go_field_name, fs in required_fields:
            ty = _py_type_expr(schema=schema, pkg=pkg, go_type=fs.type)
            lines.append(f"    {go_field_name}: {ty}")
        for go_field_name, fs in optional_fields:
            ty = _py_type_expr(schema=schema, pkg=pkg, go_type=fs.type)
            if "None" not in ty:
                ty = f"{ty} | None"
            lines.append(f"    {go_field_name}: {ty} = None")
        if not st.fields_by_name:
            lines.append("    pass")
        lines.append("")

    # Build decode types mapping once.
    lines.append("_STRUCTS: dict[str, type] = {")
    for struct_name in structs.keys():
        lines.append(f"    {struct_name!r}: {struct_name},")
    lines.append("}")
    lines.append("")

    # API wrapper
    api = opts.api_class_name
    lines.append(f"class {api}:")
    lines.append("    def __init__(self, handle: PackageHandle):")
    lines.append("        if handle.schema is None:")
    lines.append('            raise RuntimeError("manifest schema is required")')
    lines.append("        self._h = handle")
    lines.append("        self._schema = handle.schema")
    lines.append(
        "        self._types = usegolib.typed.package_types_from_classes("
        "schema=self._schema, pkg=handle.package, structs=_STRUCTS)"
    )
    lines.append("")

    for fn_name, (params, results) in symbols.items():
        # (T, error) is represented as a single successful result.
        ret_go = "nil"
        if results:
            ret_go = results[0]
        ret_py = "None" if not results else _py_type_expr(schema=schema, pkg=pkg, go_type=ret_go)

        arg_parts: list[str] = []
        call_args: list[str] = []
        for i, t in enumerate(params):
            arg_name = f"arg{i}"
            arg_parts.append(f"{arg_name}: {_py_type_expr(schema=schema, pkg=pkg, go_type=t)}")
            call_args.append(arg_name)
        args_sig = ", ".join(["self", *arg_parts])
        lines.append(f"    def {fn_name}({args_sig}) -> {ret_py}:")
        lines.append(f"        r = self._h.{fn_name}({', '.join(call_args)})")
        if results:
            lines.append(
                f"        return usegolib.typed.decode_value(types=self._types, go_type={ret_go!r}, v=r)"
            )
        else:
            lines.append("        return None")
        lines.append("")

    # load() helper
    lines.append("def load(*, artifact_dir: str | Path, version: str | None = None) -> API:")
    lines.append(
        f"    h = usegolib.import_({pkg!r}, version=version, artifact_dir=artifact_dir)"
    )
    lines.append(f"    return {api}(h)")
    lines.append("")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(lines), encoding="utf-8")

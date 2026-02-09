from __future__ import annotations

from pathlib import Path

from .build import ExportedFunc


def write_bridge(*, bridge_dir: Path, module_path: str, functions: list[ExportedFunc]) -> None:
    # Generate a single `main` package for `-buildmode=c-shared`.
    imports: dict[str, str] = {}
    for fn in functions:
        if fn.pkg not in imports:
            alias = f"p{len(imports)}"
            imports[fn.pkg] = alias

    reg_lines: list[str] = []
    wrap_lines: list[str] = []

    for fn in functions:
        alias = imports[fn.pkg]
        key = f"{fn.pkg}:{fn.name}"
        wrap_name = f"wrap_{alias}_{fn.name}"

        reg_lines.append(f'        "{key}": {wrap_name},')
        wrap_lines.extend(_write_wrapper(wrap_name=wrap_name, alias=alias, fn=fn))
        wrap_lines.append("")

    src = "\n".join(
        [
            "package main",
            "",
            "/*",
            "#include <stdlib.h>",
            "*/",
            'import "C"',
            "",
            "import (",
            '    "unsafe"',
            "",
            '    "github.com/vmihailenco/msgpack/v5"',
            ")",
            "",
            "// Request is the MessagePack request envelope (ABI v0).",
            "type Request struct {",
            '    ABI int `msgpack:"abi"`',
            '    Op  string `msgpack:"op"`',
            '    Pkg string `msgpack:"pkg"`',
            '    Fn  string `msgpack:"fn"`',
            '    Args []any `msgpack:"args"`',
            "}",
            "",
            "type ErrorObj struct {",
            '    Type string `msgpack:"type"`',
            '    Message string `msgpack:"message"`',
            '    Detail map[string]any `msgpack:"detail,omitempty"`',
            "}",
            "",
            "type Response struct {",
            '    Ok bool `msgpack:"ok"`',
            '    Result any `msgpack:"result,omitempty"`',
            '    Error *ErrorObj `msgpack:"error,omitempty"`',
            "}",
            "",
            "type Handler func(args []any) (any, *ErrorObj)",
            "",
            "var dispatch = map[string]Handler{}",
            "",
            "func init() {",
            "    dispatch = map[string]Handler{",
            *reg_lines,
            "    }",
            "}",
            "",
            "func main() {}",
            "",
            "//export usegolib_call",
            "func usegolib_call(reqPtr unsafe.Pointer, reqLen C.size_t, respPtr **C.uchar, respLen *C.size_t) C.int {",
            "    reqBytes := C.GoBytes(reqPtr, C.int(reqLen))",
            "",
            "    var req Request",
            "    if err := msgpack.Unmarshal(reqBytes, &req); err != nil {",
            '        writeError(respPtr, respLen, "ABIDecodeError", err.Error(), nil)',
            "        return 0",
            "    }",
            "    if req.ABI != 0 {",
            '        writeError(respPtr, respLen, "UnsupportedABIVersion", "unsupported abi version", map[string]any{"abi": req.ABI})',
            "        return 0",
            "    }",
            '    if req.Op != "call" {',
            '        writeError(respPtr, respLen, "UnsupportedOperation", "unsupported op", map[string]any{"op": req.Op})',
            "        return 0",
            "    }",
            "",
            '    key := req.Pkg + ":" + req.Fn',
            "    h := dispatch[key]",
            "    if h == nil {",
            '        writeError(respPtr, respLen, "SymbolNotFound", "symbol not found", map[string]any{"pkg": req.Pkg, "fn": req.Fn})',
            "        return 0",
            "    }",
            "",
            "    var result any",
            "    var errObj *ErrorObj",
            "    func() {",
            "        defer func() {",
            "            if r := recover(); r != nil {",
            '                errObj = &ErrorObj{Type: "GoPanicError", Message: "panic"}',
            "            }",
            "        }()",
            "        result, errObj = h(req.Args)",
            "    }()",
            "",
            "    if errObj != nil {",
            "        writeResp(respPtr, respLen, &Response{Ok: false, Error: errObj})",
            "        return 0",
            "    }",
            "    writeResp(respPtr, respLen, &Response{Ok: true, Result: result})",
            "    return 0",
            "}",
            "",
            "func writeError(respPtr **C.uchar, respLen *C.size_t, typ string, msg string, detail map[string]any) {",
            "    writeResp(respPtr, respLen, &Response{Ok: false, Error: &ErrorObj{Type: typ, Message: msg, Detail: detail}})",
            "}",
            "",
            "func writeResp(respPtr **C.uchar, respLen *C.size_t, resp *Response) {",
            "    out, err := msgpack.Marshal(resp)",
            "    if err != nil {",
            "        // Last resort: return an empty response (caller will error).",
            "        *respPtr = nil",
            "        *respLen = 0",
            "        return",
            "    }",
            "    p := C.malloc(C.size_t(len(out)))",
            "    if p == nil {",
            "        *respPtr = nil",
            "        *respLen = 0",
            "        return",
            "    }",
            "    C.memcpy(p, unsafe.Pointer(&out[0]), C.size_t(len(out)))",
            "    *respPtr = (*C.uchar)(p)",
            "    *respLen = C.size_t(len(out))",
            "}",
            "",
            "//export usegolib_free",
            "func usegolib_free(p unsafe.Pointer) {",
            "    C.free(p)",
            "}",
        ]
    )

    # We need to insert Go imports for target packages; easiest is to regenerate
    # file with a proper import block.
    import_block = ["import (", '    "unsafe"', "", '    "github.com/vmihailenco/msgpack/v5"']
    for pkg, alias in imports.items():
        import_block.append(f'    {alias} "{pkg}"')
    import_block.append(")")

    src = src.replace(
        "import (\n    \"unsafe\"\n\n    \"github.com/vmihailenco/msgpack/v5\"\n)",
        "\n".join(import_block),
    )
    # Add missing C prototype for memcpy.
    src = src.replace(
        "#include <stdlib.h>",
        "#include <stdlib.h>\n#include <string.h>",
    )

    bridge_file = bridge_dir / "bridge_gen.go"
    helpers = _write_helpers()
    bridge_file.write_text(
        src + "\n" + "\n".join(wrap_lines) + "\n" + "\n".join(helpers) + "\n",
        encoding="utf-8",
    )


def _write_wrapper(*, wrap_name: str, alias: str, fn: ExportedFunc) -> list[str]:
    # Only support a small set of v0 types.
    lines: list[str] = []
    lines.append(f"func {wrap_name}(args []any) (any, *ErrorObj) {{")
    lines.append(f"    if len(args) != {len(fn.params)} {{")
    lines.append(
        '        return nil, &ErrorObj{Type: "ABIError", Message: "wrong arity"}'
    )
    lines.append("    }")

    arg_names: list[str] = []
    for i, t in enumerate(fn.params):
        vn = f"a{i}"
        arg_names.append(vn)
        lines.extend(_write_arg_convert(var_name=vn, go_type=t, value_expr=f"args[{i}]"))

    call = f"{alias}.{fn.name}({', '.join(arg_names)})"
    if len(fn.results) == 0:
        lines.append(f"    {call}")
        lines.append("    return nil, nil")
    elif len(fn.results) == 1:
        lines.append(f"    r0 := {call}")
        lines.append("    return r0, nil")
    else:
        # (T, error)
        lines.append(f"    r0, err := {call}")
        lines.append("    if err != nil {")
        lines.append('        return nil, &ErrorObj{Type: "GoError", Message: err.Error()}')
        lines.append("    }")
        lines.append("    return r0, nil")

    lines.append("}")
    return lines


def _conv_expr(go_type: str, v: str) -> str:
    raise AssertionError(f"unexpected: {_conv_expr.__name__} called for {go_type}/{v}")


def _write_arg_convert(*, var_name: str, go_type: str, value_expr: str) -> list[str]:
    lines: list[str] = []

    def unsupported() -> None:
        lines.append(
            '    return nil, &ErrorObj{Type: "UnsupportedTypeError", Message: "unsupported arg type"}'
        )

    if go_type.startswith("map[string]"):
        vt = go_type[len("map[string]") :]
        tmp = f"t_{var_name}"

        if vt == "int64":
            lines.append(f"    {var_name}, ok := toStringInt64Map({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            return lines

        if vt in {"int", "int32", "int16", "int8"}:
            lines.append(f"    {tmp}, ok := toStringInt64Map({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            lines.append(f"    {var_name} := make(map[string]{vt}, len({tmp}))")
            lines.append(f"    for k, x := range {tmp} {{")
            lines.append(f"        {var_name}[k] = {vt}(x)")
            lines.append("    }")
            return lines

        if vt == "float64":
            lines.append(f"    {var_name}, ok := toStringFloat64Map({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            return lines

        if vt == "float32":
            lines.append(f"    {tmp}, ok := toStringFloat64Map({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            lines.append(f"    {var_name} := make(map[string]float32, len({tmp}))")
            lines.append(f"    for k, x := range {tmp} {{")
            lines.append(f"        {var_name}[k] = float32(x)")
            lines.append("    }")
            return lines

        if vt == "string":
            lines.append(f"    {var_name}, ok := toStringStringMap({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            return lines

        if vt == "bool":
            lines.append(f"    {var_name}, ok := toStringBoolMap({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            return lines

        if vt == "[]byte":
            lines.append(f"    {var_name}, ok := toStringBytesMap({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            return lines

        if vt == "[]int64":
            lines.append(f"    {var_name}, ok := toStringInt64SliceMap({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            return lines

        if vt == "[]int":
            lines.append(f"    {tmp}, ok := toStringInt64SliceMap({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            lines.append(f"    {var_name} := make(map[string][]int, len({tmp}))")
            lines.append(f"    for k, xs := range {tmp} {{")
            lines.append("        out := make([]int, 0, len(xs))")
            lines.append("        for _, x := range xs {")
            lines.append("            out = append(out, int(x))")
            lines.append("        }")
            lines.append(f"        {var_name}[k] = out")
            lines.append("    }")
            return lines

        if vt == "[]float64":
            lines.append(f"    {var_name}, ok := toStringFloat64SliceMap({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            return lines

        if vt == "[]string":
            lines.append(f"    {var_name}, ok := toStringStringSliceMap({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            return lines

        if vt == "[]bool":
            lines.append(f"    {var_name}, ok := toStringBoolSliceMap({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            return lines

        if vt == "[][]byte":
            lines.append(f"    {var_name}, ok := toStringBytesSliceMap({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            return lines

        lines.append("    if true {")
        unsupported()
        lines.append("    }")
        return lines

    if go_type in {"int64", "int", "int32", "int16", "int8"}:
        tmp = f"t_{var_name}"
        lines.append(f"    {tmp}, ok := toInt64({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        cast = go_type
        lines.append(f"    {var_name} := {cast}({tmp})")
        return lines

    if go_type in {"float64", "float32"}:
        tmp = f"t_{var_name}"
        lines.append(f"    {tmp}, ok := toFloat64({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        lines.append(f"    {var_name} := {go_type}({tmp})")
        return lines

    if go_type == "string":
        lines.append(f"    {var_name}, ok := toString({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        return lines

    if go_type == "bool":
        lines.append(f"    {var_name}, ok := toBool({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        return lines

    if go_type == "[]byte":
        lines.append(f"    {var_name}, ok := toBytes({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        return lines

    if go_type == "[]float64":
        lines.append(f"    {var_name}, ok := toFloat64Slice({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        return lines

    if go_type == "[]int64":
        lines.append(f"    {var_name}, ok := toInt64Slice({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        return lines

    if go_type == "[]int":
        tmp = f"t_{var_name}"
        lines.append(f"    {tmp}, ok := toInt64Slice({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        lines.append(f"    {var_name} := make([]int, 0, len({tmp}))")
        lines.append(f"    for _, x := range {tmp} {{")
        lines.append(f"        {var_name} = append({var_name}, int(x))")
        lines.append("    }")
        return lines

    if go_type == "[]string":
        lines.append(f"    {var_name}, ok := toStringSlice({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        return lines

    if go_type == "[]bool":
        lines.append(f"    {var_name}, ok := toBoolSlice({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        return lines

    if go_type == "[][]byte":
        lines.append(f"    {var_name}, ok := toBytesSlice({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        return lines

    # Unknown type (should not happen due to filtering).
    lines.append("    if true {")
    unsupported()
    lines.append("    }")
    return lines


def _write_helpers() -> list[str]:
    return [
        "func toUnsupported(v any) (any, bool) {",
        "    _ = v",
        "    return nil, false",
        "}",
        "",
        "func toBool(v any) (bool, bool) {",
        "    b, ok := v.(bool)",
        "    return b, ok",
        "}",
        "",
        "func toString(v any) (string, bool) {",
        "    s, ok := v.(string)",
        "    return s, ok",
        "}",
        "",
        "func toBytes(v any) ([]byte, bool) {",
        "    b, ok := v.([]byte)",
        "    return b, ok",
        "}",
        "",
        "func toInt64(v any) (int64, bool) {",
        "    switch t := v.(type) {",
        "    case int64:",
        "        return t, true",
        "    case int32:",
        "        return int64(t), true",
        "    case int16:",
        "        return int64(t), true",
        "    case int8:",
        "        return int64(t), true",
        "    case int:",
        "        return int64(t), true",
        "    case uint64:",
        "        if t > uint64(^uint64(0)>>1) {",
        "            return 0, false",
        "        }",
        "        return int64(t), true",
        "    case uint32:",
        "        return int64(t), true",
        "    case uint16:",
        "        return int64(t), true",
        "    case uint8:",
        "        return int64(t), true",
        "    case uint:",
        "        return int64(t), true",
        "    default:",
        "        return 0, false",
        "    }",
        "}",
        "",
        "func toFloat64(v any) (float64, bool) {",
        "    switch t := v.(type) {",
        "    case float64:",
        "        return t, true",
        "    case float32:",
        "        return float64(t), true",
        "    case int64:",
        "        return float64(t), true",
        "    case int:",
        "        return float64(t), true",
        "    default:",
        "        return 0, false",
        "    }",
        "}",
        "",
        "func toFloat64Slice(v any) ([]float64, bool) {",
        "    xs, ok := toAnySlice(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make([]float64, 0, len(xs))",
        "    for _, item := range xs {",
        "        f, ok := toFloat64(item)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out = append(out, f)",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toInt64Slice(v any) ([]int64, bool) {",
        "    xs, ok := toAnySlice(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make([]int64, 0, len(xs))",
        "    for _, item := range xs {",
        "        n, ok := toInt64(item)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out = append(out, n)",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toStringSlice(v any) ([]string, bool) {",
        "    xs, ok := toAnySlice(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make([]string, 0, len(xs))",
        "    for _, item := range xs {",
        "        s, ok := toString(item)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out = append(out, s)",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toBoolSlice(v any) ([]bool, bool) {",
        "    xs, ok := toAnySlice(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make([]bool, 0, len(xs))",
        "    for _, item := range xs {",
        "        b, ok := toBool(item)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out = append(out, b)",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toBytesSlice(v any) ([][]byte, bool) {",
        "    xs, ok := toAnySlice(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make([][]byte, 0, len(xs))",
        "    for _, item := range xs {",
        "        b, ok := toBytes(item)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out = append(out, b)",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toAnySlice(v any) ([]any, bool) {",
        "    if xs, ok := v.([]any); ok {",
        "        return xs, true",
        "    }",
        "    // Some decoders may produce concrete typed slices. Accept a few.",
        "    switch t := v.(type) {",
        "    case []float64:",
        "        out := make([]any, 0, len(t))",
        "        for _, x := range t {",
        "            out = append(out, x)",
        "        }",
        "        return out, true",
        "    case []int64:",
        "        out := make([]any, 0, len(t))",
        "        for _, x := range t {",
        "            out = append(out, x)",
        "        }",
        "        return out, true",
        "    case []string:",
        "        out := make([]any, 0, len(t))",
        "        for _, x := range t {",
        "            out = append(out, x)",
        "        }",
        "        return out, true",
        "    case []bool:",
        "        out := make([]any, 0, len(t))",
        "        for _, x := range t {",
        "            out = append(out, x)",
        "        }",
        "        return out, true",
        "    default:",
        "        return nil, false",
        "    }",
        "}",
        "",
        "func toAnyMap(v any) (map[string]any, bool) {",
        "    if m, ok := v.(map[string]any); ok {",
        "        return m, true",
        "    }",
        "    if m, ok := v.(map[any]any); ok {",
        "        out := make(map[string]any, len(m))",
        "        for k, vv := range m {",
        "            ks, ok := k.(string)",
        "            if !ok {",
        "                return nil, false",
        "            }",
        "            out[ks] = vv",
        "        }",
        "        return out, true",
        "    }",
        "    return nil, false",
        "}",
        "",
        "func toStringInt64Map(v any) (map[string]int64, bool) {",
        "    m, ok := toAnyMap(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make(map[string]int64, len(m))",
        "    for k, vv := range m {",
        "        n, ok := toInt64(vv)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out[k] = n",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toStringFloat64Map(v any) (map[string]float64, bool) {",
        "    m, ok := toAnyMap(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make(map[string]float64, len(m))",
        "    for k, vv := range m {",
        "        f, ok := toFloat64(vv)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out[k] = f",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toStringStringMap(v any) (map[string]string, bool) {",
        "    m, ok := toAnyMap(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make(map[string]string, len(m))",
        "    for k, vv := range m {",
        "        s, ok := toString(vv)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out[k] = s",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toStringBoolMap(v any) (map[string]bool, bool) {",
        "    m, ok := toAnyMap(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make(map[string]bool, len(m))",
        "    for k, vv := range m {",
        "        b, ok := toBool(vv)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out[k] = b",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toStringBytesMap(v any) (map[string][]byte, bool) {",
        "    m, ok := toAnyMap(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make(map[string][]byte, len(m))",
        "    for k, vv := range m {",
        "        b, ok := toBytes(vv)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out[k] = b",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toStringInt64SliceMap(v any) (map[string][]int64, bool) {",
        "    m, ok := toAnyMap(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make(map[string][]int64, len(m))",
        "    for k, vv := range m {",
        "        xs, ok := toInt64Slice(vv)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out[k] = xs",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toStringFloat64SliceMap(v any) (map[string][]float64, bool) {",
        "    m, ok := toAnyMap(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make(map[string][]float64, len(m))",
        "    for k, vv := range m {",
        "        xs, ok := toFloat64Slice(vv)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out[k] = xs",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toStringStringSliceMap(v any) (map[string][]string, bool) {",
        "    m, ok := toAnyMap(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make(map[string][]string, len(m))",
        "    for k, vv := range m {",
        "        xs, ok := toStringSlice(vv)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out[k] = xs",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toStringBoolSliceMap(v any) (map[string][]bool, bool) {",
        "    m, ok := toAnyMap(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make(map[string][]bool, len(m))",
        "    for k, vv := range m {",
        "        xs, ok := toBoolSlice(vv)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out[k] = xs",
        "    }",
        "    return out, true",
        "}",
        "",
        "func toStringBytesSliceMap(v any) (map[string][][]byte, bool) {",
        "    m, ok := toAnyMap(v)",
        "    if !ok {",
        "        return nil, false",
        "    }",
        "    out := make(map[string][][]byte, len(m))",
        "    for k, vv := range m {",
        "        xs, ok := toBytesSlice(vv)",
        "        if !ok {",
        "            return nil, false",
        "        }",
        "        out[k] = xs",
        "    }",
        "    return out, true",
        "}",
    ]

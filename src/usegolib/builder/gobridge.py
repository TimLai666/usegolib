from __future__ import annotations

from pathlib import Path

from .symbols import ExportedFunc, ExportedMethod, GenericInstantiation


def write_bridge(
    *,
    bridge_dir: Path,
    module_path: str,
    functions: list[ExportedFunc],
    methods: list[ExportedMethod] | None = None,
    generic_instantiations: list[GenericInstantiation] | None = None,
    struct_types_by_pkg: dict[str, set[str]] | None = None,
    adapter_types: set[str] | None = None,
) -> None:
    # Generate a single `main` package for `-buildmode=c-shared`.
    struct_types_by_pkg = struct_types_by_pkg or {}
    methods = methods or []
    generic_instantiations = generic_instantiations or []
    adapter_types = adapter_types or set()
    imports: dict[str, str] = {}
    for fn in functions:
        if fn.pkg not in imports:
            alias = f"p{len(imports)}"
            imports[fn.pkg] = alias
    for m in methods:
        if m.pkg not in imports:
            alias = f"p{len(imports)}"
            imports[m.pkg] = alias
    for gi in generic_instantiations:
        if gi.pkg not in imports:
            alias = f"p{len(imports)}"
            imports[gi.pkg] = alias

    func_reg_lines: list[str] = []
    method_reg_lines: list[str] = []
    wrap_lines: list[str] = []

    needs_reflect = True  # Object handles require reflection helpers.
    allowed_struct_type_keys: set[str] = set()
    for pkg, names in struct_types_by_pkg.items():
        for n in names:
            allowed_struct_type_keys.add(f"{pkg}.{n}")

    for fn in functions:
        alias = imports[fn.pkg]
        key = f"{fn.pkg}:{fn.name}"
        wrap_name = f"wrap_{alias}_{fn.name}"

        func_reg_lines.append(f'        "{key}": {wrap_name},')
        struct_types = struct_types_by_pkg.get(fn.pkg, set())
        if any(_base_type(t) in struct_types for t in fn.params) or any(
            _base_type(t) in struct_types for t in fn.results
        ):
            needs_reflect = True
        if any(_base_type(t) in adapter_types for t in fn.params) or any(
            _base_type(t) in adapter_types for t in fn.results
        ):
            needs_reflect = True
        wrap_lines.extend(
            _write_wrapper(
                wrap_name=wrap_name,
                alias=alias,
                fn=fn,
                struct_types=struct_types,
            )
        )
        wrap_lines.append("")

    for gi in generic_instantiations:
        alias = imports[gi.pkg]
        key = f"{gi.pkg}:{gi.symbol}"
        wrap_name = f"wrapg_{alias}_{gi.symbol}"

        func_reg_lines.append(f'        "{key}": {wrap_name},')
        struct_types = struct_types_by_pkg.get(gi.pkg, set())
        wrap_lines.extend(
            _write_generic_wrapper(
                wrap_name=wrap_name,
                alias=alias,
                gi=gi,
                struct_types=struct_types,
            )
        )
        wrap_lines.append("")

    obj_type_keys: set[str] = set()
    for m in methods:
        alias = imports[m.pkg]
        type_key = f"{m.pkg}.{m.recv}"
        obj_type_keys.add(type_key)
        method_key = f"{type_key}:{m.name}"
        wrap_name = f"wrapm_{alias}_{m.recv}_{m.name}"
        method_reg_lines.append(f'        "{method_key}": {wrap_name},')

        struct_types = struct_types_by_pkg.get(m.pkg, set())
        if any(_base_type(t) in struct_types for t in m.params) or any(
            _base_type(t) in struct_types for t in m.results
        ):
            needs_reflect = True
        if any(_base_type(t) in adapter_types for t in m.params) or any(
            _base_type(t) in adapter_types for t in m.results
        ):
            needs_reflect = True
        wrap_lines.extend(
            _write_method_wrapper(
                wrap_name=wrap_name,
                alias=alias,
                m=m,
                struct_types=struct_types,
            )
        )
        wrap_lines.append("")
    type_lines: list[str] = []
    for m in methods:
        type_key = f"{m.pkg}.{m.recv}"
        # De-dupe by key.
        if any(ln.startswith(f'        "{type_key}":') for ln in type_lines):
            continue
        alias = imports[m.pkg]
        type_lines.append(f'        "{type_key}": reflect.TypeOf({alias}.{m.recv}{{}}),')

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
            '    Type string `msgpack:"type,omitempty"`',
            '    ID uint64 `msgpack:"id,omitempty"`',
            '    Method string `msgpack:"method,omitempty"`',
            '    Init any `msgpack:"init,omitempty"`',
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
            '    Result any `msgpack:"result"`',
            '    Error *ErrorObj `msgpack:"error,omitempty"`',
            "}",
            "",
            "type Handler func(args []any) (any, *ErrorObj)",
            "type MethodHandler func(obj any, args []any) (any, *ErrorObj)",
            "",
            "var dispatch = map[string]Handler{}",
            "var methodDispatch = map[string]MethodHandler{}",
            "var typeByKey = map[string]reflect.Type{}",
            "",
            "type ObjEntry struct {",
            "    Key string",
            "    Obj any",
            "}",
            "",
            "var objNext uint64",
            "var objMu sync.RWMutex",
            "var objByID = map[uint64]ObjEntry{}",
            "",
            "func init() {",
            "    dispatch = map[string]Handler{",
            *func_reg_lines,
            "    }",
            "    methodDispatch = map[string]MethodHandler{",
            *method_reg_lines,
            "    }",
            "    typeByKey = map[string]reflect.Type{",
            *type_lines,
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
            "",
            "    switch req.Op {",
            '    case "call":',
            '        key := req.Pkg + ":" + req.Fn',
            "        h := dispatch[key]",
            "        if h == nil {",
            '            writeError(respPtr, respLen, "SymbolNotFound", "symbol not found", map[string]any{"pkg": req.Pkg, "fn": req.Fn})',
            "            return 0",
            "        }",
            "",
            "        var result any",
            "        var errObj *ErrorObj",
            "        func() {",
            "            defer func() {",
            "                if r := recover(); r != nil {",
            '                    errObj = &ErrorObj{Type: "GoPanicError", Message: "panic"}',
            "                }",
            "            }()",
            "            result, errObj = h(req.Args)",
            "        }()",
            "",
            "        if errObj != nil {",
            "            writeResp(respPtr, respLen, &Response{Ok: false, Error: errObj})",
            "            return 0",
            "        }",
            "        writeResp(respPtr, respLen, &Response{Ok: true, Result: result})",
            "        return 0",
            '    case "obj_new":',
            "        typeKey := req.Pkg + \".\" + req.Type",
            "        rt, ok := typeByKey[typeKey]",
            "        if !ok {",
            '            writeError(respPtr, respLen, "TypeNotFound", "type not found", map[string]any{"type": typeKey})',
            "            return 0",
            "        }",
            "        if rt.Kind() != reflect.Struct {",
            '            writeError(respPtr, respLen, "ABIError", "type is not a struct", map[string]any{"type": typeKey})',
            "            return 0",
            "        }",
            "        sv := reflect.New(rt).Elem()",
            "        if req.Init != nil {",
            "            cv, ok := convertToType(req.Init, rt)",
            "            if !ok {",
            '                writeError(respPtr, respLen, "UnsupportedTypeError", "invalid init", map[string]any{"type": typeKey})',
            "                return 0",
            "            }",
            "            sv = cv",
            "        }",
            "        pv := reflect.New(rt)",
            "        pv.Elem().Set(sv)",
            "        obj := pv.Interface()",
            "",
            "        id := atomic.AddUint64(&objNext, 1)",
            "        objMu.Lock()",
            "        objByID[id] = ObjEntry{Key: typeKey, Obj: obj}",
            "        objMu.Unlock()",
            "        writeResp(respPtr, respLen, &Response{Ok: true, Result: id})",
            "        return 0",
            '    case "obj_call":',
            "        typeKey := req.Pkg + \".\" + req.Type",
            "        objMu.RLock()",
            "        ent, ok := objByID[req.ID]",
            "        objMu.RUnlock()",
            "        if !ok {",
            '            writeError(respPtr, respLen, "ObjectNotFound", "object not found", map[string]any{"id": req.ID})',
            "            return 0",
            "        }",
            "        if ent.Key != typeKey {",
            '            writeError(respPtr, respLen, "ABIError", "object type mismatch", map[string]any{"id": req.ID, "type": typeKey})',
            "            return 0",
            "        }",
            "        mk := typeKey + \":\" + req.Method",
            "        mh := methodDispatch[mk]",
            "        if mh == nil {",
            '            writeError(respPtr, respLen, "MethodNotFound", "method not found", map[string]any{\"type\": typeKey, \"method\": req.Method})',
            "            return 0",
            "        }",
            "        var result any",
            "        var errObj *ErrorObj",
            "        func() {",
            "            defer func() {",
            "                if r := recover(); r != nil {",
            '                    errObj = &ErrorObj{Type: "GoPanicError", Message: "panic"}',
            "                }",
            "            }()",
            "            result, errObj = mh(ent.Obj, req.Args)",
            "        }()",
            "        if errObj != nil {",
            "            writeResp(respPtr, respLen, &Response{Ok: false, Error: errObj})",
            "            return 0",
            "        }",
            "        writeResp(respPtr, respLen, &Response{Ok: true, Result: result})",
            "        return 0",
            '    case "obj_free":',
            "        objMu.Lock()",
            "        delete(objByID, req.ID)",
            "        objMu.Unlock()",
            "        writeResp(respPtr, respLen, &Response{Ok: true, Result: nil})",
            "        return 0",
            "    default:",
            '        writeError(respPtr, respLen, "UnsupportedOperation", "unsupported op", map[string]any{"op": req.Op})',
            "        return 0",
            "    }",
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
    import_block = [
        "import (",
        '    "unsafe"',
        "",
        '    "github.com/vmihailenco/msgpack/v5"',
    ]
    import_block.append('    "sync"')
    import_block.append('    "sync/atomic"')
    import_block.append('    "reflect"')
    import_block.append('    "strings"')
    import_block.append('    "time"')
    if "uuid.UUID" in adapter_types:
        import_block.append('    uuid "github.com/google/uuid"')
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
    helpers = _write_helpers(
        needs_reflect=needs_reflect,
        allowed_struct_type_keys=sorted(allowed_struct_type_keys),
        adapter_types=sorted(adapter_types),
    )
    bridge_file.write_text(
        src + "\n" + "\n".join(wrap_lines) + "\n" + "\n".join(helpers) + "\n",
        encoding="utf-8",
    )


def _write_wrapper(
    *,
    wrap_name: str,
    alias: str,
    fn: ExportedFunc,
    struct_types: set[str],
) -> list[str]:
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
        lines.extend(
            _write_arg_convert(
                var_name=vn,
                go_type=t,
                value_expr=f"args[{i}]",
                pkg_alias=alias,
                struct_types=struct_types,
            )
        )

    call_args = list(arg_names)
    if fn.params and fn.params[-1].strip().startswith("..."):
        call_args[-1] = call_args[-1] + "..."
    call = f"{alias}.{fn.name}({', '.join(call_args)})"
    if len(fn.results) == 0:
        lines.append(f"    {call}")
        lines.append("    return nil, nil")
    elif len(fn.results) == 1:
        lines.append(f"    r0 := {call}")
        if _base_type(fn.results[0]) == "any" or _base_type(fn.results[0]) in struct_types or _base_type(
            fn.results[0]
        ) in {
            "time.Time",
            "time.Duration",
            "uuid.UUID",
        }:
            lines.append("    v0, ok := exportAny(reflect.ValueOf(r0))")
            lines.append("    if !ok {")
            lines.append(
                '        return nil, &ErrorObj{Type: "UnsupportedTypeError", Message: "unsupported return type"}'
            )
            lines.append("    }")
            lines.append("    return v0, nil")
        else:
            lines.append("    return r0, nil")
    else:
        # (T, error)
        lines.append(f"    r0, err := {call}")
        lines.append("    if err != nil {")
        lines.append('        return nil, &ErrorObj{Type: "GoError", Message: err.Error()}')
        lines.append("    }")
        if _base_type(fn.results[0]) in struct_types or _base_type(fn.results[0]) in {
            "time.Time",
            "time.Duration",
            "uuid.UUID",
        }:
            lines.append("    v0, ok := exportAny(reflect.ValueOf(r0))")
            lines.append("    if !ok {")
            lines.append(
                '        return nil, &ErrorObj{Type: "UnsupportedTypeError", Message: "unsupported return type"}'
            )
            lines.append("    }")
            lines.append("    return v0, nil")
        else:
            lines.append("    return r0, nil")

    lines.append("}")
    return lines


def _write_method_wrapper(
    *,
    wrap_name: str,
    alias: str,
    m: ExportedMethod,
    struct_types: set[str],
) -> list[str]:
    lines: list[str] = []
    recv_go = f"*{alias}.{m.recv}"
    lines.append(f"func {wrap_name}(obj any, args []any) (any, *ErrorObj) {{")
    lines.append(f"    recv, ok := obj.({recv_go})")
    lines.append("    if !ok {")
    lines.append('        return nil, &ErrorObj{Type: "ABIError", Message: "wrong receiver type"}')
    lines.append("    }")
    lines.append(f"    if len(args) != {len(m.params)} {{")
    lines.append('        return nil, &ErrorObj{Type: "ABIError", Message: "wrong arity"}')
    lines.append("    }")

    arg_names: list[str] = []
    for i, t in enumerate(m.params):
        vn = f"a{i}"
        arg_names.append(vn)
        lines.extend(
            _write_arg_convert(
                var_name=vn,
                go_type=t,
                value_expr=f"args[{i}]",
                pkg_alias=alias,
                struct_types=struct_types,
            )
        )

    call_args = list(arg_names)
    if m.params and m.params[-1].strip().startswith("..."):
        call_args[-1] = call_args[-1] + "..."
    call = f"recv.{m.name}({', '.join(call_args)})"
    if len(m.results) == 0:
        lines.append(f"    {call}")
        lines.append("    return nil, nil")
    elif len(m.results) == 1:
        lines.append(f"    r0 := {call}")
        if _base_type(m.results[0]) == "any" or _base_type(m.results[0]) in struct_types or _base_type(
            m.results[0]
        ) in {
            "time.Time",
            "time.Duration",
            "uuid.UUID",
        }:
            lines.append("    v0, ok := exportAny(reflect.ValueOf(r0))")
            lines.append("    if !ok {")
            lines.append(
                '        return nil, &ErrorObj{Type: "UnsupportedTypeError", Message: "unsupported return type"}'
            )
            lines.append("    }")
            lines.append("    return v0, nil")
        else:
            lines.append("    return r0, nil")
    else:
        lines.append(f"    r0, err := {call}")
        lines.append("    if err != nil {")
        lines.append('        return nil, &ErrorObj{Type: "GoError", Message: err.Error()}')
        lines.append("    }")
        if _base_type(m.results[0]) in struct_types or _base_type(m.results[0]) in {
            "time.Time",
            "time.Duration",
            "uuid.UUID",
        }:
            lines.append("    v0, ok := exportAny(reflect.ValueOf(r0))")
            lines.append("    if !ok {")
            lines.append(
                '        return nil, &ErrorObj{Type: "UnsupportedTypeError", Message: "unsupported return type"}'
            )
            lines.append("    }")
            lines.append("    return v0, nil")
        else:
            lines.append("    return r0, nil")

    lines.append("}")
    return lines


def _write_generic_wrapper(
    *,
    wrap_name: str,
    alias: str,
    gi: GenericInstantiation,
    struct_types: set[str],
) -> list[str]:
    lines: list[str] = []
    lines.append(f"func {wrap_name}(args []any) (any, *ErrorObj) {{")
    lines.append(f"    if len(args) != {len(gi.params)} {{")
    lines.append('        return nil, &ErrorObj{Type: "ABIError", Message: "wrong arity"}')
    lines.append("    }")

    arg_names: list[str] = []
    for i, t in enumerate(gi.params):
        vn = f"a{i}"
        arg_names.append(vn)
        lines.extend(
            _write_arg_convert(
                var_name=vn,
                go_type=t,
                value_expr=f"args[{i}]",
                pkg_alias=alias,
                struct_types=struct_types,
            )
        )

    type_args_exprs = [
        _qualify_type(t, pkg_alias=alias, struct_types=struct_types) for t in gi.type_args
    ]
    call_args = list(arg_names)
    if gi.params and gi.params[-1].strip().startswith("..."):
        call_args[-1] = call_args[-1] + "..."
    call = f"{alias}.{gi.generic_name}[{', '.join(type_args_exprs)}]({', '.join(call_args)})"
    if len(gi.results) == 0:
        lines.append(f"    {call}")
        lines.append("    return nil, nil")
    elif len(gi.results) == 1:
        lines.append(f"    r0 := {call}")
        if _base_type(gi.results[0]) == "any" or _base_type(gi.results[0]) in struct_types or _base_type(
            gi.results[0]
        ) in {
            "time.Time",
            "time.Duration",
            "uuid.UUID",
        }:
            lines.append("    v0, ok := exportAny(reflect.ValueOf(r0))")
            lines.append("    if !ok {")
            lines.append(
                '        return nil, &ErrorObj{Type: "UnsupportedTypeError", Message: "unsupported return type"}'
            )
            lines.append("    }")
            lines.append("    return v0, nil")
        else:
            lines.append("    return r0, nil")
    else:
        lines.append(f"    r0, err := {call}")
        lines.append("    if err != nil {")
        lines.append('        return nil, &ErrorObj{Type: "GoError", Message: err.Error()}')
        lines.append("    }")
        if _base_type(gi.results[0]) in struct_types or _base_type(gi.results[0]) in {
            "time.Time",
            "time.Duration",
            "uuid.UUID",
        }:
            lines.append("    v0, ok := exportAny(reflect.ValueOf(r0))")
            lines.append("    if !ok {")
            lines.append(
                '        return nil, &ErrorObj{Type: "UnsupportedTypeError", Message: "unsupported return type"}'
            )
            lines.append("    }")
            lines.append("    return v0, nil")
        else:
            lines.append("    return r0, nil")
    lines.append("}")
    return lines


def _conv_expr(go_type: str, v: str) -> str:
    raise AssertionError(f"unexpected: {_conv_expr.__name__} called for {go_type}/{v}")


def _base_type(go_type: str) -> str:
    t = go_type.strip()
    while True:
        # Variadic `...T` behaves like a slice `[]T` inside the wrapper.
        if t.startswith("..."):
            t = t[3:].strip()
            continue
        if t.startswith("*"):
            t = t[1:].strip()
            continue
        if t.startswith("[]"):
            t = t[2:].strip()
            continue
        if t.startswith("map[string]"):
            t = t[len("map[string]") :].strip()
            continue
        return t


def _qualify_type(go_type: str, *, pkg_alias: str, struct_types: set[str]) -> str:
    t = go_type.strip()
    if t.startswith("*"):
        return "*" + _qualify_type(t[1:], pkg_alias=pkg_alias, struct_types=struct_types)
    if t.startswith("..."):
        # Variadic `...T` is a slice type `[]T` when referenced as a value type.
        return "[]" + _qualify_type(t[3:], pkg_alias=pkg_alias, struct_types=struct_types)
    if t.startswith("[]"):
        return "[]" + _qualify_type(t[2:], pkg_alias=pkg_alias, struct_types=struct_types)
    if t.startswith("map[string]"):
        return "map[string]" + _qualify_type(
            t[len("map[string]") :],
            pkg_alias=pkg_alias,
            struct_types=struct_types,
        )
    if t in struct_types:
        return f"{pkg_alias}.{t}"
    return t


def _write_arg_convert(
    *,
    var_name: str,
    go_type: str,
    value_expr: str,
    pkg_alias: str,
    struct_types: set[str],
) -> list[str]:
    lines: list[str] = []

    def unsupported() -> None:
        lines.append(
            '    return nil, &ErrorObj{Type: "UnsupportedTypeError", Message: "unsupported arg type"}'
        )

    # Normalize variadics: `...T` is received over ABI as a single slice arg.
    if go_type.strip().startswith("..."):
        go_type = "[]" + go_type.strip()[3:].strip()

    if go_type == "any":
        lines.append(f"    {var_name} := {value_expr}")
        return lines

    if _base_type(go_type) in struct_types:
        typ = _qualify_type(go_type, pkg_alias=pkg_alias, struct_types=struct_types)
        lines.append(f"    {var_name}, ok := toGoValue[{typ}]({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        return lines

    if _base_type(go_type) == "time.Time":
        typ = _qualify_type(go_type, pkg_alias=pkg_alias, struct_types=struct_types)
        lines.append(f"    {var_name}, ok := toGoValue[{typ}]({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        return lines

    if _base_type(go_type) == "time.Duration":
        typ = _qualify_type(go_type, pkg_alias=pkg_alias, struct_types=struct_types)
        lines.append(f"    {var_name}, ok := toGoValue[{typ}]({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        return lines

    if _base_type(go_type) == "uuid.UUID":
        typ = _qualify_type(go_type, pkg_alias=pkg_alias, struct_types=struct_types)
        lines.append(f"    {var_name}, ok := toGoValue[{typ}]({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        return lines

    if go_type.startswith("map[string]"):
        vt = go_type[len("map[string]") :]
        tmp = f"t_{var_name}"

        if vt == "any":
            lines.append(f"    {var_name}, ok := toAnyMap({value_expr})")
            lines.append("    if !ok {")
            unsupported()
            lines.append("    }")
            return lines

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

    if go_type == "[]any":
        lines.append(f"    {var_name}, ok := toAnySlice({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        return lines

    if go_type == "[]map[string]any":
        tmp = f"t_{var_name}"
        lines.append(f"    {tmp}, ok := toAnySlice({value_expr})")
        lines.append("    if !ok {")
        unsupported()
        lines.append("    }")
        lines.append(f"    {var_name} := make([]map[string]any, 0, len({tmp}))")
        lines.append(f"    for _, item := range {tmp} {{")
        lines.append("        m, ok := toAnyMap(item)")
        lines.append("        if !ok {")
        lines.append(
            '            return nil, &ErrorObj{Type: "UnsupportedTypeError", Message: "unsupported arg type"}'
        )
        lines.append("        }")
        lines.append(f"        {var_name} = append({var_name}, m)")
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


def _write_helpers(
    *,
    needs_reflect: bool,
    allowed_struct_type_keys: list[str],
    adapter_types: list[str],
) -> list[str]:
    adapter_type_set = set(adapter_types)
    out = [
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

    if not needs_reflect:
        return out

    # Ensure adapter types listed are at least referenced so go imports don't get dropped by generator updates.
    _ = adapter_types

    # Embed a whitelist of named struct types we allow to cross the boundary as record structs.
    # This prevents accidentally exporting arbitrary third-party structs (e.g. time.Time) as maps.
    # Note: these types are referenced only by reflection, so this list is sufficient.
    #
    # We currently allow all named structs discovered in the scanned packages.
    # (It is still restricted to structs that actually appear in supported signatures.)
    out.extend(
        [
            "",
            "var allowedStructTypes = map[string]bool{",
        ]
    )
    for k in allowed_struct_type_keys:
        out.append(f'    "{k}": true,')
    out.extend(
        [
            "}",
            "",
            "func isAllowedStructType(t reflect.Type) bool {",
            "    if t.Kind() == reflect.Ptr {",
            "        t = t.Elem()",
            "    }",
            "    if t.Kind() != reflect.Struct {",
            "        return false",
            "    }",
            "    if t.PkgPath() == \"\" || t.Name() == \"\" {",
            "        return false",
            "    }",
            "    k := t.PkgPath() + \".\" + t.Name()",
            "    return allowedStructTypes[k]",
            "}",
        ]
    )

    out.extend(
        [
            "",
            "func toGoValue[T any](v any) (T, bool) {",
            "    var out T",
            "    rt := reflect.TypeOf((*T)(nil)).Elem()",
            "    rv, ok := convertToType(v, rt)",
            "    if !ok {",
            "        return out, false",
            "    }",
            "    vv, ok := rv.Interface().(T)",
            "    if !ok {",
            "        return out, false",
            "    }",
            "    return vv, true",
            "}",
            "",
            "func toStruct[T any](v any) (T, bool) {",
            "    var out T",
            "    rv := reflect.ValueOf(&out).Elem()",
            "    if rv.Kind() != reflect.Struct {",
                "        return out, false",
            "    }",
            "    m, ok := toAnyMap(v)",
            "    if !ok {",
            "        return out, false",
            "    }",
            "    rt := rv.Type()",
            "    for k, vv := range m {",
            "        sf, ok := rt.FieldByName(k)",
            "        if !ok || sf.PkgPath != \"\" {",
            "            return out, false",
            "        }",
            "        fv := rv.FieldByIndex(sf.Index)",
            "        if !fv.CanSet() {",
            "            return out, false",
            "        }",
            "        cv, ok := convertToType(vv, fv.Type())",
            "        if !ok {",
            "            return out, false",
            "        }",
            "        fv.Set(cv)",
            "    }",
            "    return out, true",
            "}",
            "",
            "func fromStruct(v any) (map[string]any, bool) {",
            "    rv := reflect.ValueOf(v)",
            "    if rv.Kind() == reflect.Ptr {",
                "        rv = rv.Elem()",
            "    }",
            "    if rv.Kind() != reflect.Struct {",
                "        return nil, false",
            "    }",
            "    rt := rv.Type()",
            "    out := map[string]any{}",
            "    for i := 0; i < rt.NumField(); i++ {",
                "        sf := rt.Field(i)",
                "        if sf.PkgPath != \"\" {",
                    "            continue",
                "        }",
                "        av, ok := exportAny(rv.Field(i))",
                "        if !ok {",
                    "            return nil, false",
                "        }",
                "        out[sf.Name] = av",
            "    }",
            "    return out, true",
            "}",
            "",
            "func convertToType(v any, t reflect.Type) (reflect.Value, bool) {",
            "    // Adapter: github.com/google/uuid.UUID encoded as string.",
            "    if t.PkgPath() == \"github.com/google/uuid\" && t.Name() == \"UUID\" {",
            "        s, ok := toString(v)",
            "        if !ok {",
            "            return reflect.Value{}, false",
            "        }",
            "        id, err := uuid.Parse(s)",
            "        if err != nil {",
            "            return reflect.Value{}, false",
            "        }",
            "        out := reflect.New(t).Elem()",
            "        out.Set(reflect.ValueOf(id))",
            "        return out, true",
            "    }",
            "    switch t.Kind() {",
            "    case reflect.Bool:",
            "        b, ok := toBool(v)",
            "        if !ok {",
                "            return reflect.Value{}, false",
            "        }",
            "        out := reflect.New(t).Elem()",
            "        out.SetBool(b)",
            "        return out, true",
            "    case reflect.String:",
            "        s, ok := toString(v)",
            "        if !ok {",
            "            return reflect.Value{}, false",
            "        }",
            "        out := reflect.New(t).Elem()",
            "        out.SetString(s)",
            "        return out, true",
            "    case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:",
            "        n, ok := toInt64(v)",
            "        if !ok {",
            "            return reflect.Value{}, false",
            "        }",
            "        out := reflect.New(t).Elem()",
            "        if out.OverflowInt(n) {",
            "            return reflect.Value{}, false",
            "        }",
            "        out.SetInt(n)",
            "        return out, true",
            "    case reflect.Float32, reflect.Float64:",
            "        f, ok := toFloat64(v)",
            "        if !ok {",
            "            return reflect.Value{}, false",
            "        }",
            "        out := reflect.New(t).Elem()",
            "        if out.OverflowFloat(f) {",
            "            return reflect.Value{}, false",
            "        }",
            "        out.SetFloat(f)",
            "        return out, true",
            "    case reflect.Ptr:",
            "        if v == nil {",
            "            return reflect.Zero(t), true",
            "        }",
            "        cv, ok := convertToType(v, t.Elem())",
            "        if !ok {",
            "            return reflect.Value{}, false",
            "        }",
            "        out := reflect.New(t.Elem())",
            "        out.Elem().Set(cv)",
            "        return out, true",
            "    case reflect.Slice:",
            "        // Special-case []byte",
            "        if t.Elem().Kind() == reflect.Uint8 {",
                "            b, ok := toBytes(v)",
                "            if !ok {",
                    "                return reflect.Value{}, false",
                "            }",
                "            out := reflect.New(t).Elem()",
                "            out.SetBytes(b)",
                "            return out, true",
            "        }",
            "        xs, ok := toAnySlice(v)",
            "        if !ok {",
            "            return reflect.Value{}, false",
            "        }",
            "        out := reflect.MakeSlice(t, 0, len(xs))",
            "        for _, item := range xs {",
            "            cv, ok := convertToType(item, t.Elem())",
            "            if !ok {",
            "                return reflect.Value{}, false",
            "            }",
            "            out = reflect.Append(out, cv)",
            "        }",
            "        return out, true",
            "    case reflect.Map:",
            "        if t.Key().Kind() != reflect.String {",
            "            return reflect.Value{}, false",
            "        }",
            "        m, ok := toAnyMap(v)",
            "        if !ok {",
            "            return reflect.Value{}, false",
            "        }",
            "        out := reflect.MakeMapWithSize(t, len(m))",
            "        for k, vv := range m {",
            "            cv, ok := convertToType(vv, t.Elem())",
            "            if !ok {",
            "                return reflect.Value{}, false",
            "            }",
            "            out.SetMapIndex(reflect.ValueOf(k), cv)",
            "        }",
            "        return out, true",
            "    case reflect.Struct:",
            "        // Adapter: time.Time encoded as RFC3339Nano string.",
            "        if t.PkgPath() == \"time\" && t.Name() == \"Time\" {",
            "            s, ok := toString(v)",
            "            if !ok {",
            "                return reflect.Value{}, false",
            "            }",
            "            tt, err := time.Parse(time.RFC3339Nano, s)",
            "            if err != nil {",
            "                return reflect.Value{}, false",
            "            }",
            "            out := reflect.New(t).Elem()",
            "            out.Set(reflect.ValueOf(tt))",
            "            return out, true",
            "        }",
            "        if !isAllowedStructType(t) {",
            "            return reflect.Value{}, false",
            "        }",
            "        m, ok := toAnyMap(v)",
            "        if !ok {",
            "            return reflect.Value{}, false",
            "        }",
            "        out := reflect.New(t).Elem()",
            "        rt := out.Type()",
            "        for k, vv := range m {",
            "            sf, ok := fieldByKey(rt, k)",
            "            if !ok {",
            "                return reflect.Value{}, false",
            "            }",
            "            fv := out.FieldByIndex(sf.Index)",
            "            if !fv.CanSet() {",
            "                return reflect.Value{}, false",
            "            }",
            "            cv, ok := convertToType(vv, fv.Type())",
            "            if !ok {",
            "                return reflect.Value{}, false",
            "            }",
            "            fv.Set(cv)",
            "        }",
            "        return out, true",
            "    default:",
            "        return reflect.Value{}, false",
            "    }",
            "}",
            "",
            "func fieldByKey(rt reflect.Type, key string) (reflect.StructField, bool) {",
            "    if key == \"\" {",
            "        return reflect.StructField{}, false",
            "    }",
            "    // Prefer direct exported field name match.",
            "    if sf, ok := rt.FieldByName(key); ok && sf.PkgPath == \"\" && !fieldIgnored(sf) {",
            "        return sf, true",
            "    }",
            "    // Fallback to tag-based keys (msgpack/json).",
            "    for i := 0; i < rt.NumField(); i++ {",
            "        sf := rt.Field(i)",
            "        if sf.PkgPath != \"\" {",
            "            continue",
            "        }",
            "        if fieldIgnored(sf) {",
            "            continue",
            "        }",
            "        if tagName(sf.Tag.Get(\"msgpack\")) == key {",
            "            return sf, true",
            "        }",
            "        if tagName(sf.Tag.Get(\"json\")) == key {",
            "            return sf, true",
            "        }",
            "    }",
            "    return reflect.StructField{}, false",
            "}",
            "",
            "func exportAny(v reflect.Value) (any, bool) {",
            "    if v.Kind() == reflect.Ptr {",
            "        if v.IsNil() {",
            "            return nil, true",
            "        }",
            "        v = v.Elem()",
            "    }",
            "    if v.Kind() == reflect.Interface {",
            "        if v.IsNil() {",
            "            return nil, true",
            "        }",
            "        v = v.Elem()",
            "    }",
            "    // Adapter: github.com/google/uuid.UUID encoded as string.",
            "    if v.Type().PkgPath() == \"github.com/google/uuid\" && v.Type().Name() == \"UUID\" {",
            "        id := v.Interface().(uuid.UUID)",
            "        return id.String(), true",
            "    }",
            "    switch v.Kind() {",
            "    case reflect.Bool, reflect.String, reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64, reflect.Float32, reflect.Float64:",
            "        return v.Interface(), true",
            "    case reflect.Slice:",
            "        if v.Type().Elem().Kind() == reflect.Uint8 {",
            "            return v.Bytes(), true",
            "        }",
            "        out := make([]any, 0, v.Len())",
            "        for i := 0; i < v.Len(); i++ {",
            "            item, ok := exportAny(v.Index(i))",
            "            if !ok {",
            "                return nil, false",
            "            }",
            "            out = append(out, item)",
            "        }",
            "        return out, true",
            "    case reflect.Map:",
            "        if v.Type().Key().Kind() != reflect.String {",
            "            return nil, false",
            "        }",
            "        out := make(map[string]any, v.Len())",
            "        for _, k := range v.MapKeys() {",
            "            kv := k.Interface().(string)",
            "            item, ok := exportAny(v.MapIndex(k))",
            "            if !ok {",
            "                return nil, false",
            "            }",
            "            out[kv] = item",
            "        }",
            "        return out, true",
            "    case reflect.Struct:",
            "        // Adapter: time.Time encoded as RFC3339Nano string.",
            "        if v.Type().PkgPath() == \"time\" && v.Type().Name() == \"Time\" {",
            "            tt := v.Interface().(time.Time)",
            "            return tt.Format(time.RFC3339Nano), true",
            "        }",
            "        if !isAllowedStructType(v.Type()) {",
            "            return nil, false",
            "        }",
            "        out := map[string]any{}",
            "        rt := v.Type()",
            "        for i := 0; i < rt.NumField(); i++ {",
            "            sf := rt.Field(i)",
            "            if sf.PkgPath != \"\" {",
            "                continue",
            "            }",
            "            if fieldIgnored(sf) {",
            "                continue",
            "            }",
            "            if fieldOmitEmpty(sf) && isEmptyValue(v.Field(i)) {",
            "                continue",
            "            }",
            "            av, ok := exportAny(v.Field(i))",
            "            if !ok {",
            "                return nil, false",
            "            }",
            "            k := fieldOutputKey(sf)",
            "            if k == \"\" {",
            "                continue",
            "            }",
            "            out[k] = av",
            "        }",
            "        return out, true",
            "    default:",
            "        return nil, false",
            "    }",
            "}",
            "",
            "func fieldOutputKey(sf reflect.StructField) string {",
            "    // Canonical key precedence: msgpack tag name, then json tag name, else field name.",
            "    if tagName(sf.Tag.Get(\"msgpack\")) != \"\" {",
            "        return tagName(sf.Tag.Get(\"msgpack\"))",
            "    }",
            "    if tagName(sf.Tag.Get(\"json\")) != \"\" {",
            "        return tagName(sf.Tag.Get(\"json\"))",
            "    }",
            "    return sf.Name",
            "}",
            "",
            "func tagName(tag string) string {",
            "    if tag == \"\" {",
            "        return \"\"",
            "    }",
            "    // `name,omitempty` -> name",
            "    n := tag",
            "    for i := 0; i < len(n); i++ {",
            "        if n[i] == ',' {",
            "            n = n[:i]",
            "            break",
            "        }",
            "    }",
            "    if n == \"-\" {",
            "        return \"\"",
            "    }",
            "    return n",
            "}",
            "",
            "func tagIgnored(tag string) bool {",
            "    if tag == \"\" {",
            "        return false",
            "    }",
            "    // `-` or `-,omitempty` etc.",
            "    return tag[0] == '-'",
            "}",
            "",
            "func tagHasOption(tag string, opt string) bool {",
            "    if tag == \"\" || opt == \"\" {",
            "        return false",
            "    }",
            "    i := strings.IndexByte(tag, ',')",
            "    if i < 0 {",
            "        return false",
            "    }",
            "    opts := tag[i+1:]",
            "    for _, part := range strings.Split(opts, \",\") {",
            "        if part == opt {",
            "            return true",
            "        }",
            "    }",
            "    return false",
            "}",
            "",
            "func fieldIgnored(sf reflect.StructField) bool {",
            "    mp := sf.Tag.Get(\"msgpack\")",
            "    js := sf.Tag.Get(\"json\")",
            "    if mp != \"\" {",
            "        return tagIgnored(mp)",
            "    }",
            "    return tagIgnored(js)",
            "}",
            "",
            "func fieldOmitEmpty(sf reflect.StructField) bool {",
            "    mp := sf.Tag.Get(\"msgpack\")",
            "    js := sf.Tag.Get(\"json\")",
            "    if mp != \"\" {",
            "        return tagHasOption(mp, \"omitempty\")",
            "    }",
            "    return tagHasOption(js, \"omitempty\")",
            "}",
            "",
            "func isEmptyValue(v reflect.Value) bool {",
            "    switch v.Kind() {",
            "    case reflect.Array, reflect.Map, reflect.Slice, reflect.String:",
            "        return v.Len() == 0",
            "    case reflect.Bool:",
            "        return !v.Bool()",
            "    case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:",
            "        return v.Int() == 0",
            "    case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64, reflect.Uintptr:",
            "        return v.Uint() == 0",
            "    case reflect.Float32, reflect.Float64:",
            "        return v.Float() == 0",
            "    case reflect.Interface, reflect.Ptr:",
            "        return v.IsNil()",
            "    case reflect.Struct:",
            "        return v.IsZero()",
            "    default:",
            "        return false",
            "    }",
            "}",
        ]
    )

    if "uuid.UUID" not in adapter_type_set:
        # Remove uuid adapter blocks when the dependency isn't needed, to avoid
        # importing google/uuid (and referencing `uuid`) for unrelated builds.
        filtered: list[str] = []
        ctx = ""
        skipping = False
        skip_until = ""
        uuid_marker = "    // Adapter: github.com/google/uuid.UUID encoded as string."
        for line in out:
            if line == "func convertToType(v any, t reflect.Type) (reflect.Value, bool) {":
                ctx = "convert"
            elif line == "func exportAny(v reflect.Value) (any, bool) {":
                ctx = "export"

            if not skipping and line == uuid_marker:
                skipping = True
                skip_until = "    switch t.Kind() {" if ctx == "convert" else "    switch v.Kind() {"
                continue

            if skipping:
                if line == skip_until:
                    skipping = False
                    skip_until = ""
                    filtered.append(line)
                continue

            filtered.append(line)
        out = filtered

    return out

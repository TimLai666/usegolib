from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from ..errors import BuildError
from .symbols import ExportedFunc, ExportedMethod, GenericFuncDef, ModuleScan, StructField


def scan_module(*, module_dir: Path) -> ModuleScan:
    """Scan exported top-level functions by parsing Go source (not `go doc` text).

    This is used by the builder to decide which functions are callable through the
    generated bridge for v0.
    """
    module_dir = module_dir.resolve()

    with tempfile.TemporaryDirectory(prefix="usegolib-goscan-") as td:
        scan_dir = Path(td)
        (scan_dir / "go.mod").write_text(
            "\n".join(
                [
                    "module usegolib.goscan",
                    "",
                    "go 1.22",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (scan_dir / "main.go").write_text(_scanner_go_source(), encoding="utf-8")

        try:
            proc = subprocess.run(
                ["go", "run", ".", "--module-dir", str(module_dir)],
                cwd=str(scan_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
        except FileNotFoundError as e:
            raise BuildError(
                "Go toolchain not found (`go` is missing from PATH). "
                "Install Go and ensure `go` is available on PATH. "
                "If you do not want auto-build on import, pass `build_if_missing=False` "
                "(and use prebuilt artifacts/wheels)."
            ) from e
        if proc.returncode != 0:
            raise BuildError(f"go scan failed\n{proc.stdout}")

        try:
            obj = json.loads(proc.stdout)
        except Exception as e:  # noqa: BLE001
            raise BuildError(f"failed to parse go scan output: {e}\n{proc.stdout}") from e

        funcs: list[ExportedFunc] = []
        for item in obj.get("funcs", []):
            if not isinstance(item, dict):
                continue
            pkg = item.get("pkg")
            name = item.get("name")
            params = item.get("params")
            results = item.get("results")
            doc = item.get("doc")
            if not isinstance(pkg, str) or not isinstance(name, str):
                continue
            if not isinstance(params, list) or not isinstance(results, list):
                continue
            if not all(isinstance(t, str) for t in params):
                continue
            if not all(isinstance(t, str) for t in results):
                continue
            doc_str: str | None = None
            if isinstance(doc, str):
                doc_str = doc.strip() or None
            funcs.append(
                ExportedFunc(
                    pkg=pkg,
                    name=name,
                    params=list(params),
                    results=list(results),
                    doc=doc_str,
                )
            )

        methods: list[ExportedMethod] = []
        for item in obj.get("methods", []):
            if not isinstance(item, dict):
                continue
            pkg = item.get("pkg")
            recv = item.get("recv")
            name = item.get("name")
            params = item.get("params")
            results = item.get("results")
            doc = item.get("doc")
            if not (isinstance(pkg, str) and isinstance(recv, str) and isinstance(name, str)):
                continue
            if not isinstance(params, list) or not isinstance(results, list):
                continue
            if not all(isinstance(t, str) for t in params):
                continue
            if not all(isinstance(t, str) for t in results):
                continue
            methods.append(
                ExportedMethod(
                    pkg=pkg,
                    recv=recv,
                    name=name,
                    params=list(params),
                    results=list(results),
                    doc=(doc.strip() or None) if isinstance(doc, str) else None,
                )
            )

        generic_funcs: list[GenericFuncDef] = []
        for item in obj.get("generic_funcs", []):
            if not isinstance(item, dict):
                continue
            pkg = item.get("pkg")
            name = item.get("name")
            type_params = item.get("type_params")
            params = item.get("params")
            results = item.get("results")
            doc = item.get("doc")
            if not (isinstance(pkg, str) and isinstance(name, str)):
                continue
            if not isinstance(type_params, list) or not all(isinstance(x, str) for x in type_params):
                continue
            if not isinstance(params, list) or not isinstance(results, list):
                continue
            if not all(isinstance(t, str) for t in params):
                continue
            if not all(isinstance(t, str) for t in results):
                continue
            generic_funcs.append(
                GenericFuncDef(
                    pkg=pkg,
                    name=name,
                    type_params=list(type_params),
                    params=list(params),
                    results=list(results),
                    doc=(doc.strip() or None) if isinstance(doc, str) else None,
                )
            )

        struct_types_by_pkg: dict[str, set[str]] = {}
        st = obj.get("struct_types")
        if isinstance(st, dict):
            for pkg, items in st.items():
                if not isinstance(pkg, str) or not isinstance(items, list):
                    continue
                struct_types_by_pkg[pkg] = {x for x in items if isinstance(x, str)}

        structs_by_pkg: dict[str, dict[str, list[StructField]]] = {}
        sd = obj.get("structs")
        if isinstance(sd, dict):
            for pkg, structs in sd.items():
                if not isinstance(pkg, str) or not isinstance(structs, list):
                    continue
                by_name: dict[str, list[StructField]] = {}
                for s in structs:
                    if not isinstance(s, dict):
                        continue
                    name = s.get("name")
                    fields = s.get("fields")
                    if not isinstance(name, str) or not isinstance(fields, list):
                        continue
                    out_fields: list[StructField] = []
                    for f in fields:
                        if not isinstance(f, dict):
                            continue
                        fn = f.get("name")
                        ft = f.get("type")
                        fk = f.get("key")
                        fa = f.get("aliases")
                        fo = f.get("omitempty")
                        fe = f.get("embedded")
                        if not (isinstance(fn, str) and isinstance(ft, str) and fn and ft):
                            continue
                        if not isinstance(fk, str) or not fk:
                            fk = fn
                        aliases: list[str] = []
                        if isinstance(fa, list) and all(isinstance(x, str) for x in fa):
                            aliases = [x for x in fa if x]
                        omitempty = bool(fo) if isinstance(fo, bool) else False
                        embedded = bool(fe) if isinstance(fe, bool) else False
                        out_fields.append(
                            StructField(
                                name=fn,
                                type=ft,
                                key=fk,
                                aliases=aliases,
                                omitempty=omitempty,
                                embedded=embedded,
                            )
                        )
                    by_name[name] = out_fields
                if by_name:
                    structs_by_pkg[pkg] = by_name

        return ModuleScan(
            funcs=funcs,
            methods=methods,
            generic_funcs=generic_funcs,
            struct_types_by_pkg=struct_types_by_pkg,
            structs_by_pkg=structs_by_pkg,
        )


def scan_exported_funcs(*, module_dir: Path) -> list[ExportedFunc]:
    return scan_module(module_dir=module_dir).funcs


def _scanner_go_source() -> str:
    # Keep this file stdlib-only so `go run` doesn't need network access.
    return r'''
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
)

type goListPkg struct {
	ImportPath string
	Dir        string
	GoFiles    []string
	CgoFiles   []string
}

type outFunc struct {
	Pkg     string   `json:"pkg"`
	Name    string   `json:"name"`
	Params  []string `json:"params"`
	Results []string `json:"results"`
	Doc     string   `json:"doc"`
}

type outMethod struct {
	Pkg     string   `json:"pkg"`
	Recv    string   `json:"recv"`
	Name    string   `json:"name"`
	Params  []string `json:"params"`
	Results []string `json:"results"`
	Doc     string   `json:"doc"`
}

type outGenericFunc struct {
	Pkg        string   `json:"pkg"`
	Name       string   `json:"name"`
	TypeParams []string `json:"type_params"`
	Params     []string `json:"params"`
	Results    []string `json:"results"`
	Doc        string   `json:"doc"`
}

type outObj struct {
	Funcs []outFunc `json:"funcs"`
	Methods []outMethod `json:"methods"`
	GenericFuncs []outGenericFunc `json:"generic_funcs"`
	StructTypes map[string][]string `json:"struct_types"`
	Structs map[string][]outStruct `json:"structs"`
}

type outStructField struct {
	Name string `json:"name"`
	Type string `json:"type"`
	Key string `json:"key"`
	Aliases []string `json:"aliases"`
	OmitEmpty bool `json:"omitempty"`
	Embedded bool `json:"embedded"`
}

type outStruct struct {
	Name   string           `json:"name"`
	Fields []outStructField `json:"fields"`
}

func main() {
	var moduleDir string
	flag.StringVar(&moduleDir, "module-dir", "", "Go module directory to scan")
	flag.Parse()

	if moduleDir == "" {
		fmt.Fprintln(os.Stderr, "missing --module-dir")
		os.Exit(2)
	}

	if err := os.Chdir(moduleDir); err != nil {
		fmt.Fprintf(os.Stderr, "chdir: %v\n", err)
		os.Exit(2)
	}

	pkgs, err := listPkgs()
	if err != nil {
		fmt.Fprintln(os.Stderr, err.Error())
		os.Exit(1)
	}

	out := outObj{
		Funcs:       make([]outFunc, 0, 128),
		Methods:     make([]outMethod, 0, 128),
		GenericFuncs: make([]outGenericFunc, 0, 128),
		StructTypes: map[string][]string{},
		Structs:     map[string][]outStruct{},
	}
	for _, p := range pkgs {
		if isInternalPkg(p.ImportPath) {
			continue
		}

		// Parse only GoFiles (exclude CgoFiles) to avoid `import "C"` handling here.
		files := make([]string, 0, len(p.GoFiles))
		for _, fn := range p.GoFiles {
			files = append(files, filepath.Join(p.Dir, fn))
		}
		if len(files) == 0 {
			continue
		}

		fs := token.NewFileSet()
		structNames := map[string]bool{}
		structFields := map[string][]outStructField{}
		for _, file := range files {
			af, err := parser.ParseFile(fs, file, nil, parser.ParseComments)
			if err != nil {
				continue
			}
			im := fileImports(af)
			collectStructTypes(af, im, structNames, structFields)
			for _, decl := range af.Decls {
				fd, ok := decl.(*ast.FuncDecl)
				if !ok {
					continue
				}
				if fd.Name == nil || !fd.Name.IsExported() {
					continue
				}
				// Exported generic functions are reported separately.
				if fd.Recv == nil && fd.Type != nil && fd.Type.TypeParams != nil && len(fd.Type.TypeParams.List) > 0 {
					typeParams := []string{}
					for _, tp := range fd.Type.TypeParams.List {
						if tp == nil || len(tp.Names) == 0 {
							continue
						}
						for _, nm := range tp.Names {
							if nm == nil || nm.Name == "" {
								continue
							}
							typeParams = append(typeParams, nm.Name)
						}
					}
					if len(typeParams) == 0 {
						continue
					}
					params := fieldListTypes(fd.Type.Params, im)
					results := fieldListTypes(fd.Type.Results, im)
					if params == nil || results == nil {
						continue
					}
					out.GenericFuncs = append(out.GenericFuncs, outGenericFunc{
						Pkg:        p.ImportPath,
						Name:       fd.Name.Name,
						TypeParams: typeParams,
						Params:     params,
						Results:    results,
						Doc:        docText(fd.Doc),
					})
					continue
				}

				// Top-level function.
				if fd.Recv == nil {
					params := fieldListTypes(fd.Type.Params, im)
					results := fieldListTypes(fd.Type.Results, im)
				if params == nil || results == nil {
					continue
				}

				out.Funcs = append(out.Funcs, outFunc{
					Pkg:     p.ImportPath,
					Name:    fd.Name.Name,
					Params:  params,
					Results: results,
					Doc:     docText(fd.Doc),
				})
					continue
				}

				// Exported method on exported struct receiver type.
				if fd.Recv.List == nil || len(fd.Recv.List) == 0 || fd.Recv.List[0] == nil || fd.Recv.List[0].Type == nil {
					continue
				}
				rt := renderType(fd.Recv.List[0].Type, im)
				if rt == "" {
					continue
				}
				recv := strings.TrimPrefix(rt, "*")
				if recv == "" || !ast.IsExported(recv) {
					continue
				}
				if !structNames[recv] {
					continue
				}

				params := fieldListTypes(fd.Type.Params, im)
				results := fieldListTypes(fd.Type.Results, im)
				if params == nil || results == nil {
					continue
				}
				out.Methods = append(out.Methods, outMethod{
					Pkg:     p.ImportPath,
					Recv:    recv,
					Name:    fd.Name.Name,
					Params:  params,
					Results: results,
					Doc:     docText(fd.Doc),
				})
			}
		}
		if len(structNames) > 0 {
			items := make([]string, 0, len(structNames))
			for n := range structNames {
				items = append(items, n)
			}
			out.StructTypes[p.ImportPath] = items
		}
		if len(structFields) > 0 {
			items := make([]outStruct, 0, len(structFields))
			for n, fields := range structFields {
				items = append(items, outStruct{Name: n, Fields: fields})
			}
			out.Structs[p.ImportPath] = items
		}
	}

	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	_ = enc.Encode(out)
}

func isInternalPkg(importPath string) bool {
	return strings.Contains(importPath, "/internal/") || strings.HasSuffix(importPath, "/internal")
}

func listPkgs() ([]goListPkg, error) {
	cmd := exec.Command("go", "list", "-json", "./...")
	var buf bytes.Buffer
	cmd.Stdout = &buf
	cmd.Stderr = &buf
	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("go list failed: %v\n%s", err, buf.String())
	}

	dec := json.NewDecoder(&buf)
	pkgs := []goListPkg{}
	for {
		var p goListPkg
		if err := dec.Decode(&p); err != nil {
			if errors.Is(err, io.EOF) {
				break
			}
			return nil, fmt.Errorf("failed to decode go list json: %v", err)
		}
		pkgs = append(pkgs, p)
	}
	return pkgs, nil
}

func fieldListTypes(fl *ast.FieldList, im map[string]string) []string {
	if fl == nil || fl.List == nil {
		return []string{}
	}
	out := []string{}
	for _, f := range fl.List {
		if f == nil || f.Type == nil {
			return nil
		}
		t := renderType(f.Type, im)
		if t == "" {
			return nil
		}
		n := 1
		if len(f.Names) > 0 {
			n = len(f.Names)
		}
		for i := 0; i < n; i++ {
			out = append(out, t)
		}
	}
	return out
}

func docText(cg *ast.CommentGroup) string {
	if cg == nil {
		return ""
	}
	return strings.TrimSpace(cg.Text())
}

func collectStructTypes(af *ast.File, im map[string]string, out map[string]bool, fieldsOut map[string][]outStructField) {
	for _, decl := range af.Decls {
		gd, ok := decl.(*ast.GenDecl)
		if !ok || gd.Tok != token.TYPE {
			continue
		}
		for _, spec := range gd.Specs {
			ts, ok := spec.(*ast.TypeSpec)
			if !ok || ts.Name == nil {
				continue
			}
			st, ok := ts.Type.(*ast.StructType)
			if ok {
				out[ts.Name.Name] = true
				if st.Fields != nil {
					// Record exported fields and their types for schema exchange.
					fields := []outStructField{}
					for _, f := range st.Fields.List {
						if f == nil || f.Type == nil {
							continue
						}
						t := renderType(f.Type, im)
						if t == "" {
							continue
						}
						tag := ""
						if f.Tag != nil {
							if s, err := strconv.Unquote(f.Tag.Value); err == nil {
								tag = s
							}
						}
						mpTag := reflect.StructTag(tag).Get("msgpack")
						jsTag := reflect.StructTag(tag).Get("json")
						// Ignore semantics follow canonical precedence: msgpack tag if present, else json.
						if mpTag != "" {
							if tagIgnored(mpTag) {
								continue
							}
						} else if jsTag != "" {
							if tagIgnored(jsTag) {
								continue
							}
						}
						omitempty := false
						if mpTag != "" {
							omitempty = tagHasOption(mpTag, "omitempty")
						} else if jsTag != "" {
							omitempty = tagHasOption(jsTag, "omitempty")
						}

						msgpackKey := tagName(mpTag)
						jsonKey := tagName(jsTag)

						if len(f.Names) == 0 {
							// Embedded (anonymous) field: use the type name as the Go field name.
							base := strings.TrimPrefix(t, "*")
							if i := strings.LastIndex(base, "."); i >= 0 {
								base = base[i+1:]
							}
							if i := strings.LastIndex(base, "/"); i >= 0 {
								base = base[i+1:]
							}
							if !ast.IsExported(base) {
								continue
							}
							key := base
							if msgpackKey != "" {
								key = msgpackKey
							} else if jsonKey != "" {
								key = jsonKey
							}
							aliases := map[string]bool{}
							aliases[base] = true
							if msgpackKey != "" {
								aliases[msgpackKey] = true
							}
							if jsonKey != "" {
								aliases[jsonKey] = true
							}
							alist := make([]string, 0, len(aliases))
							for a := range aliases {
								alist = append(alist, a)
							}
							fields = append(fields, outStructField{Name: base, Type: t, Key: key, Aliases: alist, OmitEmpty: omitempty, Embedded: true})
							continue
						}
						for _, nm := range f.Names {
							if nm == nil || !nm.IsExported() {
								continue
							}
							key := nm.Name
							if msgpackKey != "" {
								key = msgpackKey
							} else if jsonKey != "" {
								key = jsonKey
							}
							aliases := map[string]bool{}
							aliases[nm.Name] = true
							if msgpackKey != "" {
								aliases[msgpackKey] = true
							}
							if jsonKey != "" {
								aliases[jsonKey] = true
							}
							alist := make([]string, 0, len(aliases))
							for a := range aliases {
								alist = append(alist, a)
							}
							fields = append(fields, outStructField{Name: nm.Name, Type: t, Key: key, Aliases: alist, OmitEmpty: omitempty, Embedded: false})
						}
					}
					if len(fields) > 0 {
						fieldsOut[ts.Name.Name] = fields
					}
				}
			}
		}
	}
}

func tagName(tag string) string {
	if tag == "" {
		return ""
	}
	n := tag
	for i := 0; i < len(n); i++ {
		if n[i] == ',' {
			n = n[:i]
			break
		}
	}
	if n == "-" {
		return ""
	}
	return n
}

func tagIgnored(tag string) bool {
	if tag == "" {
		return false
	}
	// `-` or `-,omitempty` etc.
	if tag[0] == '-' {
		return true
	}
	return false
}

func tagHasOption(tag string, opt string) bool {
	if tag == "" || opt == "" {
		return false
	}
	// Fast path: options always occur after the first comma.
	i := strings.IndexByte(tag, ',')
	if i < 0 {
		return false
	}
	opts := tag[i+1:]
	for _, part := range strings.Split(opts, ",") {
		if part == opt {
			return true
		}
	}
	return false
}

func renderType(e ast.Expr, im map[string]string) string {
	switch t := e.(type) {
	case *ast.Ident:
		return t.Name
	case *ast.Ellipsis:
		inner := renderType(t.Elt, im)
		if inner == "" {
			return ""
		}
		return "..." + inner
	case *ast.ArrayType:
		if t.Len != nil {
			return ""
		}
		inner := renderType(t.Elt, im)
		if inner == "" {
			return ""
		}
		return "[]" + inner
	case *ast.MapType:
		k := renderType(t.Key, im)
		if k != "string" {
			return ""
		}
		v := renderType(t.Value, im)
		if v == "" {
			return ""
		}
		return "map[string]" + v
	case *ast.SelectorExpr:
		p := renderType(t.X, im)
		if p == "" {
			return ""
		}
		// Canonicalize well-known adapter types based on import path, regardless of local alias.
		if path, ok := im[p]; ok {
			if path == "github.com/google/uuid" && t.Sel.Name == "UUID" {
				return "uuid.UUID"
			}
		}
		return p + "." + t.Sel.Name
	case *ast.StarExpr:
		inner := renderType(t.X, im)
		if inner == "" {
			return ""
		}
		return "*" + inner
	case *ast.ParenExpr:
		return renderType(t.X, im)
	default:
		return ""
	}
}

func fileImports(af *ast.File) map[string]string {
	out := map[string]string{}
	if af == nil {
		return out
	}
	for _, imp := range af.Imports {
		if imp == nil || imp.Path == nil {
			continue
		}
		path, err := strconv.Unquote(imp.Path.Value)
		if err != nil || path == "" {
			continue
		}
		name := ""
		if imp.Name != nil {
			name = imp.Name.Name
			// Skip blank identifier and dot imports.
			if name == "_" || name == "." {
				continue
			}
		} else {
			name = defaultImportName(path)
		}
		if name == "" {
			continue
		}
		out[name] = path
	}
	return out
}

func defaultImportName(path string) string {
	i := strings.LastIndex(path, "/")
	if i < 0 {
		return path
	}
	return path[i+1:]
}
'''

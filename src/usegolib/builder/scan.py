from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from ..errors import BuildError
from .symbols import ExportedFunc, ModuleScan, StructField


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

        proc = subprocess.run(
            ["go", "run", ".", "--module-dir", str(module_dir)],
            cwd=str(scan_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
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
            if not isinstance(pkg, str) or not isinstance(name, str):
                continue
            if not isinstance(params, list) or not isinstance(results, list):
                continue
            if not all(isinstance(t, str) for t in params):
                continue
            if not all(isinstance(t, str) for t in results):
                continue
            funcs.append(ExportedFunc(pkg=pkg, name=name, params=list(params), results=list(results)))

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
                        if isinstance(fn, str) and isinstance(ft, str) and fn and ft:
                            out_fields.append(StructField(name=fn, type=ft))
                    by_name[name] = out_fields
                if by_name:
                    structs_by_pkg[pkg] = by_name

        return ModuleScan(
            funcs=funcs,
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
}

type outObj struct {
	Funcs []outFunc `json:"funcs"`
	StructTypes map[string][]string `json:"struct_types"`
	Structs map[string][]outStruct `json:"structs"`
}

type outStructField struct {
	Name string `json:"name"`
	Type string `json:"type"`
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
			af, err := parser.ParseFile(fs, file, nil, 0)
			if err != nil {
				continue
			}
			collectStructTypes(af, structNames, structFields)
			for _, decl := range af.Decls {
				fd, ok := decl.(*ast.FuncDecl)
				if !ok {
					continue
				}
				if fd.Recv != nil {
					continue
				}
				if fd.Name == nil || !fd.Name.IsExported() {
					continue
				}
				// Skip generic functions for v0.
				if fd.Type != nil && fd.Type.TypeParams != nil && len(fd.Type.TypeParams.List) > 0 {
					continue
				}

				params := fieldListTypes(fd.Type.Params)
				results := fieldListTypes(fd.Type.Results)
				if params == nil || results == nil {
					continue
				}

				out.Funcs = append(out.Funcs, outFunc{
					Pkg:     p.ImportPath,
					Name:    fd.Name.Name,
					Params:  params,
					Results: results,
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

func fieldListTypes(fl *ast.FieldList) []string {
	if fl == nil || fl.List == nil {
		return []string{}
	}
	out := []string{}
	for _, f := range fl.List {
		if f == nil || f.Type == nil {
			return nil
		}
		t := renderType(f.Type)
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

func collectStructTypes(af *ast.File, out map[string]bool, fieldsOut map[string][]outStructField) {
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
						if f == nil || f.Type == nil || len(f.Names) == 0 {
							continue
						}
						t := renderType(f.Type)
						if t == "" {
							continue
						}
						for _, nm := range f.Names {
							if nm == nil || !nm.IsExported() {
								continue
							}
							fields = append(fields, outStructField{Name: nm.Name, Type: t})
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

func renderType(e ast.Expr) string {
	switch t := e.(type) {
	case *ast.Ident:
		return t.Name
	case *ast.ArrayType:
		if t.Len != nil {
			return ""
		}
		inner := renderType(t.Elt)
		if inner == "" {
			return ""
		}
		return "[]" + inner
	case *ast.MapType:
		k := renderType(t.Key)
		if k != "string" {
			return ""
		}
		v := renderType(t.Value)
		if v == "" {
			return ""
		}
		return "map[string]" + v
	case *ast.SelectorExpr:
		p := renderType(t.X)
		if p == "" {
			return ""
		}
		return p + "." + t.Sel.Name
	case *ast.StarExpr:
		inner := renderType(t.X)
		if inner == "" {
			return ""
		}
		return "*" + inner
	case *ast.ParenExpr:
		return renderType(t.X)
	default:
		return ""
	}
}
'''

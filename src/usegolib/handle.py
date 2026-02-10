"""Handles returned to Python user code."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from . import abi
from .artifact import ArtifactManifest
from .errors import (
    ABIDecodeError,
    ABIEncodeError,
    GoError,
    GoPanicError,
    LoadError,
    UnsupportedSignatureError,
    UnsupportedTypeError,
    UseGoLibError,
    VersionConflictError,
)
from .runtime.cbridge import SharedLibClient
from .schema import (
    Schema,
    validate_call_args,
    validate_call_result,
    validate_method_args,
    validate_method_result,
    validate_struct_value,
)
from .runtime.platform import host_goarch, host_goos


@dataclass(frozen=True)
class _Runtime:
    module: str
    version: str
    abi_version: int
    client: SharedLibClient


_LOADED_RUNTIMES: dict[str, _Runtime] = {}


def _loaded_version_for_package(pkg: str) -> str | None:
    """Return the already-loaded module version for `pkg` (module or subpackage).

    This allows `import_(..., version=None)` for subpackages to follow the already
    loaded module version in the current process, avoiding ambiguity when multiple
    artifact versions exist on disk.
    """
    best_key = None
    for mod in _LOADED_RUNTIMES.keys():
        if pkg == mod or pkg.startswith(mod + "/"):
            if best_key is None or len(mod) > len(best_key):
                best_key = mod
    if best_key is None:
        return None
    return _LOADED_RUNTIMES[best_key].version


def _pack_variadic_args(*, params: list[str], args: list[Any]) -> list[Any]:
    """Pack Python varargs for Go variadic parameters.

    Go variadics are represented in the ABI as a single final argument: a list of
    elements. This enables `f(1, 2, 3)` in Python to map to `f(...T)` in Go.
    """
    if not params:
        return args
    if not params[-1].strip().startswith("..."):
        return args

    fixed = len(params) - 1
    if len(args) < fixed:
        # Missing required fixed args; let schema validation raise a good error.
        return args

    if len(args) == fixed:
        # No variadic args provided.
        return [*args, []]

    # If the caller already provided the packed variadic list, don't repack.
    if len(args) == len(params) and isinstance(args[-1], (list, tuple)):
        return args

    tail = list(args[fixed:])
    return [*args[:fixed], tail]


def _format_go_sig(*, pkg: str, name: str, params: list[str], results: list[str], recv: str | None = None) -> str:
    if recv is None:
        head = f"{pkg}.{name}"
    else:
        head = f"(*{recv}).{name}"
    p = ", ".join(params)
    if not results:
        r = ""
    elif len(results) == 1:
        r = results[0]
    else:
        r = ", ".join(results)
        r = f"({r})"
    return f"Go: {head}({p}){(' ' + r) if r else ''}"


def _attach_doc(*, fn: Callable[..., Any], doc: str | None, sig: str | None) -> None:
    """Best-effort attach __doc__ to a dynamic callable."""
    doc = (doc or "").strip()
    sig = (sig or "").strip()
    if doc and sig:
        fn.__doc__ = f"{doc}\n\n{sig}"
        return
    if doc:
        fn.__doc__ = doc
        return
    if sig:
        fn.__doc__ = sig


def _opaque_ptr_target(*, schema: Schema, pkg: str, go_type: str) -> str | None:
    """If go_type is `*T` for an opaque struct T, return `T` else None.

    Opaque structs are represented in the manifest schema as struct entries with
    zero exported fields. For pointers to those structs, the runtime uses object
    handles (uint64 ids) instead of record dicts.
    """
    t = go_type.strip()
    if not t.startswith("*"):
        return None
    inner = t[1:].strip()
    if not inner or inner.startswith(("[]", "map[string]", "...", "*")):
        return None
    st = schema.structs_by_pkg.get(pkg, {}).get(inner)
    if st is None:
        return None
    if st.fields_by_name:
        return None
    return inner


@dataclass
class PackageHandle:
    module: str
    version: str
    abi_version: int
    package: str
    _client: SharedLibClient
    _schema: Schema | None = None
    _var_cache: dict[str, "GoObject"] = field(default_factory=dict, repr=False)

    @classmethod
    def from_manifest(cls, manifest: ArtifactManifest, *, package: str) -> "PackageHandle":
        existing = _LOADED_RUNTIMES.get(manifest.module)
        if existing is not None and existing.version != manifest.version:
            raise VersionConflictError(
                f"module {manifest.module} already loaded as {existing.version}, "
                f"cannot load {manifest.version}"
            )

        if existing is None:
            _verify_library_sha256(manifest)
            existing = _Runtime(
                module=manifest.module,
                version=manifest.version,
                abi_version=manifest.abi_version,
                client=SharedLibClient(manifest.library_path),
            )
            _LOADED_RUNTIMES[manifest.module] = existing

        schema = Schema.from_manifest(manifest.schema)
        return cls(
            module=existing.module,
            version=existing.version,
            abi_version=existing.abi_version,
            package=package,
            _client=existing.client,
            _schema=schema,
        )

    def __getattr__(self, name: str) -> Callable[..., Any]:
        # Exported package variables can be used as namespace singletons (e.g. isr.DL.Of()).
        # When schema declares a var, resolve it to an object handle so methods can be called.
        if self._schema is not None:
            vt = self._schema.vars_by_pkg.get(self.package, {}).get(name)
            if vt is not None:
                existing = self._var_cache.get(name)
                if existing is not None:
                    return existing

                fn = f"__usegolib_getvar_{name}"
                try:
                    req = abi.encode_call_request(pkg=self.package, fn=fn, args=[])
                except Exception as e:  # noqa: BLE001 - encode boundary
                    raise ABIEncodeError(str(e)) from e

                resp_bytes = self._client.call(req)
                resp = abi.decode_response(resp_bytes)
                if resp.ok:
                    if not isinstance(resp.result, int) or isinstance(resp.result, bool):
                        raise ABIDecodeError("getvar: expected integer object id")
                    obj = GoObject(_pkg=self, _type=vt, _id=resp.result)
                    self._var_cache[name] = obj
                    return obj

                err = resp.error
                if err is None:
                    raise ABIDecodeError("missing error object in failed response")
                if err.type == "GoError":
                    raise GoError(err.message)
                if err.type == "GoPanicError":
                    raise GoPanicError(err.message)
                raise UseGoLibError(f"{err.type}: {err.message}")

        # Treat any missing attribute as a Go function call.
        def _call(*args: Any) -> Any:
            args_list = list(args)
            result_go_type: str | None = None
            if self._schema is not None:
                sig = self._schema.symbols_by_pkg.get(self.package, {}).get(name)
                if sig is not None:
                    params, _results = sig
                    args_list = _pack_variadic_args(params=params, args=args_list)
                    if _results:
                        result_go_type = _results[0]

                # Allow passing generated dataclasses; encode them to record-struct dicts first.
                from .typed import encode_value

                args_list = [
                    encode_value(schema=self._schema, pkg=self.package, v=a) for a in args_list
                ]
                validate_call_args(schema=self._schema, pkg=self.package, fn=name, args=args_list)
            try:
                req = abi.encode_call_request(pkg=self.package, fn=name, args=args_list)
            except Exception as e:  # noqa: BLE001 - encode boundary
                raise ABIEncodeError(str(e)) from e

            resp_bytes = self._client.call(req)
            resp = abi.decode_response(resp_bytes)
            if resp.ok:
                if self._schema is not None:
                    validate_call_result(
                        schema=self._schema,
                        pkg=self.package,
                        fn=name,
                        result=resp.result,
                    )
                    if result_go_type is not None:
                        type_name = _opaque_ptr_target(
                            schema=self._schema, pkg=self.package, go_type=result_go_type
                        )
                        if type_name is not None:
                            if not isinstance(resp.result, int) or isinstance(resp.result, bool):
                                raise ABIDecodeError(
                                    f"expected integer object id for opaque pointer result {result_go_type}"
                                )
                            return GoObject(_pkg=self, _type=type_name, _id=resp.result)
                return resp.result

            err = resp.error
            if err is None:
                raise ABIDecodeError("missing error object in failed response")

            if err.type == "GoError":
                raise GoError(err.message)
            if err.type == "GoPanicError":
                raise GoPanicError(err.message)
            if err.type == "UnsupportedTypeError":
                raise UnsupportedTypeError(err.message)
            if err.type == "UnsupportedSignatureError":
                raise UnsupportedSignatureError(err.message)

            raise UseGoLibError(f"{err.type}: {err.message}")

        if self._schema is not None:
            doc = self._schema.symbol_docs_by_pkg.get(self.package, {}).get(name)
            sig = self._schema.symbols_by_pkg.get(self.package, {}).get(name)
            sig_txt = None
            if sig is not None:
                params, results = sig
                sig_txt = _format_go_sig(pkg=self.package, name=name, params=params, results=results)
            _attach_doc(fn=_call, doc=doc, sig=sig_txt)

        return _call

    @property
    def schema(self) -> Schema | None:
        return self._schema

    def typed(self) -> "TypedPackageHandle":
        return TypedPackageHandle(self)

    def generic(self, name: str, type_args: list[str]) -> Callable[..., Any]:
        if self._schema is None:
            raise UseGoLibError("generic() requires manifest schema")
        sym = (
            self._schema.generics_by_pkg.get(self.package, {})
            .get(name, {})
            .get(tuple(type_args))
        )
        if sym is None:
            raise UseGoLibError(f"generic instantiation not found: {self.package}.{name}{type_args!r}")
        return getattr(self, sym)

    def object(self, type_name: str, init: Any | None = None) -> "GoObject":
        if self._schema is not None and init is not None:
            from .typed import encode_value

            init = encode_value(schema=self._schema, pkg=self.package, v=init)
            validate_struct_value(schema=self._schema, pkg=self.package, struct=type_name, value=init)
        try:
            req = abi.encode_obj_new_request(pkg=self.package, type_name=type_name, init=init)
        except Exception as e:  # noqa: BLE001 - encode boundary
            raise ABIEncodeError(str(e)) from e

        resp_bytes = self._client.call(req)
        resp = abi.decode_response(resp_bytes)
        if resp.ok:
            if not isinstance(resp.result, int) or isinstance(resp.result, bool):
                raise ABIDecodeError("obj_new: expected integer object id")
            return GoObject(_pkg=self, _type=type_name, _id=resp.result)

        err = resp.error
        if err is None:
            raise ABIDecodeError("missing error object in failed response")
        if err.type == "GoError":
            raise GoError(err.message)
        if err.type == "GoPanicError":
            raise GoPanicError(err.message)
        if err.type == "UnsupportedTypeError":
            raise UnsupportedTypeError(err.message)
        if err.type == "UnsupportedSignatureError":
            raise UnsupportedSignatureError(err.message)
        raise UseGoLibError(f"{err.type}: {err.message}")


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:  # noqa: PTH123 - runtime file read
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_library_sha256(manifest: ArtifactManifest) -> None:
    goos = host_goos()
    goarch = host_goarch()
    if manifest.goos != goos or manifest.goarch != goarch:
        raise LoadError(
            f"artifact platform mismatch: manifest {manifest.goos}/{manifest.goarch}, host {goos}/{goarch}"
        )

    want = (manifest.library_sha256 or "").strip()
    if not want:
        raise LoadError("manifest missing library.sha256")
    if not _SHA256_RE.fullmatch(want):
        raise LoadError("manifest library.sha256 must be 64 lowercase hex characters")

    lib_path = manifest.library_path
    if not lib_path.exists():
        raise LoadError(f"shared library not found at {lib_path}")
    got = _sha256_file(lib_path)
    if got != want:
        raise LoadError(f"shared library sha256 mismatch: expected {want}, got {got}")


@dataclass(frozen=True)
class TypedPackageHandle:
    """Typed wrapper around PackageHandle.

    It decodes record-struct results into generated dataclasses based on the
    manifest schema (when available).
    """

    _base: PackageHandle
    _types: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self._base._schema is None:  # noqa: SLF001 - internal linkage
            raise UseGoLibError("typed handle requires manifest schema")
        from .typed import make_package_types

        schema = self._base._schema  # noqa: SLF001 - internal linkage
        assert schema is not None
        object.__setattr__(self, "_types", make_package_types(schema=schema, pkg=self._base.package))

    @property
    def types(self):
        return self._types

    def __getattr__(self, name: str) -> Callable[..., Any]:
        fn = getattr(self._base, name)
        schema = self._base._schema  # noqa: SLF001 - internal linkage
        assert schema is not None

        def _call(*args: Any) -> Any:
            result = fn(*args)
            sig = schema.symbols_by_pkg.get(self._base.package, {}).get(name)
            if sig is None:
                return result
            _params, results = sig
            if not results:
                return result
            from .typed import decode_value

            return decode_value(types=self._types, go_type=results[0], v=result)

        # Preserve docstrings from the base callable (GoDoc/signature).
        _call.__doc__ = getattr(fn, "__doc__", None)
        return _call

    def object(self, type_name: str, init: Any | None = None) -> "TypedGoObject":
        obj = self._base.object(type_name, init=init)
        schema = self._base._schema  # noqa: SLF001 - internal linkage
        assert schema is not None
        return TypedGoObject(_base=obj, _types=self._types, _schema=schema, _pkg=self._base.package)

    def generic(self, name: str, type_args: list[str]) -> Callable[..., Any]:
        schema = self._base._schema  # noqa: SLF001 - internal linkage
        assert schema is not None
        sym = schema.generics_by_pkg.get(self._base.package, {}).get(name, {}).get(tuple(type_args))
        if sym is None:
            raise UseGoLibError(f"generic instantiation not found: {self._base.package}.{name}{type_args!r}")
        fn = getattr(self._base, sym)

        def _call(*args: Any) -> Any:
            result = fn(*args)
            sig = schema.symbols_by_pkg.get(self._base.package, {}).get(sym)
            if sig is None:
                return result
            _params, results = sig
            if not results:
                return result
            from .typed import decode_value

            return decode_value(types=self._types, go_type=results[0], v=result)

        _call.__doc__ = getattr(fn, "__doc__", None)
        return _call


@dataclass
class GoObject:
    _pkg: PackageHandle
    _type: str
    _id: int
    _closed: bool = False

    @property
    def id(self) -> int:
        return self._id

    @property
    def type_name(self) -> str:
        return self._type

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            req = abi.encode_obj_free_request(obj_id=self._id)
        except Exception:
            return
        try:
            _ = self._pkg._client.call(req)  # noqa: SLF001 - internal linkage
        except Exception:
            return

    def __enter__(self) -> "GoObject":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self.close()

    def __del__(self) -> None:
        # Best-effort cleanup; ignore errors at interpreter shutdown.
        try:
            self.close()
        except Exception:
            return

    def __getattr__(self, name: str) -> Callable[..., Any]:
        def _call(*args: Any) -> Any:
            if self._closed:
                raise UseGoLibError("object is closed")
            args_list = list(args)
            schema = self._pkg._schema  # noqa: SLF001 - internal linkage
            result_go_type: str | None = None
            if schema is not None:
                sig = (
                    schema.methods_by_pkg.get(self._pkg.package, {})
                    .get(self._type, {})
                    .get(name)
                )
                if sig is not None:
                    params, _results = sig
                    args_list = _pack_variadic_args(params=params, args=args_list)
                    if _results:
                        result_go_type = _results[0]

                from .typed import encode_value

                args_list = [encode_value(schema=schema, pkg=self._pkg.package, v=a) for a in args_list]
                validate_method_args(
                    schema=schema,
                    pkg=self._pkg.package,
                    recv=self._type,
                    method=name,
                    args=args_list,
                )
            try:
                req = abi.encode_obj_call_request(
                    pkg=self._pkg.package,
                    type_name=self._type,
                    obj_id=self._id,
                    method=name,
                    args=args_list,
                )
            except Exception as e:  # noqa: BLE001 - encode boundary
                raise ABIEncodeError(str(e)) from e

            resp_bytes = self._pkg._client.call(req)  # noqa: SLF001 - internal linkage
            resp = abi.decode_response(resp_bytes)
            if resp.ok:
                if schema is not None:
                    validate_method_result(
                        schema=schema,
                        pkg=self._pkg.package,
                        recv=self._type,
                        method=name,
                        result=resp.result,
                    )
                    if result_go_type is not None:
                        type_name = _opaque_ptr_target(
                            schema=schema, pkg=self._pkg.package, go_type=result_go_type
                        )
                        if type_name is not None:
                            if not isinstance(resp.result, int) or isinstance(resp.result, bool):
                                raise ABIDecodeError(
                                    f"expected integer object id for opaque pointer result {result_go_type}"
                                )
                            return GoObject(_pkg=self._pkg, _type=type_name, _id=resp.result)
                return resp.result

            err = resp.error
            if err is None:
                raise ABIDecodeError("missing error object in failed response")
            if err.type == "GoError":
                raise GoError(err.message)
            if err.type == "GoPanicError":
                raise GoPanicError(err.message)
            if err.type == "UnsupportedTypeError":
                raise UnsupportedTypeError(err.message)
            if err.type == "UnsupportedSignatureError":
                raise UnsupportedSignatureError(err.message)
            raise UseGoLibError(f"{err.type}: {err.message}")

        schema = self._pkg._schema  # noqa: SLF001 - internal linkage
        if schema is not None:
            doc = (
                schema.method_docs_by_pkg.get(self._pkg.package, {})
                .get(self._type, {})
                .get(name)
            )
            sig = (
                schema.methods_by_pkg.get(self._pkg.package, {})
                .get(self._type, {})
                .get(name)
            )
            sig_txt = None
            if sig is not None:
                params, results = sig
                sig_txt = _format_go_sig(
                    pkg=self._pkg.package, recv=self._type, name=name, params=params, results=results
                )
            _attach_doc(fn=_call, doc=doc, sig=sig_txt)

        return _call


@dataclass(frozen=True)
class TypedGoObject:
    _base: GoObject
    _types: Any
    _schema: Schema
    _pkg: str

    @property
    def id(self) -> int:
        return self._base.id

    @property
    def type_name(self) -> str:
        return self._base.type_name

    def close(self) -> None:
        self._base.close()

    def __enter__(self) -> "TypedGoObject":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self.close()

    def __getattr__(self, name: str) -> Callable[..., Any]:
        fn = getattr(self._base, name)

        def _call(*args: Any) -> Any:
            result = fn(*args)
            sig = self._schema.methods_by_pkg.get(self._pkg, {}).get(self._base.type_name, {}).get(name)
            if sig is None:
                return result
            _params, results = sig
            if not results:
                return result
            from .typed import decode_value

            return decode_value(types=self._types, go_type=results[0], v=result)

        _call.__doc__ = getattr(fn, "__doc__", None)
        return _call

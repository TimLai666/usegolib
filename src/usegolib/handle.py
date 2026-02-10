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


@dataclass
class PackageHandle:
    module: str
    version: str
    abi_version: int
    package: str
    _client: SharedLibClient
    _schema: Schema | None = None

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
        # Treat any missing attribute as a Go function call.
        def _call(*args: Any) -> Any:
            args_list = list(args)
            if self._schema is not None:
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
            if schema is not None:
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

        return _call

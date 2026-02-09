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
from .schema import Schema, validate_call_args, validate_call_result


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


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:  # noqa: PTH123 - runtime file read
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_library_sha256(manifest: ArtifactManifest) -> None:
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

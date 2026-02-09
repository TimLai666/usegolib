"""Handles returned to Python user code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from . import abi
from .artifact import ArtifactManifest
from .errors import (
    ABIDecodeError,
    ABIEncodeError,
    GoError,
    GoPanicError,
    UnsupportedSignatureError,
    UnsupportedTypeError,
    UseGoLibError,
    VersionConflictError,
)
from .runtime.cbridge import SharedLibClient
from .schema import Schema, validate_call_args


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
            if self._schema is not None:
                validate_call_args(schema=self._schema, pkg=self.package, fn=name, args=list(args))
            try:
                req = abi.encode_call_request(pkg=self.package, fn=name, args=list(args))
            except Exception as e:  # noqa: BLE001 - encode boundary
                raise ABIEncodeError(str(e)) from e

            resp_bytes = self._client.call(req)
            resp = abi.decode_response(resp_bytes)
            if resp.ok:
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

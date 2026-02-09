"""Module handle returned to Python user code."""

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

_LOADED_MODULES: dict[str, str] = {}


@dataclass
class ModuleHandle:
    module: str
    version: str
    abi_version: int
    _client: SharedLibClient

    @classmethod
    def from_manifest(cls, manifest: ArtifactManifest) -> "ModuleHandle":
        existing = _LOADED_MODULES.get(manifest.module)
        if existing is not None and existing != manifest.version:
            raise VersionConflictError(
                f"module {manifest.module} already loaded as {existing}, "
                f"cannot load {manifest.version}"
            )
        _LOADED_MODULES[manifest.module] = manifest.version

        client = SharedLibClient(manifest.library_path)
        return cls(
            module=manifest.module,
            version=manifest.version,
            abi_version=manifest.abi_version,
            _client=client,
        )

    def __getattr__(self, name: str) -> Callable[..., Any]:
        # Treat any missing attribute as a Go function call.
        def _call(*args: Any) -> Any:
            try:
                req = abi.encode_call_request(pkg=self.module, fn=name, args=list(args))
            except Exception as e:  # noqa: BLE001 - encode boundary
                raise ABIEncodeError(str(e)) from e
            resp_bytes = self._client.call(req)
            resp = abi.decode_response(resp_bytes)
            if resp.ok:
                return resp.result
            err = resp.error
            if err is None:
                raise ABIDecodeError("missing error object in failed response")

            # Map stable ABI error types to Python exceptions.
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

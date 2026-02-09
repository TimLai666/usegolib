"""MessagePack ABI helpers (v0)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import msgpack

from .errors import ABIDecodeError

ABI_VERSION = 0


@dataclass(frozen=True)
class ABIError:
    type: str
    message: str
    detail: dict[str, Any] | None = None


@dataclass(frozen=True)
class ABIResponse:
    ok: bool
    result: Any | None = None
    error: ABIError | None = None


def encode_call_request(*, pkg: str, fn: str, args: list[Any]) -> bytes:
    payload = {
        "abi": ABI_VERSION,
        "op": "call",
        "pkg": pkg,
        "fn": fn,
        "args": args,
    }
    return msgpack.packb(payload, use_bin_type=True)


def decode_response(payload: bytes) -> ABIResponse:
    try:
        obj = msgpack.unpackb(payload, raw=False)
    except Exception as e:  # noqa: BLE001 - boundary decoding error
        raise ABIDecodeError(str(e)) from e

    if not isinstance(obj, dict) or "ok" not in obj:
        raise ABIDecodeError("invalid response envelope")

    ok = bool(obj.get("ok"))
    if ok:
        return ABIResponse(ok=True, result=obj.get("result"), error=None)

    err = obj.get("error")
    if not isinstance(err, dict):
        raise ABIDecodeError("invalid error envelope")

    return ABIResponse(
        ok=False,
        result=None,
        error=ABIError(
            type=str(err.get("type", "")),
            message=str(err.get("message", "")),
            detail=err.get("detail") if isinstance(err.get("detail"), dict) else None,
        ),
    )


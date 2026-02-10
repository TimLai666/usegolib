from __future__ import annotations

import msgpack


class _FakeClient:
    def __init__(self) -> None:
        self.calls: list[bytes] = []

    def call(self, req: bytes) -> bytes:  # noqa: ANN001
        self.calls.append(req)
        # Return object id 7.
        return msgpack.packb({"ok": True, "result": 7}, use_bin_type=True)


def test_package_handle_var_returns_goobject_and_caches():
    from usegolib.handle import PackageHandle
    from usegolib.schema import Schema

    schema = Schema.from_manifest(
        {
            "structs": {"example.com/p": {"dl": []}},
            "methods": [
                {"pkg": "example.com/p", "recv": "dl", "name": "Of", "params": ["...any"], "results": ["*dl"]}
            ],
            "vars": [{"pkg": "example.com/p", "name": "DL", "type": "dl"}],
        }
    )
    assert schema is not None

    h = PackageHandle(
        module="example.com/p",
        version="v1.0.0",
        abi_version=0,
        package="example.com/p",
        _client=_FakeClient(),  # type: ignore[arg-type]
        _schema=schema,
    )

    dl1 = h.DL  # type: ignore[attr-defined]
    dl2 = h.DL  # type: ignore[attr-defined]
    assert dl1 is dl2
    assert dl1.type_name == "dl"
    assert dl1.id == 7


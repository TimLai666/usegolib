import msgpack


def test_encode_call_request_roundtrips():
    import usegolib

    req = usegolib.abi.encode_call_request(
        pkg="example.com/mod",
        fn="AddInt",
        args=[1, 2],
    )
    decoded = msgpack.unpackb(req, raw=False)
    assert decoded["abi"] == 0
    assert decoded["op"] == "call"
    assert decoded["pkg"] == "example.com/mod"
    assert decoded["fn"] == "AddInt"
    assert decoded["args"] == [1, 2]


def test_decode_response_ok():
    import usegolib

    payload = msgpack.packb({"ok": True, "result": 123}, use_bin_type=True)
    resp = usegolib.abi.decode_response(payload)
    assert resp.ok is True
    assert resp.result == 123
    assert resp.error is None


def test_decode_response_error():
    import usegolib

    payload = msgpack.packb(
        {"ok": False, "error": {"type": "GoError", "message": "boom"}},
        use_bin_type=True,
    )
    resp = usegolib.abi.decode_response(payload)
    assert resp.ok is False
    assert resp.result is None
    assert resp.error is not None
    assert resp.error.type == "GoError"
    assert resp.error.message == "boom"


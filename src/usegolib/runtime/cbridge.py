"""ctypes binding to the Go shared library C ABI."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path

from ..errors import LoadError


class SharedLibClient:
    def __init__(self, path: Path):
        self._path = Path(path)
        self._lib = None

    def _load(self) -> None:
        if self._lib is not None:
            return
        if not self._path.exists():
            raise LoadError(f"shared library not found: {self._path}")

        try:
            if os.name == "nt":
                lib = ctypes.WinDLL(str(self._path))
            else:
                lib = ctypes.CDLL(str(self._path))
        except OSError as e:
            raise LoadError(str(e)) from e

        # int usegolib_call(uint8_t* req, size_t req_len, uint8_t** resp, size_t* resp_len)
        lib.usegolib_call.argtypes = [
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_size_t),
        ]
        lib.usegolib_call.restype = ctypes.c_int

        lib.usegolib_free.argtypes = [ctypes.c_void_p]
        lib.usegolib_free.restype = None

        self._lib = lib

    def call(self, request: bytes) -> bytes:
        self._load()
        assert self._lib is not None

        req_buf = ctypes.create_string_buffer(request)
        resp_ptr = ctypes.c_void_p()
        resp_len = ctypes.c_size_t()

        rc = self._lib.usegolib_call(
            ctypes.cast(req_buf, ctypes.c_void_p),
            ctypes.c_size_t(len(request)),
            ctypes.byref(resp_ptr),
            ctypes.byref(resp_len),
        )
        try:
            if rc != 0:
                raise LoadError(f"usegolib_call failed with code {rc}")
            data = ctypes.string_at(resp_ptr, resp_len.value)
            return data
        finally:
            if resp_ptr.value:
                self._lib.usegolib_free(resp_ptr)


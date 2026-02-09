from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path

from ..errors import BuildError


@contextmanager
def leaf_lock(lock_path: Path, *, timeout_s: float = 600.0, poll_s: float = 0.1):
    """Cross-platform exclusive file lock for build output directories."""
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    f = lock_path.open("a+b")
    try:
        _lock_file(f, timeout_s=timeout_s, poll_s=poll_s)
        yield
    finally:
        try:
            _unlock_file(f)
        finally:
            f.close()


def _lock_file(f, *, timeout_s: float, poll_s: float) -> None:
    deadline = time.time() + timeout_s
    if os.name == "nt":
        import msvcrt

        while True:
            try:
                # Lock 1 byte region.
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                if time.time() >= deadline:
                    raise BuildError("timed out waiting for build lock")
                time.sleep(poll_s)
    else:
        import fcntl

        while True:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except OSError:
                if time.time() >= deadline:
                    raise BuildError("timed out waiting for build lock")
                time.sleep(poll_s)


def _unlock_file(f) -> None:
    if os.name == "nt":
        import msvcrt

        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            return
    else:
        import fcntl

        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except OSError:
            return


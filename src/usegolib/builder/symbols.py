from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExportedFunc:
    pkg: str
    name: str
    params: list[str]
    results: list[str]


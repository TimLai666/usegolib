from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExportedFunc:
    pkg: str
    name: str
    params: list[str]
    results: list[str]


@dataclass(frozen=True)
class ModuleScan:
    funcs: list[ExportedFunc]
    struct_types_by_pkg: dict[str, set[str]]

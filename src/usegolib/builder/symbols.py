from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExportedFunc:
    pkg: str
    name: str
    params: list[str]
    results: list[str]


@dataclass(frozen=True)
class ExportedMethod:
    pkg: str
    recv: str  # receiver struct type name (no leading '*')
    name: str
    params: list[str]
    results: list[str]


@dataclass(frozen=True)
class StructField:
    name: str
    type: str
    key: str
    aliases: list[str]
    omitempty: bool = False
    embedded: bool = False


@dataclass(frozen=True)
class ModuleScan:
    funcs: list[ExportedFunc]
    methods: list[ExportedMethod]
    struct_types_by_pkg: dict[str, set[str]]
    structs_by_pkg: dict[str, dict[str, list[StructField]]]

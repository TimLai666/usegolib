from __future__ import annotations

import re
import sys
from pathlib import Path


REQ_RE = re.compile(r"^### Requirement:")
SCEN_RE = re.compile(r"^#### Scenario:")


def _validate_spec_text(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    lines = text.splitlines()

    in_req = False
    saw_scenario = False

    def end_requirement(line_no: int) -> None:
        nonlocal in_req, saw_scenario
        if in_req and not saw_scenario:
            errors.append(f"{path}: requirement missing scenario near line {line_no}")
        in_req = False
        saw_scenario = False

    for i, line in enumerate(lines, start=1):
        if REQ_RE.match(line):
            end_requirement(i)
            in_req = True
            continue

        if SCEN_RE.match(line):
            if not in_req:
                errors.append(f"{path}: scenario outside requirement at line {i}")
            saw_scenario = True

    end_requirement(len(lines) + 1)
    return errors


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    roots = [repo / "openspec" / "specs", repo / "openspec" / "changes"]
    spec_files: list[Path] = []
    for r in roots:
        if not r.exists():
            continue
        spec_files.extend([p for p in r.rglob("*.md") if p.name == "spec.md"])

    errors: list[str] = []
    for p in spec_files:
        errors.extend(_validate_spec_text(p, p.read_text(encoding="utf-8")))

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    print(f"openspec ok: {len(spec_files)} spec files checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


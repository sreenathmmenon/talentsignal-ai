from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JobSpec:
    id: str
    title: str
    category: str
    preferred_min_years: float
    preferred_max_years: float
    strongest_min_years: float
    strongest_max_years: float
    preferred_locations: tuple[str, ...]
    country_preferred: str
    must_have: tuple[str, ...]
    nice_to_have: tuple[str, ...]
    disqualifiers: tuple[str, ...]
    weights: dict[str, float]


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_simple_yaml(path: str | Path) -> dict[str, Any]:
    """Parse the small YAML subset used by job_specs without external deps."""
    return _parse_yaml_with_lists(Path(path).read_text(encoding="utf-8").splitlines())


def _parse_yaml_with_lists(lines: list[str]) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any, str | None]] = [(-1, root, None)]
    for i, raw in enumerate(lines):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        text = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if text.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"Unexpected list item: {raw}")
            parent.append(_parse_scalar(text[2:]))
            continue
        key, _, value = text.partition(":")
        key = key.strip()
        value = value.strip()
        if value:
            parent[key] = _parse_scalar(value)
            continue
        next_is_list = False
        for nxt in lines[i + 1 :]:
            if not nxt.strip() or nxt.lstrip().startswith("#"):
                continue
            next_indent = len(nxt) - len(nxt.lstrip(" "))
            next_is_list = next_indent > indent and nxt.strip().startswith("- ")
            break
        container: Any = [] if next_is_list else {}
        parent[key] = container
        stack.append((indent, container, key))
    return root


def load_job_spec(path: str | Path) -> JobSpec:
    data = load_simple_yaml(path)
    exp = data["experience"]
    loc = data["locations"]
    return JobSpec(
        id=str(data["id"]),
        title=str(data["title"]),
        category=str(data["category"]),
        preferred_min_years=float(exp["preferred_min_years"]),
        preferred_max_years=float(exp["preferred_max_years"]),
        strongest_min_years=float(exp["strongest_min_years"]),
        strongest_max_years=float(exp["strongest_max_years"]),
        preferred_locations=tuple(loc["preferred"]),
        country_preferred=str(loc["country_preferred"]),
        must_have=tuple(data["must_have"]),
        nice_to_have=tuple(data["nice_to_have"]),
        disqualifiers=tuple(data["disqualifiers"]),
        weights={k: float(v) for k, v in data["weights"].items()},
    )

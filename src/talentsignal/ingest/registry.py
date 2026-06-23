"""Adapter registry + the public ingest() entry point.

An adapter is a callable that knows how to turn one kind of input into canonical
candidate records. Adapters register against format names; ingest() auto-detects
the format (by extension/content) or takes an explicit `fmt`.

Adding a new input type (e.g. a future GitHub-repo analyzer) is just:
    @register_adapter("github", extensions=[], detect=lambda x: ...)
    def github_adapter(source, **opts) -> list[dict]: ...
No core changes required.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

# format name -> {"fn", "extensions", "detect"}
_ADAPTERS: dict[str, dict[str, Any]] = {}


def register_adapter(name: str, *, extensions: list[str] | None = None,
                     detect: Callable[[Any], bool] | None = None):
    """Decorator to register an ingest adapter."""
    def deco(fn: Callable[..., list[dict[str, Any]]]):
        _ADAPTERS[name] = {"fn": fn, "extensions": [e.lower() for e in (extensions or [])],
                           "detect": detect}
        return fn
    return deco


def list_adapters() -> list[str]:
    return sorted(_ADAPTERS)


def detect_format(source: Any) -> str | None:
    """Best-effort format detection for a single source (path, str, or dict)."""
    # dicts -> json
    if isinstance(source, dict):
        return "json"
    if isinstance(source, (str, Path)):
        p = Path(source)
        # by extension if it looks like a path
        suffix = p.suffix.lower()
        if suffix:
            for name, spec in _ADAPTERS.items():
                if suffix in spec["extensions"]:
                    return name
        # content-based detect callbacks
        for name, spec in _ADAPTERS.items():
            if spec["detect"] and spec["detect"](source):
                return name
        # a path that exists but unknown extension -> text
        try:
            if p.exists() and p.is_file():
                return "text"
        except OSError:
            pass
        # otherwise treat a bare string as pasted text
        return "text"
    return None


def _ingest_one(source: Any, fmt: str | None, **opts) -> list[dict[str, Any]]:
    name = fmt or detect_format(source)
    if name not in _ADAPTERS:
        raise ValueError(f"no ingest adapter for format '{name}' "
                         f"(available: {', '.join(list_adapters())})")
    records = _ADAPTERS[name]["fn"](source, **opts)
    # adapters may return Candidate objects or dicts; normalize to dicts
    from .model import Candidate
    out = []
    for r in records:
        out.append(r.to_record() if isinstance(r, Candidate) else r)
    return out


def ingest(source: Any, fmt: str | None = None, **opts) -> list[dict[str, Any]]:
    """Ingest one source or a list of sources into canonical candidate records.

    source: a path/str/dict, or a list of them (mixed formats allowed).
    fmt: force a format; otherwise auto-detected per source.
    opts: passed to the adapter (e.g. use_llm=True for resume parsing).
    """
    # ensure built-in adapters are registered
    from . import adapters  # noqa: F401  (import side-effect registers them)

    if isinstance(source, list):
        out: list[dict[str, Any]] = []
        for item in source:
            out.extend(_ingest_one(item, fmt, **opts))
        return out
    return _ingest_one(source, fmt, **opts)

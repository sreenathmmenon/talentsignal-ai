from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any, Iterator


def iter_candidates(path: str | Path) -> Iterator[dict[str, Any]]:
    """Yield candidate objects from .jsonl or .jsonl.gz."""
    candidate_path = Path(path)
    opener = gzip.open if candidate_path.suffix == ".gz" else open
    with opener(candidate_path, "rt", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
            if "candidate_id" not in candidate:
                raise ValueError(f"Missing candidate_id on line {line_no}")
            yield candidate


def load_candidates(path: str | Path) -> list[dict[str, Any]]:
    return list(iter_candidates(path))


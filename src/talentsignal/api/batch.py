"""Batch + file ergonomics — the enterprise-scale entry points.

The core rank() takes an in-memory candidate list. At enterprise scale a buyer
has a large candidate FILE (a 200K-row JSONL export) and often many open ROLES.
These helpers cover both without forcing the caller to wire streaming or loops:

  rank_file(jd, path)        : stream a .jsonl/.jsonl.gz candidate file -> ranked
  rank_many_jds(jds, cands)  : rank one candidate pool against many JDs at once
  rank_to_csv(jd, cands, out): rank and write the standard submission CSV

All run on the same engine and return the same typed RankResult, so batch and
single-call paths are identical in quality and shape.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable

from .facade import TalentSignal, rank
from .types import RankResult


def rank_file(
    jd: Any,
    candidates_path: str | Path,
    *,
    top_n: int = 100,
    engine: str = "hybrid",
    index_dir: str | None = None,
    embedder=None,
    category: str = "ai_ml_search_ranking",
) -> RankResult:
    """Rank candidates from a .jsonl / .jsonl.gz file (streamed, not all loaded
    eagerly into a Python list by the caller)."""
    from ..io import iter_candidates
    ts = TalentSignal(index_dir=index_dir, embedder=embedder)
    # iter_candidates streams; the facade materializes only what it needs and
    # hydrates heavy objects for the top_n only.
    return ts.rank(jd, iter_candidates(candidates_path), top_n=top_n,
                   engine=engine, category=category)


def rank_many_jds(
    jds: dict[str, Any],
    candidates: Iterable[dict[str, Any]],
    *,
    top_n: int = 100,
    engine: str = "spine",
    categories: dict[str, str] | None = None,
    default_category: str = "ai_ml_search_ranking",
) -> dict[str, RankResult]:
    """Rank ONE candidate pool against MANY JDs (e.g. all of a company's open
    roles). Returns {jd_key: RankResult}. Materializes the pool once.

    Each JD is scored with its OWN category (so a sales JD uses sales weights, not
    the AI ones) -- pass `categories` as {jd_key: category}; JDs without an entry
    use default_category. A JobSpec passed as a value already carries its
    category and is used as-is.
    """
    pool = list(candidates)
    categories = categories or {}
    out: dict[str, RankResult] = {}
    for key, jd in jds.items():
        cat = categories.get(key, default_category)
        out[key] = rank(jd, pool, top_n=top_n, engine=engine, category=cat)
    return out


def rank_to_csv(
    jd: Any,
    candidates: Iterable[dict[str, Any]],
    out_path: str | Path,
    *,
    top_n: int = 100,
    engine: str = "spine",
    category: str = "ai_ml_search_ranking",
) -> RankResult:
    """Rank and write the standard candidate_id,rank,score,reasoning CSV."""
    result = rank(jd, candidates, top_n=top_n, engine=engine, category=category)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        w.writeheader()
        for row in result.to_csv_rows():
            w.writerow(row)
    return result

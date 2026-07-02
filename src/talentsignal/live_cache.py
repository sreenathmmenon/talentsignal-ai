"""Live, in-memory ranking cache for the product surfaces (Studio, REST).

NO hardcoding: every result here is produced by the real engine on the real
100K candidates. We simply cache the computed ranking in memory so a customer
gets an instant response, and recompute on demand for custom JDs. The standing
("challenge") JD is ranked once on first request and reused until invalidated.

Design:
  * load the 100K candidate records once (lazy, cached),
  * rank with the hybrid engine + precomputed embedding index,
  * memoize by a cache key derived from (jd_text, category, engine, top_n),
  * expose elapsed + engine + freshness so the UI can show it's real.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_DATASET = _ROOT / "[PUB] India_runs_data_and_ai_challenge" / "India_runs_data_and_ai_challenge" / "candidates.jsonl"
_INDEX_DIR = _ROOT / "outputs" / "index"

# The standing challenge JD — full free text, parsed live (not a frozen answer).
CHALLENGE_JD = (
    "Senior AI Engineer — Founding Team.\n\n"
    "You must have shipped retrieval and ranking systems to real users: production "
    "embeddings-based retrieval, vector/hybrid search, and ranking models. Strong "
    "Python. You must have designed evaluation frameworks for ranking (NDCG, MRR, MAP). "
    "We will not move forward with keyword-only AI experience or research with no "
    "production deployment. 5-9 years."
)

_lock = threading.Lock()
_records: list[dict[str, Any]] | None = None
_records_fp: str | None = None        # fingerprint of the loaded candidate pool
_cache: dict[str, dict[str, Any]] = {}


def _file_fingerprint() -> str:
    """Cheap fingerprint of the dataset FILE (size + mtime). Changes whenever the
    file is rewritten — first line of defense against serving a stale dataset."""
    if not _DATASET.exists():
        return "absent"
    st = _DATASET.stat()
    return f"{st.st_size}:{int(st.st_mtime)}"


def _content_fingerprint(records: list[dict[str, Any]]) -> str:
    """Content fingerprint of the candidate POOL: count + hash of every candidate
    id AND a hash of each candidate's evidence. If a candidate is added, removed,
    or edits their profile, this changes — so the cache cannot serve stale ranks.
    Computed once per (re)load, not per request."""
    h = hashlib.sha1()
    h.update(str(len(records)).encode())
    for r in records:
        h.update((r.get("candidate_id", "") or "").encode())
        # include the fields the engine scores on, so an edit invalidates too
        p = r.get("profile", {}) or {}
        h.update((p.get("headline", "") or "").encode())
        h.update((p.get("summary", "") or "").encode())
        h.update(json.dumps(r.get("skills", []), sort_keys=True).encode())
        h.update(json.dumps(r.get("career_history", []), sort_keys=True).encode())
    return h.hexdigest()[:16]


def _load_records(force: bool = False) -> list[dict[str, Any]]:
    """Load candidates, transparently reloading if the file changed on disk.

    This is what makes the product correct when the candidate list changes: every
    access checks the file fingerprint; if it moved, we reload AND recompute the
    content fingerprint, which invalidates every cached ranking built on the old
    pool (their cache keys no longer match)."""
    global _records, _records_fp
    with _lock:
        cur_file_fp = _file_fingerprint()
        if force or _records is None or cur_file_fp != getattr(_load_records, "_file_fp", None):
            if not _DATASET.exists():
                _records, _records_fp = [], "absent"
            else:
                _records = [json.loads(l) for l in open(_DATASET) if l.strip()]
                _records_fp = _content_fingerprint(_records)
            _load_records._file_fp = cur_file_fp  # type: ignore[attr-defined]
        return _records


def pool_fingerprint() -> str:
    _load_records()
    return _records_fp or "absent"


def dataset_size() -> int:
    return len(_load_records())


def _key(jd: str, category: str, engine: str, top_n: int, pool_fp: str) -> str:
    """Cache key binds the request to the EXACT candidate pool it was computed on.
    Different pool fingerprint -> different key -> guaranteed live re-rank."""
    h = hashlib.sha1(f"{jd}|{category}|{engine}|{top_n}|{pool_fp}".encode()).hexdigest()[:16]
    return h


def _index_dir_or_none() -> str | None:
    return str(_INDEX_DIR) if _INDEX_DIR.exists() else None


def rank_live(jd: str | None = None, *, category: str = "ai_ml_search_ranking",
              engine: str = "hybrid", top_n: int = 20,
              embedder=None, force: bool = False) -> dict[str, Any]:
    """Rank the real 100K live (hybrid + precomputed index), memoized in memory.

    Returns a JSON-serializable payload with the ranked candidates AND proof that
    it is real and dynamic: elapsed seconds, engine used, dataset size, cache flag.
    """
    from .api import rank as _rank

    # Use the SAME job spec the submission (rank.py) uses, so the UI's 100K ranking
    # is the identical computation to the CSV/XLSX — same parsed requirements AND the
    # same precomputed requirement embeddings in the index. (Falls back to the text
    # JD only if the spec file is missing.)
    if jd is None:
        from pathlib import Path as _Path
        _spec = _Path(__file__).resolve().parents[2] / "job_specs" / "redrob_senior_ai_engineer.yaml"
        if _spec.exists():
            from .jd_parser import load_job_spec
            jd = load_job_spec(_spec)
        else:
            jd = CHALLENGE_JD
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    # Load (reloads automatically if the file changed) BEFORE building the key,
    # so the key reflects the current candidate pool — never a stale one.
    records = _load_records()
    if not records:
        return {"error": "dataset not found", "top": [], "total": 0}
    pool_fp = pool_fingerprint()

    key = _key(jd, category, engine, top_n, pool_fp)
    if not force and key in _cache:
        cached = dict(_cache[key])
        cached["from_cache"] = True
        return cached

    by_id = {r["candidate_id"]: r for r in records}
    idx = _index_dir_or_none() if engine == "hybrid" else None
    t = time.time()
    res = _rank(jd, records, top_n=top_n, engine=engine, index_dir=idx,
                embedder=embedder, category=category)
    elapsed = round(time.time() - t, 2)

    top = []
    for i, c in enumerate(res.ranked, 1):
        rec = by_id.get(c.candidate_id, {})
        p = rec.get("profile", {})
        f = c.factors
        top.append({
            "rank": i,
            "candidate_id": c.candidate_id,
            "score": round(c.score, 4),
            "headline": p.get("headline", ""),
            "title": c.title or p.get("current_title", ""),
            "years": c.years,
            "location": c.location or p.get("location", ""),
            "reasoning": c.reasoning,
            "factors": {
                "technical_evidence": round(f.technical_evidence, 2) if f else 0,
                "career_fit": round(f.career_fit, 2) if f else 0,
                "seniority": round(f.seniority, 2) if f else 0,
                "behavioral": round(f.behavioral, 2) if f else 0,
                "trust": round(f.trust, 2) if f else 0,
                "logistics": round(f.logistics, 2) if f else 0,
            } if f else {},
            "consistency_clean": not bool(c.risk_flags),
            "flags": [fl.detail for fl in (c.risk_flags or [])],
        })

    payload = {
        "jd": jd,
        "category": category,
        "engine": res.engine,
        "total": len(records),
        "elapsed": elapsed,
        "top": top,
        "from_cache": False,
        "pool_fingerprint": pool_fp,
        "honeypots_in_top": sum(1 for t in top if not t["consistency_clean"]),
    }
    with _lock:
        _cache[key] = payload
    return dict(payload)


def warm(embedder=None, engine: str = "spine", top_n: int = 10) -> dict[str, Any]:
    """Precompute the standing challenge ranking at boot so the first customer
    request is instant. Uses the SPINE engine by default — it ranks the 100K in
    ~30s deterministically and, crucially, does NOT hold the embedder model, so
    the interactive paste-a-JD product loop keeps the hybrid engine available while
    the 100K warms. Must match the engine/top_n the challenge route requests so the
    cache key actually hits."""
    return rank_live(CHALLENGE_JD, engine=engine, top_n=top_n, embedder=embedder, force=True)


def invalidate() -> None:
    with _lock:
        _cache.clear()

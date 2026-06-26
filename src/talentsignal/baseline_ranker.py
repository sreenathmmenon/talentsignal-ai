"""A credible keyword-only baseline ranker — the foil that proves our value.

The brief's opening claim: "recruiters miss the right person because keyword
filters can't see what matters." To PROVE we fix that, we need an honest keyword
baseline to compare against — not a substring strawman, but a real ATS-style
ranker: whole-token overlap between the JD's requirement keywords and the
candidate's text, weighted by requirement importance, normalized. Then we can show
exactly which strong candidates this keyword ranker buries that our engine rescues.

This is READ-ONLY and never touches the production ranking. It exists only to
generate the head-to-head rescue ledger.
"""
from __future__ import annotations

import re
from typing import Any, Iterable

from .jd_parser import JobSpec
from . import artifacts

_TOKEN = re.compile(r"[a-z0-9+#./]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN.findall((text or "").lower()))


def _req_keywords(job: JobSpec) -> list[tuple[str, float]]:
    """(keyword, weight) for every salient word in the JD's must/nice requirements.
    Must-have words weigh more than nice-to-have — a real ATS prioritizes them."""
    out: list[tuple[str, float]] = []
    for kw in job.must_have:
        for w in re.split(r"[\s/\-,]+", kw.lower()):
            if len(w) >= 3:
                out.append((w, 1.0))
    for kw in job.nice_to_have:
        for w in re.split(r"[\s/\-,]+", kw.lower()):
            if len(w) >= 3:
                out.append((w, 0.4))
    return out


def keyword_score(candidate: dict[str, Any], req_kw: list[tuple[str, float]]) -> float:
    """Normalized keyword-overlap score in [0,1] — the keyword filter's view."""
    if not req_kw:
        return 0.0
    toks = _tokens(artifacts.evidence_text_of(candidate))
    hit = sum(w for kw, w in req_kw if kw in toks)
    total = sum(w for _, w in req_kw)
    return hit / total if total else 0.0


def keyword_rank(candidates: Iterable[dict[str, Any]], job: JobSpec) -> dict[str, int]:
    """Rank ALL candidates by the keyword baseline; return {candidate_id: rank}."""
    req_kw = _req_keywords(job)
    scored = [(c["candidate_id"], keyword_score(c, req_kw)) for c in candidates]
    # deterministic: by score desc, then id, exactly like the real engine's tiebreak
    scored.sort(key=lambda x: (-x[1], x[0]))
    return {cid: i for i, (cid, _) in enumerate(scored, 1)}

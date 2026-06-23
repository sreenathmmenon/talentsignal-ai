"""Canonical candidate model — the normalized shape every adapter produces.

This is a superset of the challenge schema plus the fields a universal product
needs. Adapters map their raw input into `canonical_record()`, which fills sane
defaults so a sparse resume and a rich JSON profile both come out rankable.

The engine consumes plain dicts (it already does), so the canonical record IS a
dict in the challenge shape, with extra optional keys tolerated. normalize_record
repairs/derives common fields (years from career, missing signal block, etc.).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

COMPANY_SIZES = {"1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10001+"}


@dataclass
class Candidate:
    """Lightweight typed view used by adapters while building a record."""
    name: str = ""
    headline: str = ""
    summary: str = ""
    location: str = ""
    country: str = ""
    years_of_experience: float = 0.0
    current_title: str = ""
    current_company: str = ""
    current_industry: str = ""
    career: list[dict[str, Any]] = field(default_factory=list)
    education: list[dict[str, Any]] = field(default_factory=list)
    skills: list[dict[str, Any]] = field(default_factory=list)
    signals: dict[str, Any] = field(default_factory=dict)
    source: str = ""          # which adapter produced this
    confidence: float = 1.0   # parse confidence (lower for messy resumes)
    raw_text: str = ""        # original text, for audit/embedding fallback

    def to_record(self) -> dict[str, Any]:
        return canonical_record(self)


def _gen_id(seed: str) -> str:
    return "CAND_" + str(int(hashlib.sha256(seed.encode()).hexdigest(), 16) % 10_000_000).zfill(7)


def canonical_record(c: Candidate, candidate_id: str | None = None) -> dict[str, Any]:
    """Produce a challenge-shaped, engine-rankable dict from a Candidate."""
    cid = candidate_id or _gen_id(c.name + c.summary + c.current_company + (c.raw_text[:200]))
    rec = {
        "candidate_id": cid,
        "profile": {
            "anonymized_name": c.name or "Candidate",
            "headline": c.headline or c.current_title,
            "summary": c.summary,
            "location": c.location,
            "country": c.country,
            "years_of_experience": float(c.years_of_experience or 0.0),
            "current_title": c.current_title,
            "current_company": c.current_company,
            "current_company_size": _coerce_size(c),
            "current_industry": c.current_industry,
        },
        "career_history": c.career or [],
        "education": c.education or [],
        "skills": c.skills or [],
        "redrob_signals": c.signals or {},
        # product metadata (tolerated by the engine, used by surfaces)
        "_ingest": {"source": c.source, "confidence": round(c.confidence, 3)},
    }
    return normalize_record(rec)


def _coerce_size(c: Candidate) -> str:
    for job in c.career:
        s = str(job.get("company_size", ""))
        if s in COMPANY_SIZES:
            return s
    return "51-200"  # neutral default


def normalize_record(rec: dict[str, Any]) -> dict[str, Any]:
    """Repair/derive common fields so any partial record is rankable.

    - derive years_of_experience from career durations if missing/zero
    - ensure a signals block exists (neutral defaults) so behavioral scoring runs
    - coerce career durations / dates into the expected types
    """
    profile = rec.setdefault("profile", {})
    career = rec.setdefault("career_history", [])
    rec.setdefault("education", [])
    rec.setdefault("skills", [])
    signals = rec.setdefault("redrob_signals", {})

    # derive years from career if absent
    if not profile.get("years_of_experience"):
        months = sum(int(j.get("duration_months") or 0) for j in career)
        if months:
            profile["years_of_experience"] = round(months / 12.0, 1)

    # current title/company from the current/first career entry
    if not profile.get("current_title") and career:
        cur = next((j for j in career if j.get("is_current")), career[0])
        profile.setdefault("current_title", cur.get("title", ""))
        profile.setdefault("current_company", cur.get("company", ""))

    # ensure a behavioral signal block so schema-driven scoring has something.
    # neutral-but-present defaults (a real product would source these live).
    signals.setdefault("open_to_work_flag", True)
    signals.setdefault("profile_completeness_score", _completeness(rec))
    signals.setdefault("verified_email", False)

    # coerce skill/career numeric fields
    for s in rec["skills"]:
        if "duration_months" in s:
            s["duration_months"] = int(s.get("duration_months") or 0)
    for j in career:
        if "duration_months" in j:
            j["duration_months"] = int(j.get("duration_months") or 0)
    return rec


def _completeness(rec: dict[str, Any]) -> int:
    p = rec.get("profile", {})
    have = sum(bool(p.get(k)) for k in ("summary", "current_title", "location"))
    have += 1 if rec.get("career_history") else 0
    have += 1 if rec.get("skills") else 0
    return int(20 + 16 * have)  # 20..100


# --- shared text helpers used by resume parsers --------------------------------

def parse_duration_months(start: str, end: str | None) -> int:
    """Months between two YYYY[-MM] strings; end None -> 'present' (ref 2026-06)."""
    def ym(s: str) -> tuple[int, int] | None:
        m = re.match(r"(\d{4})(?:-(\d{1,2}))?", s or "")
        if not m:
            return None
        return int(m.group(1)), int(m.group(2) or 1)
    a = ym(start)
    b = ym(end) if end else (2026, 6)
    if not a:
        return 0
    if not b:
        b = (2026, 6)
    return max(0, (b[0] - a[0]) * 12 + (b[1] - a[1]))

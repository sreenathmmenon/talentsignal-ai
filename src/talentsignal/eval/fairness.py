"""Fairness / bias audit for the ranking engine.

A ranking system that decides who recruiters see must be auditable for bias. The
core property we want is *name/identity invariance*: changing only a candidate's
name (and any name-correlated identity field) must not change their score or
rank. Because the engine scores from evidence text (summary, career, skills) and
structured signals — never the name — this should hold exactly; this module
proves it empirically rather than asserting it.

Checks:
  name_invariance    — swap names across gendered/cultural name sets; scores must
                       be identical (the engine is name-blind by construction).
  location_sensitivity (informational) — location DOES legitimately affect the
                       logistics factor when a JD lists preferred locations; we
                       report its magnitude so it's transparent, not hidden.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

# Distinct name sets to swap in. The point is only that the NAME varies; the
# evidence is held identical, so any score change would reveal name leakage.
NAME_SETS = {
    "set_a": ["Aarav Sharma", "Priya Nair", "Mohammed Khan", "Lakshmi Iyer"],
    "set_b": ["John Smith", "Mary Johnson", "Wei Chen", "Olga Petrov"],
    "set_c": ["Fatima Ali", "Chen Li", "James Brown", "Ananya Reddy"],
}


@dataclass
class FairnessReport:
    name_invariant: bool
    max_score_delta: float
    n_tested: int
    location_factor_range: float
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name_invariant": self.name_invariant,
            "max_score_delta": self.max_score_delta,
            "n_tested": self.n_tested,
            "location_factor_range": self.location_factor_range,
            "details": self.details,
        }


def _score_one(record: dict[str, Any], job) -> float:
    from ..features import build_evidence
    from ..scoring import score_candidate
    return score_candidate(build_evidence(record), job).final_score


def audit_name_invariance(records: list[dict[str, Any]], job, *, limit: int = 40) -> FairnessReport:
    """For each candidate, re-score under every name set; the score must not move."""
    max_delta = 0.0
    tested = 0
    worst = None
    for rec in records[:limit]:
        base = _score_one(rec, job)
        for names in NAME_SETS.values():
            for nm in names[:1]:  # one swap per set is enough to detect leakage
                alt = copy.deepcopy(rec)
                prof = alt.setdefault("profile", {})
                prof["anonymized_name"] = nm
                # Inject the name into the fields the ENGINE actually reads, so the
                # test genuinely exercises name-leakage (the old version only set
                # anonymized_name, which build_evidence ignores — a vacuous test).
                prof["summary"] = f"{nm}. " + str(prof.get("summary", ""))
                prof["headline"] = f"{nm} — " + str(prof.get("headline", ""))
                d = abs(_score_one(alt, job) - base)
                if d > max_delta:
                    max_delta = d
                    worst = (rec.get("candidate_id"), nm, d)
                tested += 1
    return FairnessReport(
        name_invariant=max_delta < 1e-9,
        max_score_delta=round(max_delta, 9),
        n_tested=tested,
        location_factor_range=0.0,
        details={"worst_case": worst},
    )


def audit_location_transparency(records: list[dict[str, Any]], job, *, limit: int = 40) -> float:
    """Report how much the location/logistics factor varies across candidates.

    Location is a LEGITIMATE factor when a JD names preferred locations (a recruiter
    cares about it), so we don't suppress it — we surface its magnitude so it's a
    transparent, intentional weight rather than a hidden bias.
    """
    from ..features import build_evidence
    from ..scoring import _logistics_score
    vals = [_logistics_score(build_evidence(r), job) for r in records[:limit]]
    return round(max(vals) - min(vals), 4) if vals else 0.0


def run_fairness_audit(records: list[dict[str, Any]], job, *, limit: int = 40) -> FairnessReport:
    rep = audit_name_invariance(records, job, limit=limit)
    rep.location_factor_range = audit_location_transparency(records, job, limit=limit)
    return rep

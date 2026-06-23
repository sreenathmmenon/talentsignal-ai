"""Fairness audit: the engine is name/identity-blind — swapping a candidate's
name across gendered/cultural name sets must not change their score.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.eval.fairness import run_fairness_audit, audit_name_invariance, NAME_SETS
from talentsignal.jd_parser import load_job_spec
from talentsignal.eval import datasets as D
from talentsignal.eval.roles import AI_SEARCH

JOB = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")


def test_name_invariance_is_exact() -> None:
    recs = D.records_of(D.build_pool(AI_SEARCH, mix={D.STRONG: 10, D.ADJACENT: 10, D.IRRELEVANT: 10}))
    rep = audit_name_invariance(recs, JOB, limit=30)
    assert rep.name_invariant is True
    assert rep.max_score_delta == 0.0
    assert rep.n_tested > 0


def test_multiple_name_sets_used() -> None:
    assert len(NAME_SETS) >= 3
    # name sets are distinct (vary gender/culture)
    flat = [n for s in NAME_SETS.values() for n in s]
    assert len(set(flat)) == len(flat)


def test_full_report_serializes() -> None:
    recs = D.records_of(D.build_pool(AI_SEARCH, mix={D.STRONG: 5, D.IRRELEVANT: 5}))
    rep = run_fairness_audit(recs, JOB, limit=10)
    d = rep.to_dict()
    assert d["name_invariant"] is True
    assert "location_factor_range" in d

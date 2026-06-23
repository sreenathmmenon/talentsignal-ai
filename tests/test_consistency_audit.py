"""General consistency auditor: fires on internal contradictions (honeypots),
stays silent on clean profiles, and works for any role/schema.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.consistency_audit import audit_candidate
from talentsignal.eval import datasets as D
from talentsignal.eval.roles import AI_SEARCH, SALES


def _base_clean() -> dict:
    return {
        "candidate_id": "CAND_0000001",
        "profile": {"years_of_experience": 6.0, "summary": "built ranking systems with python and faiss",
                    "headline": "ML Engineer", "current_title": "ML Engineer"},
        "career_history": [
            {"title": "ML Engineer", "description": "built ranking with python and faiss",
             "duration_months": 36, "start_date": "2021-01-01", "end_date": None},
            {"title": "SDE", "description": "backend python services",
             "duration_months": 36, "start_date": "2018-01-01", "end_date": "2020-12-01"},
        ],
        "skills": [{"name": "Python", "proficiency": "expert", "duration_months": 60},
                   {"name": "FAISS", "proficiency": "advanced", "duration_months": 24}],
        "redrob_signals": {"endorsements_received": 30, "skill_assessment_scores": {"python": 80}},
    }


def test_clean_profile_no_flags() -> None:
    assert audit_candidate(_base_clean()).flags == []


def test_tenure_exceeds_experience() -> None:
    c = _base_clean()
    c["profile"]["years_of_experience"] = 3.0  # but career sums to 72 months
    codes = audit_candidate(c).codes
    assert "tenure_exceeds_experience" in codes


def test_expert_zero_duration() -> None:
    c = _base_clean()
    c["skills"] = [{"name": "Python", "proficiency": "expert", "duration_months": 0},
                   {"name": "FAISS", "proficiency": "expert", "duration_months": 0}]
    rep = audit_candidate(c)
    assert "expert_zero_duration" in rep.codes
    assert rep.is_impossible


def test_skill_exceeds_experience_far() -> None:
    c = _base_clean()
    c["profile"]["years_of_experience"] = 3.0
    c["career_history"] = [{"title": "x", "description": "y", "duration_months": 30,
                            "start_date": "2023-01-01", "end_date": None}]
    c["skills"] = [{"name": "Python", "proficiency": "advanced", "duration_months": 120}]  # 10y skill, 3y exp
    assert "skill_exceeds_career" in audit_candidate(c).codes


def test_date_integrity_end_before_start() -> None:
    c = _base_clean()
    c["career_history"][0]["start_date"] = "2022-01-01"
    c["career_history"][0]["end_date"] = "2020-01-01"
    assert "date_integrity" in audit_candidate(c).codes


def test_synthetic_honeypots_all_flagged_clean_silent() -> None:
    pool = D.build_pool(AI_SEARCH, mix={D.STRONG: 8, D.PARAPHRASE_IDEAL: 6,
                                        D.ADJACENT: 8, D.HONEYPOT: 10, D.IRRELEVANT: 8})
    for c in pool:
        flagged = bool(audit_candidate(c.record).flags)
        if c.archetype == D.HONEYPOT:
            assert flagged, c.candidate_id
        elif c.archetype in (D.STRONG, D.PARAPHRASE_IDEAL, D.ADJACENT, D.IRRELEVANT):
            assert not flagged, (c.archetype, c.candidate_id, audit_candidate(c.record).codes)


def test_role_independent() -> None:
    # same checks work for a non-AI role
    pool = D.build_pool(SALES, mix={D.STRONG: 5, D.HONEYPOT: 5})
    honey = [c for c in pool if c.archetype == D.HONEYPOT]
    assert all(audit_candidate(c.record).flags for c in honey)

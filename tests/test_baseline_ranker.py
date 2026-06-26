"""Keyword baseline ranker — the honest foil for the rescue ledger. It must be a
real whole-token overlap ranker (not substring) and must NEVER touch production
ranking (read-only)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.baseline_ranker import keyword_score, keyword_rank, _req_keywords
from talentsignal.jd_parser import job_spec_from_jd_text


JD = "AI Engineer. Must have embeddings, retrieval, ranking, python. 5-9 years."


def _cand(cid, text):
    return {"candidate_id": cid, "profile": {"summary": text, "headline": "",
            "current_title": "Engineer", "years_of_experience": 6},
            "career_history": [{"title": "Engineer", "description": text, "duration_months": 72}],
            "skills": [], "redrob_signals": {}}


def test_keyword_score_whole_token():
    job = job_spec_from_jd_text(JD, category="ai_ml_search_ranking")
    rk = _req_keywords(job)
    strong = keyword_score(_cand("A", "built embeddings retrieval ranking in python"), rk)
    weak = keyword_score(_cand("B", "managed a marketing team and brand campaigns"), rk)
    assert strong > weak
    # substring must NOT count: 'ml' inside 'html' shouldn't score the 'ml' family
    assert keyword_score(_cand("C", "i wrote html and xml"), rk) == 0.0


def test_keyword_rank_is_deterministic_and_total():
    job = job_spec_from_jd_text(JD, category="ai_ml_search_ranking")
    cands = [_cand("A", "embeddings retrieval ranking python"),
             _cand("B", "python"), _cand("C", "marketing")]
    r1 = keyword_rank(cands, job)
    r2 = keyword_rank(cands, job)
    assert r1 == r2  # deterministic
    assert r1["A"] == 1 and set(r1.values()) == {1, 2, 3}  # full ranking

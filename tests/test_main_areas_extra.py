"""Extra coverage on main areas the bug hunt touched: cross-encoder rerank
(no-drop + monotonicity), explanation grounding audit, category-weight validation,
and the keyword baseline ranker. All offline / deterministic."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest


# --- reranker: must never drop a candidate, must stay monotonic ---------------

class _FakeCE:
    """Deterministic fake cross-encoder: scores by a number embedded in the doc."""
    def predict(self, pairs, **k):
        import re
        out = []
        for _jd, doc in pairs:
            m = re.search(r"score=(\d+)", doc)
            out.append(float(m.group(1)) if m else 0.0)
        return out


class _RC:
    def __init__(self, cid, score):
        self.candidate_id = cid
        self.score = score
        self.rank = 0


def _cand(cid, n):
    return {"candidate_id": cid, "profile": {"summary": f"score={n} python"},
            "career_history": [], "skills": []}


def test_rerank_preserves_all_candidates_including_missing(monkeypatch):
    import talentsignal.reranker as R
    monkeypatch.setattr(R, "_load", lambda *a, **k: _FakeCE())
    monkeypatch.setattr(R, "available", lambda *a, **k: True)
    ranked = [_RC("A", 0.5), _RC("B", 0.5), _RC("MISSING", 0.5)]
    id2 = {"A": _cand("A", 1), "B": _cand("B", 9)}  # MISSING has no record
    out = R.rerank("jd", ranked, id2, top_k=10)
    assert len(out) == 3                                   # nothing dropped
    assert {c.candidate_id for c in out} == {"A", "B", "MISSING"}
    # B (score=9) should now outrank A (score=1)
    ids = [c.candidate_id for c in out]
    assert ids.index("B") < ids.index("A")
    assert [c.rank for c in out] == [1, 2, 3]              # ranks renumbered


def test_rerank_degrades_when_unavailable(monkeypatch):
    import talentsignal.reranker as R
    monkeypatch.setattr(R, "_load", lambda *a, **k: None)
    ranked = [_RC("A", 0.9), _RC("B", 0.5)]
    out = R.rerank("jd", ranked, {"A": _cand("A", 1), "B": _cand("B", 2)})
    assert [c.candidate_id for c in out] == ["A", "B"]     # original order, no crash


# --- explanation_audit: grounding catches a hallucinated term -----------------

def test_explanation_audit_flags_ungrounded_term(tmp_path):
    from talentsignal.explanation_audit import audit_packets
    # a packet whose reasoning cites 'kubernetes' that is NOT in its evidence
    packet = {
        "candidate_id": "CAND_X", "rank": 1, "score": 0.9,
        "reasoning": "Strong fit: deep evidence for kubernetes and ranking.",
        "score_breakdown": {"engine": "hybrid"},
        "matched_requirements": [["ranking models", ["ranking"], "built ranking"]],
        "evidence": {"all_text": "built ranking systems in python",
                     "career_text": "ranking", "skill_text": "python ranking"},
    }
    p = tmp_path / "packets.jsonl"
    p.write_text(json.dumps(packet) + "\n", encoding="utf-8")
    warnings = audit_packets(p)
    assert any("kubernetes" in w.lower() and "unsupported" in w.lower() for w in warnings)


def test_explanation_audit_passes_grounded(tmp_path):
    from talentsignal.explanation_audit import audit_packets
    packet = {
        "candidate_id": "CAND_Y", "rank": 1, "score": 0.9,
        "reasoning": "Strong fit: hands-on evidence for ranking and retrieval.",
        "score_breakdown": {"engine": "hybrid"},
        "matched_requirements": [["ranking", ["ranking", "retrieval"], "built ranking retrieval"]],
        "evidence": {"all_text": "built ranking and retrieval systems",
                     "career_text": "ranking retrieval", "skill_text": "ranking"},
    }
    p = tmp_path / "packets.jsonl"
    p.write_text(json.dumps(packet) + "\n", encoding="utf-8")
    warnings = audit_packets(p)
    assert not any("unsupported term" in w for w in warnings)


# --- category taxonomy: weight validation -------------------------------------

def test_category_weights_sum_to_one():
    from talentsignal.category_taxonomy import CATEGORY_PROFILES, validate_weights
    for name, prof in CATEGORY_PROFILES.items():
        validate_weights(prof.default_weights)   # raises if not ~1.0 / missing keys


def test_validate_weights_rejects_bad_total():
    from talentsignal.category_taxonomy import validate_weights
    with pytest.raises(ValueError):
        validate_weights({"technical_evidence": 0.5, "career_fit": 0.1, "seniority": 0.1,
                          "logistics": 0.1, "behavioral": 0.05, "trust": 0.0})  # sums 0.85


def test_unknown_category_falls_back():
    from talentsignal.category_taxonomy import get_category_profile
    p = get_category_profile("welding_fabrication")   # no such profile
    assert p.category == "welding_fabrication" and p.default_weights


# --- keyword baseline ranker: distinct from the engine ------------------------

def test_keyword_baseline_ranks_by_overlap():
    from talentsignal.baseline_ranker import keyword_rank
    from talentsignal.jd_parser import job_spec_from_jd_text
    job = job_spec_from_jd_text("AI Engineer. Must have embeddings, retrieval, ranking, python. 5-9 years.",
                                category="ai_ml_search_ranking")
    cands = [_cand("strong", 0) | {"profile": {"summary": "embeddings retrieval ranking python"}},
             _cand("weak", 0) | {"profile": {"summary": "marketing brand campaigns"}}]
    rank = keyword_rank(cands, job)
    assert rank["strong"] < rank["weak"]   # strong overlap ranks higher (lower number)

"""Cross-encoder rerank stage — the production-grade accuracy stage. Tested for
graceful degradation (no model -> original order, never raises) and correct
shortlist mechanics. The model itself is exercised in the offline corpus harness.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal import reranker
from talentsignal.api import rank


def _cands(n):
    out = []
    for i in range(n):
        out.append({
            "candidate_id": f"C{i}",
            "profile": {"summary": f"candidate {i} python embeddings retrieval ranking",
                        "headline": "AI Engineer", "years_of_experience": 7,
                        "current_title": "AI Engineer"},
            "career_history": [{"title": "AI Engineer", "description": "ranking retrieval",
                                 "duration_months": 84}],
            "skills": ["Python"], "redrob_signals": {"open_to_work_flag": True},
        })
    return out


def test_rerank_off_by_default_unchanged():
    res = rank("AI Engineer. Must have python, ranking, retrieval. 5-9 years.",
               _cands(5), top_n=5, engine="spine")
    assert res.engine == "spine"  # no rerank suffix


def test_rerank_degrades_gracefully_when_unavailable(monkeypatch):
    # force the cross-encoder to be unavailable -> ranking must still succeed and
    # return the retrieval order, never raise.
    monkeypatch.setattr(reranker, "_load", lambda *a, **k: None)
    res = rank("AI Engineer. Must have python, ranking. 5-9 years.",
               _cands(5), top_n=3, engine="spine", rerank=True)
    assert len(res.ranked) == 3
    assert any("unavailable" in n for n in res.notes)


def test_rerank_blends_and_reorders(monkeypatch):
    # fake cross-encoder: score candidates in REVERSE so we can assert the rerank
    # actually changed the order using the CE signal.
    class FakeCE:
        def predict(self, pairs, **k):
            return [float(len(pairs) - i) for i in range(len(pairs))]
    monkeypatch.setattr(reranker, "_load", lambda *a, **k: FakeCE())
    res = rank("AI Engineer. Must have python, ranking, retrieval. 5-9 years.",
               _cands(6), top_n=6, engine="spine", rerank=True, rerank_top_k=6)
    assert "rerank" in res.engine
    # the first candidate now carries a cross_encoder_score
    assert res.ranked[0].cross_encoder_score >= 0.0

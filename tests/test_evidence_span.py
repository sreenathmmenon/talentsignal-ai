"""Per-candidate explainability: each matched requirement carries the candidate's
OWN sentence that proves it (a real quote, never fabricated) — the drill-down a
recruiter/enterprise needs to trust and defend a ranking decision.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.semantic_match import best_evidence_span


def test_picks_sentence_with_most_matched_keywords():
    text = ("I write backend services. "
            "I built embeddings retrieval and ranking models with NDCG evaluation. "
            "I like coffee.")
    span = best_evidence_span(("ranking", "ndcg", "embeddings"), text)
    assert "ranking" in span.lower() and "ndcg" in span.lower()
    assert "coffee" not in span.lower()


def test_returns_empty_when_no_match():
    span = best_evidence_span(("ranking",), "I only did frontend React work.")
    assert span == ""


def test_span_is_a_real_substring_no_fabrication():
    text = "Owned the candidate-matching ranker and ran A/B evaluation in production."
    span = best_evidence_span(("ranker", "evaluation"), text)
    assert span.rstrip("…") in text  # never invents text


def test_long_span_is_truncated():
    sent = "Built " + "ranking " * 60 + "systems."
    span = best_evidence_span(("ranking",), sent, max_len=80)
    assert len(span) <= 80


def test_flows_through_match_result():
    from dataclasses import dataclass
    import numpy as np
    from talentsignal import semantic_match as sm

    @dataclass
    class Req:
        text: str
        kind: str
        weight: float
        keywords: tuple

    reqs = [Req("ranking systems", "must_have", 1.0, ("ranking",))]
    req_emb = np.array([[1.0, 0.0]], dtype="float32")
    ev_emb = np.array([1.0, 0.0], dtype="float32")
    text = "I built ranking systems for search at scale."
    res = sm.match(reqs, req_emb, text, ev_emb, alpha=0.6)
    rm = res.requirement_matches[0]
    assert rm.evidence_span and "ranking" in rm.evidence_span.lower()
    assert rm.evidence_span.rstrip("…") in text

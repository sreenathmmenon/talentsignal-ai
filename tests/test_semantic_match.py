"""Hybrid semantic matching: lexical whole-token overlap, dense cosine rescaling,
graceful lexical-only fallback, and correct must/nice/disqualifier aggregation.

Uses synthetic vectors so the test needs no embedding model (CI-safe, fast).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from talentsignal import semantic_match as sm


@dataclass
class Req:
    text: str
    kind: str
    weight: float
    keywords: tuple


def test_lexical_overlap_whole_token_only() -> None:
    # 'ml' must NOT match inside 'html' (the bug we are eliminating)
    tokens = {"html", "streamline", "python"}
    score, matched = sm.lexical_overlap(("ml", "python"), tokens)
    assert "ml" not in matched
    assert "python" in matched
    assert score == 0.5


def test_cosine_rescaling_monotonic_and_clamped() -> None:
    a = np.array([1.0, 0.0, 0.0], dtype="float32")
    # identical -> cosine 1.0 -> above ceil -> 1.0
    assert sm.cosine(a, a) == 1.0
    # orthogonal -> cosine 0 -> below floor -> 0.0
    b = np.array([0.0, 1.0, 0.0], dtype="float32")
    assert sm.cosine(a, b) == 0.0


def test_match_lexical_only_fallback() -> None:
    reqs = [Req("build ranking systems", "must_have", 1.0, ("ranking", "systems"))]
    res = sm.match(reqs, None, "i build ranking systems in production", None)
    assert res.semantic_fit > 0  # works without embeddings
    assert res.requirement_matches[0].lexical == 1.0


def test_match_hybrid_combines_channels() -> None:
    reqs = [Req("ranking", "must_have", 1.0, ("ranking",))]
    req_emb = np.array([[1.0, 0.0]], dtype="float32")
    ev_emb = np.array([1.0, 0.0], dtype="float32")  # perfect dense match
    res = sm.match(reqs, req_emb, "totally different words", ev_emb, alpha=0.6)
    rm = res.requirement_matches[0]
    assert rm.dense == 1.0          # semantic match despite zero keyword overlap
    assert rm.lexical == 0.0
    assert abs(rm.score - 0.6) < 1e-6  # alpha*dense + (1-alpha)*lexical


def test_disqualifier_and_coverage_aggregation() -> None:
    reqs = [
        Req("ranking", "must_have", 1.0, ("ranking",)),
        Req("evaluation", "must_have", 1.0, ("evaluation",)),
        Req("computer vision only", "disqualifier", 1.0, ("vision",)),
    ]
    res = sm.match(reqs, None, "ranking and evaluation work, plus vision systems", None)
    assert res.coverage > 0  # must-haves matched
    assert res.disqualifier_hit > 0  # disqualifier keyword present

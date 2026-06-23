"""Validate ranking metrics against hand-computed ground truth.

Every expected value here is derived by hand (shown in comments) so the metric
implementation is pinned to known-correct arithmetic, not to itself.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.eval import metrics


def approx(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def test_dcg_simple() -> None:
    # rels = [3, 2, 0]; DCG = 3/log2(2) + 2/log2(3) + 0/log2(4)
    #      = 3/1 + 2/1.5849625... + 0 = 3 + 1.261859507... = 4.261859507...
    expected = 3.0 + 2.0 / math.log2(3)
    assert approx(metrics.dcg([3, 2, 0]), expected)


def test_ndcg_perfect_ranking_is_one() -> None:
    # Already in ideal order -> NDCG@k == 1.0
    assert approx(metrics.ndcg_at_k([5, 4, 3, 1, 0], 5), 1.0)


def test_ndcg_known_value() -> None:
    # ranked rels = [0, 3]; ideal = [3, 0]
    # DCG = 0/log2(2) + 3/log2(3) = 3/1.5849625 = 1.892789...
    # IDCG = 3/log2(2) + 0 = 3
    # NDCG@2 = 1.892789.../3 = 0.630929...
    dcg = 3.0 / math.log2(3)
    expected = dcg / 3.0
    assert approx(metrics.ndcg_at_k([0, 3], 2), expected)


def test_ndcg_zero_when_no_relevance() -> None:
    assert metrics.ndcg_at_k([0, 0, 0], 10) == 0.0


def test_average_precision_known_value() -> None:
    # threshold=3. ranked grades = [3, 0, 3, 0]
    # relevant at positions 1 and 3 (1-based): precision = 1/1 and 2/3
    # AP = (1.0 + 0.6666...) / 2 = 0.83333...
    expected = (1.0 + 2.0 / 3.0) / 2.0
    assert approx(metrics.average_precision([3, 0, 3, 0]), expected)


def test_average_precision_no_relevant() -> None:
    assert metrics.average_precision([0, 1, 2]) == 0.0  # nothing >= 3


def test_precision_at_k() -> None:
    # top-5 grades = [5, 0, 3, 2, 4]; relevant (>=3) = 5,3,4 -> 3 of 5 = 0.6
    assert approx(metrics.precision_at_k([5, 0, 3, 2, 4], 5), 0.6)


def test_honeypot_rate() -> None:
    # top-10 grades; two honeypots (grade 0) -> 2/10 = 0.2
    rels = [5, 0, 4, 3, 0, 5, 4, 3, 1, 2]
    assert approx(metrics.honeypot_rate_at_k(rels, 10), 0.2)


def test_composite_matches_weighted_sum() -> None:
    rels = [5, 4, 3, 0, 1] + [0] * 50
    expected = (
        0.50 * metrics.ndcg_at_k(rels, 10)
        + 0.30 * metrics.ndcg_at_k(rels, 50)
        + 0.15 * metrics.average_precision(rels)
        + 0.05 * metrics.precision_at_k(rels, 10)
    )
    assert approx(metrics.composite_score(rels), expected)


def test_relevances_from_ranking_maps_and_defaults() -> None:
    labels = {"A": 5, "B": 3}
    ranked = ["B", "X", "A"]  # X not labeled -> default 0
    assert metrics.relevances_from_ranking(ranked, labels) == [3.0, 0.0, 5.0]


def test_evaluate_bundle_keys() -> None:
    out = metrics.evaluate([5, 4, 3, 0, 1])
    for key in ["ndcg@10", "ndcg@50", "map", "p@5", "p@10", "honeypot_rate@10", "composite"]:
        assert key in out

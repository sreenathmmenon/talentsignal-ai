"""Ranking-quality metrics for evaluating a ranked candidate list against
graded relevance labels.

Pure standard library (math only) so the eval suite carries no heavy runtime
dependency and can run anywhere, including inside the constrained reproduction
sandbox. All functions operate on a *ranked* list of relevance grades, i.e.
``relevances[i]`` is the ground-truth grade (0..5) of the candidate the ranker
placed at position ``i`` (position 0 = rank 1).

The composite mirrors the challenge scoring exactly:

    composite = 0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP + 0.05*P@10

Relevance grading convention used throughout the suite:
    tier 0  -> irrelevant / honeypot (NOT relevant)
    tier 1  -> weak / adjacent-only
    tier 3+ -> "relevant" for precision purposes (matches the challenge's
               "tier 3+" definition of relevant in P@10)
"""
from __future__ import annotations

import math
from typing import Sequence

# A candidate counts as "relevant" (for precision-style metrics) at this grade
# or above. The challenge defines P@10 relevance as tier 3+.
RELEVANT_THRESHOLD = 3


def dcg(relevances: Sequence[float], k: int | None = None) -> float:
    """Discounted Cumulative Gain over the first ``k`` ranked items.

    Uses the standard ``rel_i / log2(i+1)`` discount (i is 1-based rank).
    """
    if k is None:
        k = len(relevances)
    total = 0.0
    for i, rel in enumerate(relevances[:k]):
        total += float(rel) / math.log2(i + 2)  # i=0 -> log2(2)=1
    return total


def ndcg_at_k(relevances: Sequence[float], k: int) -> float:
    """Normalized DCG@k. Returns 0.0 when the ideal DCG is 0 (no relevance)."""
    actual = dcg(relevances, k)
    ideal = dcg(sorted(relevances, reverse=True), k)
    if ideal == 0.0:
        return 0.0
    return actual / ideal


def average_precision(relevances: Sequence[float], threshold: int = RELEVANT_THRESHOLD) -> float:
    """Average Precision treating grade >= threshold as relevant.

    AP = mean over relevant positions of precision@that_position. Returns 0.0
    when there are no relevant items in the list.
    """
    hits = 0
    precision_sum = 0.0
    for i, rel in enumerate(relevances):
        if rel >= threshold:
            hits += 1
            precision_sum += hits / (i + 1)
    if hits == 0:
        return 0.0
    return precision_sum / hits


def precision_at_k(relevances: Sequence[float], k: int, threshold: int = RELEVANT_THRESHOLD) -> float:
    """Fraction of the top-k that are relevant (grade >= threshold)."""
    if k <= 0:
        return 0.0
    window = relevances[:k]
    relevant = sum(1 for rel in window if rel >= threshold)
    return relevant / k


def honeypot_rate_at_k(relevances: Sequence[float], k: int, honeypot_grade: int = 0) -> float:
    """Fraction of the top-k that are honeypots (grade == honeypot_grade).

    The challenge forces honeypots to tier 0 and disqualifies submissions with
    honeypot rate > 10% in top 100, so this is a first-class metric, not an
    afterthought.
    """
    if k <= 0:
        return 0.0
    window = relevances[:k]
    return sum(1 for rel in window if rel == honeypot_grade) / len(window) if window else 0.0


def composite_score(relevances: Sequence[float]) -> float:
    """The challenge composite: 0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP + 0.05*P@10."""
    return (
        0.50 * ndcg_at_k(relevances, 10)
        + 0.30 * ndcg_at_k(relevances, 50)
        + 0.15 * average_precision(relevances)
        + 0.05 * precision_at_k(relevances, 10)
    )


def evaluate(relevances: Sequence[float]) -> dict[str, float]:
    """Full metric bundle for a single ranked relevance list."""
    rels = [float(r) for r in relevances]
    return {
        "ndcg@10": ndcg_at_k(rels, 10),
        "ndcg@50": ndcg_at_k(rels, 50),
        "map": average_precision(rels),
        "p@5": precision_at_k(rels, 5),
        "p@10": precision_at_k(rels, 10),
        "honeypot_rate@10": honeypot_rate_at_k(rels, 10),
        "honeypot_rate@100": honeypot_rate_at_k(rels, 100),
        "composite": composite_score(rels),
    }


def relevances_from_ranking(
    ranked_ids: Sequence[str], labels: dict[str, float], default: float = 0.0
) -> list[float]:
    """Map a ranked list of candidate_ids to their ground-truth grades.

    ``labels`` is candidate_id -> grade. IDs not present in ``labels`` get
    ``default`` (treated as irrelevant). This is the bridge between a ranker's
    output and the metric functions above.
    """
    return [float(labels.get(cid, default)) for cid in ranked_ids]

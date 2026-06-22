from __future__ import annotations

from typing import Any


FACTOR_LABELS = {
    "technical_evidence": "Technical evidence",
    "career_fit": "Career fit",
    "seniority": "Seniority",
    "logistics": "Logistics",
    "behavioral": "Behavioral availability",
    "trust": "Trust",
    "confidence": "Evidence confidence",
}


def _factor_values(packet: dict[str, Any]) -> dict[str, float]:
    score = packet["score_breakdown"]
    return {key: float(score.get(key, 0.0)) for key in FACTOR_LABELS}


def strongest_factor(packet: dict[str, Any]) -> tuple[str, float]:
    factors = _factor_values(packet)
    key = max(factors, key=factors.get)
    return key, factors[key]


def weakest_factor(packet: dict[str, Any]) -> tuple[str, float]:
    factors = _factor_values(packet)
    key = min(factors, key=factors.get)
    return key, factors[key]


def compare_packets(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_score = float(left["score"])
    right_score = float(right["score"])
    left_factors = _factor_values(left)
    right_factors = _factor_values(right)
    deltas = [
        {
            "factor": key,
            "label": FACTOR_LABELS[key],
            "left": round(left_factors[key], 6),
            "right": round(right_factors[key], 6),
            "delta": round(left_factors[key] - right_factors[key], 6),
        }
        for key in FACTOR_LABELS
    ]
    deltas.sort(key=lambda row: abs(row["delta"]), reverse=True)
    left_strong = strongest_factor(left)
    right_strong = strongest_factor(right)
    winner = left if left_score >= right_score else right
    loser = right if winner is left else left
    return {
        "left_candidate_id": left["candidate_id"],
        "right_candidate_id": right["candidate_id"],
        "left_rank": left["rank"],
        "right_rank": right["rank"],
        "left_score": left["score"],
        "right_score": right["score"],
        "score_delta": round(left_score - right_score, 6),
        "factor_deltas": deltas,
        "left_strongest_factor": {"factor": left_strong[0], "label": FACTOR_LABELS[left_strong[0]], "value": round(left_strong[1], 6)},
        "right_strongest_factor": {"factor": right_strong[0], "label": FACTOR_LABELS[right_strong[0]], "value": round(right_strong[1], 6)},
        "recommendation": (
            f"Keep {winner['candidate_id']} ahead of {loser['candidate_id']} because the combined scorecard gives it "
            f"the stronger evidence-backed decision score ({winner['score']} vs {loser['score']})."
        ),
    }


def compare_by_rank(packets: list[dict[str, Any]], left_rank: int, right_rank: int) -> dict[str, Any] | None:
    by_rank = {int(packet["rank"]): packet for packet in packets}
    if left_rank not in by_rank or right_rank not in by_rank:
        return None
    return compare_packets(by_rank[left_rank], by_rank[right_rank])


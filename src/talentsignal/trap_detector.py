from __future__ import annotations

from typing import Any


TRAP_FLAG_LABELS = {
    "non_tech_ai_keyword_stuffing": "non-technical profile with AI keyword stuffing",
    "ai_terms_without_career_evidence": "AI terms without career evidence",
    "expert_skills_zero_duration": "expert skills with zero duration",
    "service_only_without_product_search_evidence": "service-only background without product/search proof",
    "stale_low_response": "stale and low response profile",
    "shallow_ai_tool_interest": "shallow AI tool interest without applied evidence",
}


def rejected_trap_examples(packets: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    flagged = [
        packet
        for packet in packets
        if packet["score_breakdown"].get("risk_flags") or not packet["score_breakdown"].get("top10_eligible", False)
    ]
    flagged.sort(
        key=lambda packet: (
            int(packet["rank"]) <= 10,
            len(packet["score_breakdown"].get("risk_flags", [])),
            float(packet["score_breakdown"].get("penalty", 0.0)),
        ),
        reverse=True,
    )
    examples: list[dict[str, Any]] = []
    for packet in flagged[:limit]:
        flags = packet["score_breakdown"].get("risk_flags", [])
        examples.append(
            {
                "candidate_id": packet["candidate_id"],
                "rank": packet["rank"],
                "score": packet["score"],
                "title": packet["evidence"]["title"],
                "reason": "; ".join(TRAP_FLAG_LABELS.get(flag, flag) for flag in flags) or "not eligible for top-10 confidence gate",
                "risk_flags": flags,
                "penalty": packet["score_breakdown"].get("penalty", 0.0),
                "evidence_terms": (
                    packet["evidence"].get("career_retrieval_terms", [])
                    + packet["evidence"].get("skill_ml_terms", [])
                    + packet["evidence"].get("vector_terms", [])
                )[:6],
            }
        )
    return examples


def rejected_trap_examples_from_scored(scored: list[tuple[Any, Any, dict[str, Any]]], limit: int = 5) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for rank, (score, ev, _candidate) in enumerate(scored, start=1):
        lexical_strength = len(ev.retrieval_terms) + len(ev.vector_terms) + len(ev.ml_terms)
        if not score.risk_flags or lexical_strength < 3:
            continue
        examples.append(
            {
                "candidate_id": ev.candidate_id,
                "rank": rank,
                "score": f"{score.final_score:.6f}",
                "title": ev.title,
                "reason": "; ".join(TRAP_FLAG_LABELS.get(flag, flag) for flag in score.risk_flags),
                "risk_flags": score.risk_flags,
                "penalty": score.penalty,
                "evidence_terms": (ev.retrieval_terms + ev.vector_terms + ev.ml_terms)[:6],
            }
        )
    examples.sort(key=lambda item: (item["rank"] <= 100, item["penalty"], -item["rank"]), reverse=True)
    return examples[:limit]

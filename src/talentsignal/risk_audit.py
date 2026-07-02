from __future__ import annotations

from .features import CandidateEvidence


def risk_flags(ev: CandidateEvidence) -> list[str]:
    flags: list[str] = []
    has_career_search_ai = bool(ev.career_retrieval_terms)
    if ev.non_tech_title and len(ev.ml_terms) >= 4 and not has_career_search_ai:
        flags.append("non_tech_ai_keyword_stuffing")
    if len(ev.ml_terms) >= 6 and not has_career_search_ai:
        flags.append("ai_terms_without_career_evidence")
    if ev.expert_zero_duration >= 2:
        flags.append("expert_skills_zero_duration")
    if ev.service_only and ev.product_company_count == 0 and not ev.career_retrieval_terms:
        flags.append("service_only_without_product_search_evidence")
    # Only flag stale/unresponsive when we actually HAVE activity data. A pasted /
    # uploaded résumé has no platform signals (last_active defaults to the 999
    # sentinel, response_rate to 0) — flagging it as "stale" would be a false
    # positive (unknown != inactive), and it wrongly drags the verdict to "Needs review".
    if 6 <= ev.last_active_months < 999 and ev.response_rate < 0.2:
        flags.append("stale_low_response")
    if ev.shallow_ai_terms and not has_career_search_ai:
        flags.append("shallow_ai_tool_interest")
    return flags


def risk_penalty(flags: list[str]) -> float:
    weights = {
        "non_tech_ai_keyword_stuffing": 0.22,
        "ai_terms_without_career_evidence": 0.16,
        "expert_skills_zero_duration": 0.12,
        "service_only_without_product_search_evidence": 0.12,
        "stale_low_response": 0.10,
        "shallow_ai_tool_interest": 0.10,
    }
    return min(0.45, sum(weights.get(flag, 0.05) for flag in flags))

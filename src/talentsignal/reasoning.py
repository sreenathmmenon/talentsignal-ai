from __future__ import annotations

from .features import CandidateEvidence
from .scoring import ScoreBreakdown


def _join_terms(terms: list[str], limit: int = 3) -> str:
    return ", ".join(terms[:limit])


def generate_reasoning(ev: CandidateEvidence, score: ScoreBreakdown, rank: int) -> str:
    strengths: list[str] = []
    concerns: list[str] = []
    if ev.career_retrieval_terms:
        strengths.append(f"career evidence for {_join_terms(ev.career_retrieval_terms)}")
    elif ev.retrieval_terms:
        strengths.append(f"profile mentions {_join_terms(ev.retrieval_terms)}")
    if ev.career_production_terms:
        strengths.append(f"production signals such as {_join_terms(ev.career_production_terms)}")
    if ev.vector_terms:
        strengths.append(f"vector/search tooling ({_join_terms(ev.vector_terms)})")
    if ev.eval_terms:
        strengths.append(f"ranking evaluation terms ({_join_terms(ev.eval_terms)})")
    if ev.product_company_count:
        strengths.append("product-company background")
    if ev.open_to_work and ev.response_rate >= 0.5:
        strengths.append(f"active hireability with {ev.response_rate:.2f} recruiter response rate")
    if not strengths:
        strengths.append("some adjacent technical/profile signals")

    if ev.notice_period_days > 90:
        concerns.append(f"{ev.notice_period_days}-day notice period")
    if ev.last_active_months >= 6:
        concerns.append("stale recent activity")
    if score.risk_flags:
        concerns.append("risk flags: " + ", ".join(score.risk_flags[:2]))
    if not ev.career_retrieval_terms and rank <= 50:
        concerns.append("limited direct career evidence for retrieval/ranking")

    first = f"{ev.title} with {ev.years:.1f} years in {ev.location}; " + "; ".join(strengths[:3]) + "."
    if concerns:
        return first + " Concern: " + "; ".join(concerns[:2]) + "."
    return first


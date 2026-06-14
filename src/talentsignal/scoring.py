from __future__ import annotations

from dataclasses import dataclass

from .features import CandidateEvidence
from .jd_parser import JobSpec
from .risk_audit import risk_flags, risk_penalty


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


@dataclass
class ScoreBreakdown:
    candidate_id: str
    final_score: float
    technical_evidence: float
    career_fit: float
    seniority: float
    logistics: float
    behavioral: float
    trust: float
    confidence: float
    top10_eligible: bool
    penalty: float
    risk_flags: list[str]


def score_candidate(ev: CandidateEvidence, job: JobSpec) -> ScoreBreakdown:
    technical = 0.0
    technical += min(0.28, 0.07 * len(ev.career_retrieval_terms))
    technical += min(0.18, 0.045 * len(ev.vector_terms))
    technical += min(0.16, 0.04 * len(ev.eval_terms))
    technical += min(0.18, 0.045 * len(ev.career_production_terms))
    technical += min(0.12, 0.015 * len(ev.ml_terms))
    technical += 0.08 if ev.skill_assessment_max >= 70 else 0.04 if ev.skill_assessment_max >= 50 else 0.0
    technical = clamp(technical)

    career = 0.0
    career += 0.32 if ev.ai_title else 0.18 if ev.adjacent_title else 0.0
    career += 0.18 if ev.product_company_count else 0.0
    career += 0.16 if ev.career_retrieval_terms else 0.0
    career += 0.12 if ev.career_production_terms else 0.0
    career += 0.10 if "hr" in ev.current_industry.lower() or "ai" in ev.current_industry.lower() or "software" in ev.current_industry.lower() else 0.0
    career -= 0.18 if ev.non_tech_title and not ev.career_retrieval_terms else 0.0
    career -= 0.12 if ev.service_only and not ev.product_company_count else 0.0
    career = clamp(career)

    if job.strongest_min_years <= ev.years <= job.strongest_max_years:
        seniority = 1.0
    elif job.preferred_min_years <= ev.years <= job.preferred_max_years:
        seniority = 0.88
    elif 4 <= ev.years < job.preferred_min_years or job.preferred_max_years < ev.years <= 11:
        seniority = 0.62
    else:
        seniority = 0.25

    loc = ev.location.lower()
    preferred_city = any(city.lower() in loc for city in job.preferred_locations)
    logistics = 0.0
    logistics += 0.55 if ev.country.lower() == job.country_preferred.lower() else 0.15
    logistics += 0.25 if preferred_city else 0.0
    logistics += 0.15 if ev.willing_to_relocate else 0.0
    logistics += 0.05 if ev.preferred_work_mode in {"hybrid", "flexible"} else 0.0
    logistics = clamp(logistics)

    response_time_score = clamp(1.0 - ev.response_time_hours / 240.0)
    notice_score = 1.0 if ev.notice_period_days <= 30 else 0.7 if ev.notice_period_days <= 60 else 0.35 if ev.notice_period_days <= 90 else 0.15
    active_score = 1.0 if ev.last_active_months <= 1 else 0.75 if ev.last_active_months <= 3 else 0.35 if ev.last_active_months <= 6 else 0.1
    behavioral = (
        0.18 * (ev.profile_completeness / 100.0)
        + 0.18 * active_score
        + 0.16 * (1.0 if ev.open_to_work else 0.25)
        + 0.18 * ev.response_rate
        + 0.08 * response_time_score
        + 0.10 * notice_score
        + 0.06 * clamp(ev.interview_completion_rate)
        + 0.03 * (1.0 if ev.verified_email else 0.0)
        + 0.03 * (1.0 if ev.verified_phone else 0.0)
    )
    behavioral = clamp(behavioral)

    trust = 0.0
    trust += 0.22 if ev.linkedin_connected else 0.0
    trust += 0.18 if ev.github_activity_score >= 40 else 0.10 if ev.github_activity_score >= 10 else 0.0
    trust += 0.18 if ev.saved_by_recruiters_30d >= 10 else 0.10 if ev.saved_by_recruiters_30d >= 4 else 0.0
    trust += 0.18 if ev.search_appearance_30d >= 150 else 0.10 if ev.search_appearance_30d >= 60 else 0.0
    trust += 0.14 if ev.offer_acceptance_rate >= 0.5 else 0.06 if ev.offer_acceptance_rate >= 0 else 0.0
    trust += 0.10 if ev.skill_assessment_max >= 70 else 0.0
    trust = clamp(trust)

    flags = risk_flags(ev)
    penalty = risk_penalty(flags)
    direct_career_evidence = bool(ev.career_retrieval_terms and (ev.career_production_terms or ev.eval_terms or ev.vector_terms))
    top10_eligible = direct_career_evidence and not any(
        flag in flags
        for flag in {
            "non_tech_ai_keyword_stuffing",
            "ai_terms_without_career_evidence",
            "expert_skills_zero_duration",
            "shallow_ai_tool_interest",
        }
    )
    confidence = 0.0
    confidence += 0.30 if ev.career_retrieval_terms else 0.0
    confidence += 0.20 if ev.career_production_terms else 0.0
    confidence += 0.15 if ev.ai_title or ev.adjacent_title else 0.0
    confidence += 0.10 if ev.vector_terms else 0.0
    confidence += 0.10 if ev.eval_terms else 0.0
    confidence += 0.10 if ev.response_rate >= 0.5 and ev.open_to_work else 0.0
    confidence += 0.05 if not flags else 0.0
    confidence = clamp(confidence)
    if not top10_eligible:
        penalty += 0.04
    weights = job.weights
    raw = (
        weights["technical_evidence"] * technical
        + weights["career_fit"] * career
        + weights["seniority"] * seniority
        + weights["logistics"] * logistics
        + weights["behavioral"] * behavioral
        + weights["trust"] * trust
    )
    if not ev.career_retrieval_terms and not ev.ai_title and ev.non_tech_title:
        penalty += 0.08
    final = clamp(raw - penalty)
    return ScoreBreakdown(
        candidate_id=ev.candidate_id,
        final_score=round(final, 6),
        technical_evidence=round(technical, 6),
        career_fit=round(career, 6),
        seniority=round(seniority, 6),
        logistics=round(logistics, 6),
        behavioral=round(behavioral, 6),
        trust=round(trust, 6),
        confidence=round(confidence, 6),
        top10_eligible=top10_eligible,
        penalty=round(penalty, 6),
        risk_flags=flags,
    )

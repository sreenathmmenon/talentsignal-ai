from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from . import talent_graph as tg


REFERENCE_DATE = date(2026, 6, 14)


def norm(text: Any) -> str:
    return str(text or "").strip().lower()


def contains_any(text: str, terms: set[str]) -> list[str]:
    return sorted(term for term in terms if term in text)


def months_since(date_text: str | None) -> int:
    if not date_text:
        return 999
    try:
        year, month, day = map(int, date_text.split("-"))
        dt = date(year, month, day)
    except Exception:
        return 999
    return max(0, (REFERENCE_DATE.year - dt.year) * 12 + (REFERENCE_DATE.month - dt.month) - (1 if REFERENCE_DATE.day < dt.day else 0))


@dataclass
class CandidateEvidence:
    candidate_id: str
    title: str
    title_norm: str
    years: float
    location: str
    country: str
    current_company: str
    current_industry: str
    all_text: str
    career_text: str
    skill_names: list[str]
    skill_text: str
    retrieval_terms: list[str]
    vector_terms: list[str]
    ml_terms: list[str]
    eval_terms: list[str]
    production_terms: list[str]
    career_retrieval_terms: list[str]
    career_production_terms: list[str]
    skill_retrieval_terms: list[str]
    skill_vector_terms: list[str]
    skill_ml_terms: list[str]
    title_relevance_terms: list[str]
    product_company_count: int
    service_company_count: int
    service_only: bool
    non_tech_title: bool
    ai_title: bool
    adjacent_title: bool
    expert_zero_duration: int
    shallow_ai_terms: list[str]
    profile_completeness: float
    last_active_months: int
    open_to_work: bool
    response_rate: float
    response_time_hours: float
    notice_period_days: int
    github_activity_score: float
    search_appearance_30d: int
    saved_by_recruiters_30d: int
    interview_completion_rate: float
    offer_acceptance_rate: float
    verified_email: bool
    verified_phone: bool
    linkedin_connected: bool
    willing_to_relocate: bool
    preferred_work_mode: str
    skill_assessment_max: float


def build_evidence(candidate: dict[str, Any]) -> CandidateEvidence:
    profile = candidate["profile"]
    signals = candidate["redrob_signals"]
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    title = profile.get("current_title", "")
    title_norm = norm(title)
    skill_names = [str(s.get("name", "")) for s in skills if s.get("name")]
    skill_text = " ".join(skill_names).lower()
    career_text = " ".join(
        " ".join(
            [
                str(job.get("title", "")),
                str(job.get("company", "")),
                str(job.get("industry", "")),
                str(job.get("description", "")),
            ]
        )
        for job in career
    ).lower()
    profile_text = " ".join(
        [
            str(profile.get("headline", "")),
            str(profile.get("summary", "")),
            str(profile.get("current_title", "")),
            str(profile.get("current_industry", "")),
        ]
    ).lower()
    all_text = " ".join([profile_text, career_text, skill_text])
    companies = [norm(job.get("company")) for job in career]
    service_count = sum(1 for c in companies if c in tg.SERVICE_COMPANIES)
    product_count = sum(1 for c in companies if c in tg.PRODUCT_COMPANIES)
    assessments = signals.get("skill_assessment_scores") or {}
    expert_zero = sum(
        1
        for skill in skills
        if norm(skill.get("proficiency")) == "expert" and int(skill.get("duration_months") or 0) == 0
    )
    return CandidateEvidence(
        candidate_id=str(candidate["candidate_id"]),
        title=str(title),
        title_norm=title_norm,
        years=float(profile.get("years_of_experience") or 0.0),
        location=str(profile.get("location", "")),
        country=str(profile.get("country", "")),
        current_company=str(profile.get("current_company", "")),
        current_industry=str(profile.get("current_industry", "")),
        all_text=all_text,
        career_text=career_text,
        skill_names=skill_names,
        skill_text=skill_text,
        retrieval_terms=contains_any(all_text, tg.RETRIEVAL_TERMS),
        vector_terms=contains_any(all_text, tg.VECTOR_TERMS),
        ml_terms=contains_any(all_text, tg.ML_TERMS),
        eval_terms=contains_any(all_text, tg.EVAL_TERMS),
        production_terms=contains_any(all_text, tg.PRODUCTION_TERMS),
        career_retrieval_terms=contains_any(career_text, tg.RETRIEVAL_TERMS),
        career_production_terms=contains_any(career_text, tg.PRODUCTION_TERMS),
        skill_retrieval_terms=contains_any(skill_text, tg.RETRIEVAL_TERMS),
        skill_vector_terms=contains_any(skill_text, tg.VECTOR_TERMS),
        skill_ml_terms=contains_any(skill_text, tg.ML_TERMS),
        title_relevance_terms=contains_any(title_norm, tg.RETRIEVAL_TERMS | tg.ML_TERMS),
        product_company_count=product_count,
        service_company_count=service_count,
        service_only=bool(companies) and service_count == len(companies),
        non_tech_title=title_norm in tg.NON_TECH_TITLES,
        ai_title=title_norm in tg.AI_TITLES,
        adjacent_title=title_norm in tg.ADJACENT_TITLES,
        expert_zero_duration=expert_zero,
        shallow_ai_terms=contains_any(all_text, tg.SHALLOW_AI_TERMS),
        profile_completeness=float(signals.get("profile_completeness_score") or 0.0),
        last_active_months=months_since(signals.get("last_active_date")),
        open_to_work=bool(signals.get("open_to_work_flag")),
        response_rate=float(signals.get("recruiter_response_rate") or 0.0),
        response_time_hours=float(signals.get("avg_response_time_hours") or 999.0),
        notice_period_days=int(signals.get("notice_period_days") or 0),
        github_activity_score=float(signals.get("github_activity_score") if signals.get("github_activity_score") is not None else -1.0),
        search_appearance_30d=int(signals.get("search_appearance_30d") or 0),
        saved_by_recruiters_30d=int(signals.get("saved_by_recruiters_30d") or 0),
        interview_completion_rate=float(signals.get("interview_completion_rate") or 0.0),
        offer_acceptance_rate=float(signals.get("offer_acceptance_rate") if signals.get("offer_acceptance_rate") is not None else -1.0),
        verified_email=bool(signals.get("verified_email")),
        verified_phone=bool(signals.get("verified_phone")),
        linkedin_connected=bool(signals.get("linkedin_connected")),
        willing_to_relocate=bool(signals.get("willing_to_relocate")),
        preferred_work_mode=str(signals.get("preferred_work_mode", "")),
        skill_assessment_max=max([float(v) for v in assessments.values()], default=0.0),
    )

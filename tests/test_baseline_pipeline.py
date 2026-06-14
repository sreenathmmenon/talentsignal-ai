from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.features import build_evidence
from talentsignal.jd_parser import load_job_spec
from talentsignal.risk_audit import risk_flags
from talentsignal.scoring import score_candidate
from talentsignal.explanation_audit import audit_packets


def test_job_spec_loads() -> None:
    spec = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")
    assert spec.id == "redrob_senior_ai_engineer"
    assert spec.weights["technical_evidence"] > 0


def test_evidence_and_scoring_for_sample_candidate() -> None:
    candidate = {
        "candidate_id": "CAND_9999999",
        "profile": {
            "headline": "ML Engineer",
            "summary": "Built production retrieval and ranking systems in Python.",
            "location": "Pune, Maharashtra",
            "country": "India",
            "years_of_experience": 6.5,
            "current_title": "ML Engineer",
            "current_company": "Razorpay",
            "current_company_size": "1001-5000",
            "current_industry": "Software",
        },
        "career_history": [
            {
                "company": "Razorpay",
                "title": "ML Engineer",
                "start_date": "2020-01-01",
                "end_date": None,
                "duration_months": 72,
                "is_current": True,
                "industry": "Fintech",
                "company_size": "1001-5000",
                "description": "Shipped production vector search, retrieval ranking, and NDCG evaluation.",
            }
        ],
        "education": [],
        "skills": [{"name": "Python", "proficiency": "expert", "endorsements": 10, "duration_months": 72}],
        "redrob_signals": {
            "profile_completeness_score": 90,
            "signup_date": "2025-01-01",
            "last_active_date": "2026-06-01",
            "open_to_work_flag": True,
            "profile_views_received_30d": 20,
            "applications_submitted_30d": 2,
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 20,
            "skill_assessment_scores": {"Python": 85},
            "connection_count": 100,
            "endorsements_received": 20,
            "notice_period_days": 30,
            "expected_salary_range_inr_lpa": {"min": 20, "max": 35},
            "preferred_work_mode": "hybrid",
            "willing_to_relocate": True,
            "github_activity_score": 50,
            "search_appearance_30d": 150,
            "saved_by_recruiters_30d": 12,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.7,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True,
        },
    }
    ev = build_evidence(candidate)
    spec = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")
    score = score_candidate(ev, spec)
    assert ev.career_retrieval_terms
    assert score.final_score > 0.5
    assert not score.risk_flags


def test_non_tech_ai_keyword_stuffer_is_flagged() -> None:
    candidate = {
        "candidate_id": "CAND_9999998",
        "profile": {
            "headline": "Marketing Manager exploring AI",
            "summary": "Curious about AI tools, ChatGPT, RAG, LLM, embeddings, NLP, and fine tuning.",
            "location": "Chennai, Tamil Nadu",
            "country": "India",
            "years_of_experience": 8.0,
            "current_title": "Marketing Manager",
            "current_company": "Wipro",
            "current_company_size": "10001+",
            "current_industry": "IT Services",
        },
        "career_history": [
            {
                "company": "Wipro",
                "title": "Marketing Manager",
                "start_date": "2020-01-01",
                "end_date": None,
                "duration_months": 72,
                "is_current": True,
                "industry": "IT Services",
                "company_size": "10001+",
                "description": "Owned marketing campaigns and customer communication.",
            }
        ],
        "education": [],
        "skills": [
            {"name": "RAG", "proficiency": "expert", "endorsements": 0, "duration_months": 0},
            {"name": "LLM", "proficiency": "expert", "endorsements": 0, "duration_months": 0},
            {"name": "Embeddings", "proficiency": "expert", "endorsements": 0, "duration_months": 0},
        ],
        "redrob_signals": {
            "profile_completeness_score": 50,
            "signup_date": "2025-01-01",
            "last_active_date": "2025-01-01",
            "open_to_work_flag": True,
            "profile_views_received_30d": 1,
            "applications_submitted_30d": 1,
            "recruiter_response_rate": 0.1,
            "avg_response_time_hours": 200,
            "skill_assessment_scores": {},
            "connection_count": 10,
            "endorsements_received": 0,
            "notice_period_days": 120,
            "expected_salary_range_inr_lpa": {"min": 10, "max": 20},
            "preferred_work_mode": "remote",
            "willing_to_relocate": False,
            "github_activity_score": -1,
            "search_appearance_30d": 5,
            "saved_by_recruiters_30d": 0,
            "interview_completion_rate": 0.3,
            "offer_acceptance_rate": -1,
            "verified_email": False,
            "verified_phone": False,
            "linkedin_connected": False,
        },
    }
    ev = build_evidence(candidate)
    flags = risk_flags(ev)
    assert "non_tech_ai_keyword_stuffing" in flags
    assert "expert_skills_zero_duration" in flags


def test_stale_unresponsive_candidate_scores_lower_than_active_peer() -> None:
    base = {
        "candidate_id": "CAND_9999997",
        "profile": {
            "headline": "ML Engineer",
            "summary": "Built production retrieval ranking systems.",
            "location": "Pune, Maharashtra",
            "country": "India",
            "years_of_experience": 7.0,
            "current_title": "ML Engineer",
            "current_company": "Razorpay",
            "current_company_size": "1001-5000",
            "current_industry": "Software",
        },
        "career_history": [
            {
                "company": "Razorpay",
                "title": "ML Engineer",
                "start_date": "2020-01-01",
                "end_date": None,
                "duration_months": 72,
                "is_current": True,
                "industry": "Fintech",
                "company_size": "1001-5000",
                "description": "Shipped production retrieval ranking search with NDCG evaluation.",
            }
        ],
        "education": [],
        "skills": [{"name": "Python", "proficiency": "expert", "endorsements": 10, "duration_months": 72}],
    }
    active = {
        **base,
        "redrob_signals": {
            "profile_completeness_score": 95,
            "signup_date": "2025-01-01",
            "last_active_date": "2026-06-01",
            "open_to_work_flag": True,
            "profile_views_received_30d": 20,
            "applications_submitted_30d": 2,
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 20,
            "skill_assessment_scores": {"Python": 85},
            "connection_count": 100,
            "endorsements_received": 20,
            "notice_period_days": 30,
            "expected_salary_range_inr_lpa": {"min": 20, "max": 35},
            "preferred_work_mode": "hybrid",
            "willing_to_relocate": True,
            "github_activity_score": 50,
            "search_appearance_30d": 150,
            "saved_by_recruiters_30d": 12,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.7,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True,
        },
    }
    stale = {
        **base,
        "candidate_id": "CAND_9999996",
        "redrob_signals": {
            **active["redrob_signals"],
            "last_active_date": "2025-01-01",
            "open_to_work_flag": False,
            "recruiter_response_rate": 0.05,
            "avg_response_time_hours": 240,
            "notice_period_days": 150,
            "verified_email": False,
            "verified_phone": False,
            "linkedin_connected": False,
        },
    }
    spec = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")
    active_score = score_candidate(build_evidence(active), spec)
    stale_score = score_candidate(build_evidence(stale), spec)
    assert active_score.final_score > stale_score.final_score
    assert active_score.top10_eligible


def test_explanation_audit_accepts_existing_packets_if_present() -> None:
    path = Path("outputs/evidence_packets.jsonl")
    if path.exists():
        assert audit_packets(path) == []

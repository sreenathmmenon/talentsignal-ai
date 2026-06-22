from __future__ import annotations

from typing import Any

from .candidate_compare import FACTOR_LABELS, weakest_factor


def build_interview_kit(packet: dict[str, Any], job: Any) -> dict[str, Any]:
    evidence = packet["evidence"]
    weak_key, weak_value = weakest_factor(packet)
    risks = packet["score_breakdown"].get("risk_flags", [])
    retrieval_terms = evidence.get("career_retrieval_terms", []) or evidence.get("vector_terms", []) or ["the claimed role fit"]
    production_terms = evidence.get("career_production_terms", []) or evidence.get("production_terms", []) or ["production ownership"]
    questions = [
        {
            "type": "technical_or_functional_depth",
            "question": (
                f"Walk through the most relevant work behind {', '.join(retrieval_terms[:3])}. "
                f"What was your role, what tradeoffs did you make, and how did you measure success?"
            ),
        },
        {
            "type": "production_or_execution_validation",
            "question": (
                f"Describe a shipped system or business outcome connected to {', '.join(production_terms[:3])}. "
                "What broke, what did you monitor, and what changed after launch?"
            ),
        },
        {
            "type": "weak_area_probe",
            "question": (
                f"The weakest current factor is {FACTOR_LABELS.get(weak_key, weak_key)} at {weak_value:.3f}. "
                "What evidence should the hiring team use to validate or override this concern?"
            ),
        },
    ]
    if risks:
        questions.append(
            {
                "type": "risk_validation",
                "question": f"Validate these risk signals directly: {', '.join(risks)}. What profile evidence resolves them?",
            }
        )
    else:
        questions.append(
            {
                "type": "role_commitment",
                "question": f"Why is this {job.title} role the right next move, and what would you ship in the first 90 days?",
            }
        )
    return {
        "candidate_id": packet["candidate_id"],
        "rank": packet["rank"],
        "job_title": job.title,
        "focus": f"Validate {packet['candidate_id']} against {job.title} using evidence, weak areas, and risk signals.",
        "questions": questions,
        "decision_rubric": [
            "Hire only if the candidate can explain concrete shipped work behind the strongest evidence terms.",
            "Downgrade if examples stay generic or cannot connect profile claims to outcomes.",
            "Use weak-factor and risk answers to decide whether the ranking should stand.",
        ],
    }


def build_interview_kits(packets: list[dict[str, Any]], job: Any, limit: int = 10) -> list[dict[str, Any]]:
    return [build_interview_kit(packet, job) for packet in packets[:limit]]


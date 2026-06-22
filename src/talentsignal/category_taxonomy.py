from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryProfile:
    category: str
    label: str
    core_signals: tuple[str, ...]
    evidence_priorities: tuple[str, ...]
    common_risks: tuple[str, ...]
    default_weights: dict[str, float]


BASE_WEIGHTS = {
    "technical_evidence": 0.30,
    "career_fit": 0.24,
    "seniority": 0.12,
    "logistics": 0.10,
    "behavioral": 0.16,
    "trust": 0.08,
}


CATEGORY_PROFILES: dict[str, CategoryProfile] = {
    "ai_ml_search_ranking": CategoryProfile(
        category="ai_ml_search_ranking",
        label="AI/ML search, ranking, retrieval",
        core_signals=("production ML", "retrieval/search/ranking", "Python", "evaluation", "shipping ownership"),
        evidence_priorities=("career descriptions", "deployed systems", "ranking metrics", "vector/search tooling"),
        common_risks=("keyword stuffing", "shallow API demos", "research without production", "irrelevant AI domain"),
        default_weights={
            "technical_evidence": 0.34,
            "career_fit": 0.22,
            "seniority": 0.10,
            "logistics": 0.10,
            "behavioral": 0.17,
            "trust": 0.07,
        },
    ),
    "backend_engineering": CategoryProfile(
        category="backend_engineering",
        label="Backend/platform engineering",
        core_signals=("distributed systems", "APIs", "databases", "reliability", "ownership"),
        evidence_priorities=("system design", "production scale", "incident ownership", "data modeling"),
        common_risks=("framework-only experience", "no scale evidence", "support-only implementation"),
        default_weights=BASE_WEIGHTS,
    ),
    "data_analytics": CategoryProfile(
        category="data_analytics",
        label="Data analytics and decision science",
        core_signals=("SQL", "metrics", "experimentation", "dashboards", "business impact"),
        evidence_priorities=("metric definitions", "stakeholder decisions", "experiments", "data quality"),
        common_risks=("dashboard-only work", "unclear business impact", "tool keyword stuffing"),
        default_weights={**BASE_WEIGHTS, "technical_evidence": 0.26, "career_fit": 0.28},
    ),
    "product_management": CategoryProfile(
        category="product_management",
        label="Product management",
        core_signals=("discovery", "launches", "metrics", "roadmap", "cross-functional leadership"),
        evidence_priorities=("launched products", "customer insight", "business outcomes", "tradeoff decisions"),
        common_risks=("project coordination only", "no shipped product", "weak metrics ownership"),
        default_weights={**BASE_WEIGHTS, "technical_evidence": 0.20, "career_fit": 0.32},
    ),
    "sales_gtm": CategoryProfile(
        category="sales_gtm",
        label="Sales and GTM",
        core_signals=("quota", "pipeline", "ICP", "region", "enterprise motion"),
        evidence_priorities=("quota attainment", "deal size", "sales motion", "CRM discipline"),
        common_risks=("lead-gen only", "no quota evidence", "wrong segment motion"),
        default_weights={**BASE_WEIGHTS, "technical_evidence": 0.18, "career_fit": 0.34},
    ),
    "design_product": CategoryProfile(
        category="design_product",
        label="Product design",
        core_signals=("portfolio", "systems thinking", "research", "interaction design", "shipping"),
        evidence_priorities=("case studies", "usable shipped work", "design systems", "user validation"),
        common_risks=("visual-only work", "no product impact", "template portfolio"),
        default_weights={**BASE_WEIGHTS, "technical_evidence": 0.22, "career_fit": 0.30},
    ),
}


def get_category_profile(category: str) -> CategoryProfile:
    return CATEGORY_PROFILES.get(category, CategoryProfile(
        category=category,
        label=category.replace("_", " ").title(),
        core_signals=("role-specific evidence", "career fit", "execution proof"),
        evidence_priorities=("career descriptions", "skills", "behavioral signals"),
        common_risks=("weak evidence", "stale profile", "keyword stuffing"),
        default_weights=BASE_WEIGHTS,
    ))


def validate_weights(weights: dict[str, float]) -> None:
    required = set(BASE_WEIGHTS)
    missing = required.difference(weights)
    if missing:
        raise ValueError(f"missing score weights: {', '.join(sorted(missing))}")
    total = sum(float(weights[key]) for key in required)
    if not 0.95 <= total <= 1.05:
        raise ValueError(f"score weights should sum near 1.0, got {total:.3f}")


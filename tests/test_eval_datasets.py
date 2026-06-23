"""Validate the synthetic labeled-candidate generator: schema-valid records,
correct grades, deterministic output, true zero-keyword paraphrase cases, and a
working alternate (non-Redrob) signal schema.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.eval import datasets as D
from talentsignal.eval.roles import ROLES, AI_SEARCH

REQUIRED_TOP = ["candidate_id", "profile", "career_history", "education", "skills", "redrob_signals"]
REQUIRED_PROFILE = [
    "anonymized_name", "headline", "summary", "location", "country",
    "years_of_experience", "current_title", "current_company",
    "current_company_size", "current_industry",
]
COMPANY_SIZES = {"1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10001+"}


def _is_schema_valid(rec: dict) -> bool:
    if not all(k in rec for k in REQUIRED_TOP):
        return False
    if not all(k in rec["profile"] for k in REQUIRED_PROFILE):
        return False
    if rec["profile"]["current_company_size"] not in COMPANY_SIZES:
        return False
    if not rec["candidate_id"].startswith("CAND_") or len(rec["candidate_id"]) != 12:
        return False
    if len(rec["career_history"]) < 1:
        return False
    return True


def test_pool_is_schema_valid() -> None:
    pool = D.build_pool(AI_SEARCH)
    assert len(pool) == sum(D.DEFAULT_MIX.values())
    assert all(_is_schema_valid(c.record) for c in pool)


def test_grades_match_archetypes() -> None:
    pool = D.build_pool(AI_SEARCH)
    for c in pool:
        assert c.grade == D.ARCHETYPE_GRADE[c.archetype]
    # honeypots are always grade 0
    assert all(c.grade == 0 for c in pool if c.archetype == D.HONEYPOT)


def test_deterministic() -> None:
    a = D.build_pool(AI_SEARCH)
    b = D.build_pool(AI_SEARCH)
    assert [c.candidate_id for c in a] == [c.candidate_id for c in b]
    assert [c.record["profile"]["summary"] for c in a] == [c.record["profile"]["summary"] for c in b]


def test_paraphrase_ideal_has_zero_keyword_overlap() -> None:
    # The whole point: a strong fit described without the role's keywords.
    keyworded = " ".join(AI_SEARCH.evidence_keyworded).lower()
    paraphrased = " ".join(AI_SEARCH.evidence_paraphrased).lower()
    salient = {"embedding", "embeddings", "retrieval", "ranking", "rank", "ranker",
               "faiss", "ndcg", "vector", "recommendation", "recommender", "semantic", "search"}
    leaked = [t for t in salient if t in paraphrased]
    assert leaked == [], f"paraphrase leaks keywords: {leaked}"


def test_honeypot_is_internally_impossible() -> None:
    pool = D.build_pool(AI_SEARCH, mix={D.HONEYPOT: 5})
    for c in pool:
        rec = c.record
        # expert skills with zero duration
        assert any(s["proficiency"] == "expert" and s["duration_months"] == 0 for s in rec["skills"])
        # tenure that exceeds plausible company existence (impossible)
        stated_months = rec["profile"]["years_of_experience"] * 12
        claimed = sum(j["duration_months"] for j in rec["career_history"])
        assert claimed > stated_months  # contradiction is present


def test_alt_schema_variant_uses_different_signal_fields() -> None:
    redrob = D.make_candidate(AI_SEARCH, D.STRONG, 0, schema_variant="redrob")
    alt = D.make_candidate(AI_SEARCH, D.STRONG, 0, schema_variant="alt")
    assert "recruiter_response_rate" in redrob.record["redrob_signals"]
    assert "recruiter_response_rate" not in alt.record["redrob_signals"]
    assert "reply_rate" in alt.record["redrob_signals"]


def test_labels_and_records_helpers() -> None:
    pool = D.build_pool(AI_SEARCH, mix={D.STRONG: 3, D.HONEYPOT: 2})
    labels = D.labels_of(pool)
    records = D.records_of(pool)
    assert len(labels) == 5 and len(records) == 5
    # records carry no leaked grade field
    assert all("grade" not in r for r in records)


def test_all_roles_build() -> None:
    for role in ROLES.values():
        pool = D.build_pool(role, mix={D.STRONG: 2, D.PARAPHRASE_IDEAL: 2, D.IRRELEVANT: 2})
        assert len(pool) == 6
        assert all(_is_schema_valid(c.record) for c in pool)

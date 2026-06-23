"""Labeled synthetic candidate generator for evaluation.

Produces schema-valid candidate profiles (matching candidate_schema.json) with a
ground-truth relevance grade attached, so any ranker can be scored with the
metrics module against controlled truth. This is what lets us measure ranking
quality with no leaderboard and no organizer labels.

Design goals:
  * Deterministic — every candidate is a pure function of (archetype, seed,
    index), so eval runs are reproducible.
  * Schema-valid — generated records pass candidate_schema.json.
  * Hard cases on purpose — the generator can emit the exact profiles that
    separate a real ranking system from a keyword matcher:
      - PARAPHRASE_IDEAL: a strong fit described WITHOUT the JD's keywords
        (tests semantic matching).
      - HONEYPOT: keyword-dense but internally impossible (tests trap rejection;
        forced to grade 0).
      - BEHAVIORAL_TWIN: strong on paper but stale/unresponsive (tests that
        behavioral signals down-weight unhireable candidates).

Relevance grades (align with eval.metrics):
    5 strong direct-evidence fit
    4 strong fit, described in paraphrase (no shared keywords)
    3 solid adjacent fit (relevant for P@10)
    1 weak / tangential
    0 irrelevant OR honeypot (never belongs in the top)

The grade is the GROUND TRUTH; it is stored alongside the record and is NOT a
field the ranker sees (the ranker only sees the schema fields).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable

# --- archetypes -------------------------------------------------------------

STRONG = "strong"              # grade 5: direct-evidence fit, uses role vocabulary
PARAPHRASE_IDEAL = "paraphrase"  # grade 4: same fit, zero keyword overlap
ADJACENT = "adjacent"          # grade 3: relevant but partial
WEAK = "weak"                  # grade 1: tangential
IRRELEVANT = "irrelevant"      # grade 0: wrong role
HONEYPOT = "honeypot"          # grade 0: impossible profile, keyword-stuffed
BEHAVIORAL_TWIN = "behavioral_twin"  # strong content, dead engagement signals

ARCHETYPE_GRADE = {
    STRONG: 5,
    PARAPHRASE_IDEAL: 4,
    ADJACENT: 3,
    WEAK: 1,
    IRRELEVANT: 0,
    HONEYPOT: 0,
    BEHAVIORAL_TWIN: 3,  # content is strong; a good ranker still down-weights it
}

COMPANY_SIZES = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10001+"]
EDU_TIERS = ["tier_1", "tier_2", "tier_3", "tier_4", "unknown"]


def _rng(seed: str) -> Callable[[int], int]:
    """Tiny deterministic pseudo-random integer stream from a string seed.

    Avoids Date/Math.random style nondeterminism; pure hash-based so results are
    stable across machines and runs (important for reproducible eval).
    """
    state = {"h": hashlib.sha256(seed.encode("utf-8")).digest(), "i": 0}

    def nxt(modulo: int) -> int:
        if state["i"] >= len(state["h"]):
            state["h"] = hashlib.sha256(state["h"]).digest()
            state["i"] = 0
        b = state["h"][state["i"]]
        state["i"] += 1
        return b % modulo if modulo else 0

    return nxt


def _pick(rand: Callable[[int], int], options: list[Any]) -> Any:
    return options[rand(len(options))]


@dataclass
class RoleProfile:
    """Describes a role for the generator: the vocabulary that signals fit, and
    paraphrases of that vocabulary that mean the same thing with NO shared words.

    This is what makes the dataset JD-agnostic: pass a RoleProfile for sales, for
    AI, for design, and the generator produces the right fits and traps for it.
    """
    role_id: str
    titles_strong: list[str]
    titles_adjacent: list[str]
    titles_irrelevant: list[str]
    # keyword phrases that directly signal fit (used by STRONG)
    evidence_keyworded: list[str]
    # paraphrases of the same competencies with NO shared keywords (PARAPHRASE_IDEAL)
    evidence_paraphrased: list[str]
    adjacent_evidence: list[str]
    weak_evidence: list[str]
    irrelevant_evidence: list[str]
    skills_strong: list[str]
    skills_adjacent: list[str]
    locations: list[str] = field(default_factory=lambda: ["Bangalore, Karnataka", "Pune, Maharashtra", "Noida, Uttar Pradesh"])
    country: str = "India"
    industry: str = "Software"


@dataclass
class LabeledCandidate:
    candidate_id: str
    archetype: str
    grade: int
    record: dict[str, Any]


def _signals(rand: Callable[[int], int], *, active: bool = True, schema_variant: str = "redrob") -> dict[str, Any]:
    """Build a behavioral-signals object.

    schema_variant lets us emit a DIFFERENT signal vocabulary than Redrob's 23
    fields (to prove schema-driven handling). "redrob" = the challenge schema;
    "alt" = a renamed/leaner availability schema a different platform might use.
    """
    response = (60 + rand(40)) / 100.0 if active else (rand(15)) / 100.0
    last_active = rand(2) if active else 6 + rand(8)  # months since active
    if schema_variant == "alt":
        return {
            "completeness": 60 + rand(40),
            "days_since_login": last_active * 30,
            "available": active,
            "reply_rate": round(response, 2),
            "avg_reply_hours": (2 + rand(20)) if active else (120 + rand(120)),
            "notice_days": _pick(rand, [0, 15, 30, 45, 60, 90]),
            "recruiter_saves_30d": (rand(20)) if active else rand(3),
            "is_email_verified": True,
            "is_phone_verified": active,
            "external_profile_linked": active,
        }
    # default: full Redrob 23-field schema
    return {
        "profile_completeness_score": 60 + rand(40),
        "signup_date": "2022-01-15",
        "last_active_date": _months_ago_date(last_active),
        "open_to_work_flag": active,
        "profile_views_received_30d": rand(200) if active else rand(20),
        "applications_submitted_30d": rand(15) if active else rand(2),
        "recruiter_response_rate": round(response, 2),
        "avg_response_time_hours": float((2 + rand(20)) if active else (120 + rand(120))),
        "skill_assessment_scores": {"core": 60 + rand(40)},
        "connection_count": 100 + rand(900),
        "endorsements_received": rand(200),
        "notice_period_days": _pick(rand, [0, 15, 30, 45, 60, 90, 120]),
        "expected_salary_range_inr_lpa": {"min": 20 + rand(20), "max": 45 + rand(40)},
        "preferred_work_mode": _pick(rand, ["remote", "hybrid", "onsite", "flexible"]),
        "willing_to_relocate": bool(rand(2)),
        "github_activity_score": float(rand(100)) if active else -1.0,
        "search_appearance_30d": rand(300) if active else rand(30),
        "saved_by_recruiters_30d": rand(20) if active else rand(3),
        "interview_completion_rate": round((70 + rand(30)) / 100.0, 2) if active else round(rand(40) / 100.0, 2),
        "offer_acceptance_rate": round((50 + rand(50)) / 100.0, 2),
        "verified_email": True,
        "verified_phone": active,
        "linkedin_connected": active,
    }


def _months_ago_date(months: int) -> str:
    """Reference-stable date string `months` before the dataset reference date.

    Uses a fixed reference (2026-06-14, matching features.REFERENCE_DATE) rather
    than the wall clock, so generated data is deterministic.
    """
    y, m = 2026, 6 - months
    while m <= 0:
        m += 12
        y -= 1
    return f"{y:04d}-{m:02d}-10"


def _career(role: RoleProfile, rand: Callable[[int], int], descriptions: list[str], title: str,
            years: float, *, impossible: bool = False) -> list[dict[str, Any]]:
    months_total = int(years * 12)
    n = max(1, min(3, 1 + rand(3)))
    per = max(6, months_total // n)
    jobs = []
    # If impossible (honeypot), claim tenure that exceeds a freshly-founded company.
    start_year = 2026 - (max(1, years // 1))
    for i in range(n):
        desc = descriptions[i % len(descriptions)]
        company_age_months = per if not impossible else per + 60  # claim > company existence
        jobs.append({
            "company": f"{role.role_id.title()}Co{i+1}",
            "title": title if i == 0 else _pick(rand, role.titles_adjacent or [title]),
            "start_date": f"{int(start_year) + i:04d}-03-01",
            "end_date": None if i == 0 else f"{int(start_year) + i + 1:04d}-02-01",
            "duration_months": company_age_months,
            "is_current": i == 0,
            "industry": role.industry,
            "company_size": _pick(rand, COMPANY_SIZES),
            "description": desc,
        })
    return jobs


def _skills(names: list[str], rand: Callable[[int], int], *, expert_zero: bool = False) -> list[dict[str, Any]]:
    out = []
    for nm in names:
        dur = 0 if expert_zero else 12 + rand(60)
        out.append({
            "name": nm,
            "proficiency": "expert" if expert_zero else _pick(rand, ["intermediate", "advanced", "expert"]),
            "endorsements": 0 if expert_zero else rand(50),
            "duration_months": dur,
        })
    return out


def make_candidate(role: RoleProfile, archetype: str, index: int, *,
                   schema_variant: str = "redrob") -> LabeledCandidate:
    """Generate one labeled, schema-valid candidate of the given archetype."""
    seed = f"{role.role_id}:{archetype}:{schema_variant}:{index}"
    rand = _rng(seed)
    cid = "CAND_" + str(int(hashlib.sha256(seed.encode()).hexdigest(), 16) % 10_000_000).zfill(7)
    years = round(5 + rand(40) / 10.0, 1)  # 5.0 - 8.9 by default
    active = archetype != BEHAVIORAL_TWIN

    if archetype == STRONG:
        title = _pick(rand, role.titles_strong)
        desc = role.evidence_keyworded
        skills = _skills(role.skills_strong, rand)
        summary = "Experienced engineer. " + " ".join(role.evidence_keyworded[:2])
    elif archetype == PARAPHRASE_IDEAL:
        title = _pick(rand, role.titles_adjacent)  # title doesn't shout the role
        desc = role.evidence_paraphrased
        skills = _skills(role.skills_adjacent, rand)  # skills avoid the canonical keywords
        summary = "Builder. " + " ".join(role.evidence_paraphrased[:2])
    elif archetype == ADJACENT:
        title = _pick(rand, role.titles_adjacent)
        desc = role.adjacent_evidence
        skills = _skills(role.skills_adjacent, rand)
        summary = "Adjacent background. " + role.adjacent_evidence[0]
    elif archetype == WEAK:
        title = _pick(rand, role.titles_adjacent)
        desc = role.weak_evidence
        skills = _skills(role.skills_adjacent[:1], rand)
        summary = role.weak_evidence[0]
    elif archetype == IRRELEVANT:
        title = _pick(rand, role.titles_irrelevant)
        desc = role.irrelevant_evidence
        skills = _skills(["Excel", "Communication"], rand)
        summary = role.irrelevant_evidence[0]
    elif archetype == HONEYPOT:
        # Keyword-stuffed (looks strong to a keyword matcher) but impossible.
        title = _pick(rand, role.titles_irrelevant)  # non-matching title
        desc = role.evidence_keyworded  # dense with role keywords
        skills = _skills(role.skills_strong, rand, expert_zero=True)  # expert, 0 months
        summary = " ".join(role.evidence_keyworded)  # stuffed
        years = round(8 + rand(20) / 10.0, 1)
    elif archetype == BEHAVIORAL_TWIN:
        title = _pick(rand, role.titles_strong)
        desc = role.evidence_keyworded
        skills = _skills(role.skills_strong, rand)
        summary = "Strong on paper. " + role.evidence_keyworded[0]
    else:
        raise ValueError(f"unknown archetype {archetype}")

    record: dict[str, Any] = {
        "candidate_id": cid,
        "profile": {
            "anonymized_name": f"Candidate {index}",
            "headline": title,
            "summary": summary,
            "location": _pick(rand, role.locations),
            "country": role.country,
            "years_of_experience": years,
            "current_title": title,
            "current_company": f"{role.role_id.title()}Co1",
            "current_company_size": _pick(rand, COMPANY_SIZES),
            "current_industry": role.industry,
        },
        "career_history": _career(role, rand, desc, title, years, impossible=(archetype == HONEYPOT)),
        "education": [{
            "institution": "Some Institute of Technology",
            "degree": "B.Tech",
            "field_of_study": "Computer Science",
            "start_year": 2014,
            "end_year": 2018,
            "grade": "8.2",
            "tier": _pick(rand, EDU_TIERS),
        }],
        "skills": skills,
        "redrob_signals": _signals(rand, active=active, schema_variant=schema_variant),
    }
    return LabeledCandidate(cid, archetype, ARCHETYPE_GRADE[archetype], record)


# Default archetype mix for a balanced labeled pool (counts per role).
DEFAULT_MIX = {
    STRONG: 8,
    PARAPHRASE_IDEAL: 6,
    ADJACENT: 12,
    WEAK: 20,
    IRRELEVANT: 30,
    HONEYPOT: 10,
    BEHAVIORAL_TWIN: 4,
}


def build_pool(role: RoleProfile, mix: dict[str, int] | None = None,
               *, schema_variant: str = "redrob") -> list[LabeledCandidate]:
    """Build a labeled candidate pool for a role from an archetype mix.

    Returns a list of LabeledCandidate (record + ground-truth grade). De-dupes
    on candidate_id so the labels map is unambiguous.
    """
    mix = mix or DEFAULT_MIX
    pool: list[LabeledCandidate] = []
    seen: set[str] = set()
    for archetype, count in mix.items():
        made = 0
        idx = 0
        while made < count:
            cand = make_candidate(role, archetype, idx, schema_variant=schema_variant)
            idx += 1
            if cand.candidate_id in seen:
                continue
            seen.add(cand.candidate_id)
            pool.append(cand)
            made += 1
    return pool


def labels_of(pool: list[LabeledCandidate]) -> dict[str, float]:
    """candidate_id -> ground-truth grade, for use with metrics.relevances_from_ranking."""
    return {c.candidate_id: float(c.grade) for c in pool}


def records_of(pool: list[LabeledCandidate]) -> list[dict[str, Any]]:
    """The raw schema records a ranker would see (no labels leaked)."""
    return [c.record for c in pool]

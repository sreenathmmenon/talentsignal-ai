from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from .features import CandidateEvidence
from .jd_parser import JobSpec
from .risk_audit import risk_flags, risk_penalty


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


@lru_cache(maxsize=4096)
def _tokenize(text: str) -> frozenset:
    """Whole-token set of a text, lowercased. Cached because the same JD term
    lists are tokenized for every candidate."""
    return frozenset(re.findall(r"[a-z0-9+#]+", text.lower()))


def _term_coverage(text: str, terms: tuple[str, ...]) -> float:
    """Fraction of `terms` whose salient words appear as WHOLE TOKENS in `text`.

    Whole-token matching (not substring) eliminates the bug where 'ml' matched
    inside 'html'/'xml' and 'ai' inside 'maintain' — which silently corrupted
    scores for ~half the pool. A term is covered if any of its >=3-char words is
    present as a standalone token.
    """
    if not terms:
        return 0.0
    tokens = _tokenize(text)
    matched = 0
    for term in terms:
        words = [w for w in re.split(r"[\s/\-]+", term.lower()) if len(w) >= 3]
        if words and any(w in tokens for w in words):
            matched += 1
    return matched / len(terms)


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
    # Additive hybrid fields (defaulted so the spine path and all existing
    # consumers are unaffected). Populated only by the hybrid engine.
    semantic_fit: float = 0.0
    lexical_fit: float = 0.0
    requirement_coverage: float = 0.0
    disqualifier_hits: tuple = ()
    engine: str = "spine"
    # Top matched requirements (text, matched keywords) for grounded reasoning.
    matched_requirements: tuple = ()
    concern_notes: tuple = ()


def _seniority_score(ev: CandidateEvidence, job: JobSpec) -> float:
    if job.strongest_min_years <= ev.years <= job.strongest_max_years:
        return 1.0
    if job.preferred_min_years <= ev.years <= job.preferred_max_years:
        return 0.88
    if 4 <= ev.years < job.preferred_min_years or job.preferred_max_years < ev.years <= 11:
        return 0.62
    return 0.25


def _logistics_score(ev: CandidateEvidence, job: JobSpec) -> float:
    loc = ev.location.lower()
    preferred_city = any(city.lower() in loc for city in job.preferred_locations)
    logistics = 0.55 if ev.country.lower() == job.country_preferred.lower() else 0.15
    logistics += 0.25 if preferred_city else 0.0
    logistics += 0.15 if ev.willing_to_relocate else 0.0
    logistics += 0.05 if ev.preferred_work_mode in {"hybrid", "flexible"} else 0.0
    return clamp(logistics)


def _behavioral_score(ev: CandidateEvidence) -> float:
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
    return clamp(behavioral)


def _trust_score(ev: CandidateEvidence) -> float:
    trust = 0.22 if ev.linkedin_connected else 0.0
    trust += 0.18 if ev.github_activity_score >= 40 else 0.10 if ev.github_activity_score >= 10 else 0.0
    trust += 0.18 if ev.saved_by_recruiters_30d >= 10 else 0.10 if ev.saved_by_recruiters_30d >= 4 else 0.0
    trust += 0.18 if ev.search_appearance_30d >= 150 else 0.10 if ev.search_appearance_30d >= 60 else 0.0
    trust += 0.14 if ev.offer_acceptance_rate >= 0.5 else 0.06 if ev.offer_acceptance_rate >= 0 else 0.0
    trust += 0.10 if ev.skill_assessment_max >= 70 else 0.0
    return clamp(trust)


def score_candidate(ev: CandidateEvidence, job: JobSpec) -> ScoreBreakdown:
    ai_search_role = job.category == "ai_ml_search_ranking"
    must_have_coverage = _term_coverage(ev.all_text, job.must_have)
    nice_to_have_coverage = _term_coverage(ev.all_text, job.nice_to_have)
    career_must_have_coverage = _term_coverage(ev.career_text, job.must_have)
    career_nice_to_have_coverage = _term_coverage(ev.career_text, job.nice_to_have)
    title_coverage = _term_coverage(ev.title_norm, (job.title,))
    disqualifier_coverage = _term_coverage(ev.all_text, job.disqualifiers)
    technical = 0.0
    if ai_search_role:
        technical += min(0.28, 0.07 * len(ev.career_retrieval_terms))
        technical += min(0.18, 0.045 * len(ev.vector_terms))
        technical += min(0.16, 0.04 * len(ev.eval_terms))
        technical += min(0.18, 0.045 * len(ev.career_production_terms))
        technical += min(0.12, 0.015 * len(ev.ml_terms))
        technical += 0.12 * must_have_coverage
        technical += 0.04 * nice_to_have_coverage
    else:
        technical += 0.48 * must_have_coverage
        technical += 0.24 * career_must_have_coverage
        technical += 0.12 * nice_to_have_coverage
        technical += 0.08 * career_nice_to_have_coverage
        technical += 0.08 if ev.career_production_terms else 0.0
    technical += 0.08 if ev.skill_assessment_max >= 70 else 0.04 if ev.skill_assessment_max >= 50 else 0.0
    technical = clamp(technical)

    career = 0.0
    if ai_search_role:
        career += 0.32 if ev.ai_title else 0.18 if ev.adjacent_title else 0.0
    else:
        career += 0.22 * title_coverage
        career += 0.24 * career_must_have_coverage
        career += 0.10 * career_nice_to_have_coverage
    career += 0.18 if ev.product_company_count else 0.0
    if ai_search_role:
        career += 0.16 if ev.career_retrieval_terms else 0.0
        career += 0.12 if ev.career_production_terms else 0.0
    else:
        career += 0.10 if ev.career_production_terms else 0.0
    career += 0.12 * career_must_have_coverage
    career += 0.04 * career_nice_to_have_coverage
    career += 0.10 if "hr" in ev.current_industry.lower() or "ai" in ev.current_industry.lower() or "software" in ev.current_industry.lower() else 0.0
    career -= 0.18 if ai_search_role and ev.non_tech_title and not ev.career_retrieval_terms else 0.0
    career -= 0.12 if ai_search_role and ev.service_only and not ev.product_company_count else 0.0
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
    if disqualifier_coverage >= 0.34 and must_have_coverage < 0.34:
        penalty += 0.06
    direct_career_evidence = bool(ev.career_retrieval_terms and (ev.career_production_terms or ev.eval_terms or ev.vector_terms))
    role_career_evidence = career_must_have_coverage >= 0.34 or (must_have_coverage >= 0.50 and career_must_have_coverage >= 0.20)
    top10_eligible = direct_career_evidence and not any(
        flag in flags
        for flag in {
            "non_tech_ai_keyword_stuffing",
            "ai_terms_without_career_evidence",
            "expert_skills_zero_duration",
            "shallow_ai_tool_interest",
        }
    )
    if not ai_search_role:
        top10_eligible = role_career_evidence and not any(
            flag in flags for flag in {"expert_skills_zero_duration", "stale_low_response"}
        )
    confidence = 0.0
    if ai_search_role:
        confidence += 0.30 if ev.career_retrieval_terms else 0.0
        confidence += 0.20 if ev.career_production_terms else 0.0
        confidence += 0.15 if ev.ai_title or ev.adjacent_title else 0.0
        confidence += 0.10 if ev.vector_terms else 0.0
        confidence += 0.10 if ev.eval_terms else 0.0
    else:
        confidence += 0.35 * career_must_have_coverage
        confidence += 0.20 * must_have_coverage
        confidence += 0.15 * title_coverage
        confidence += 0.15 if ev.career_production_terms else 0.0
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
    if ai_search_role and not ev.career_retrieval_terms and not ev.ai_title and ev.non_tech_title:
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
        engine="spine",
    )


def score_candidate_hybrid(
    ev: CandidateEvidence,
    job: JobSpec,
    *,
    match_result,                 # semantic_match.MatchResult
    schema_sig: dict,             # schema_profile.schema_signals output
    consistency,                  # consistency_audit.ConsistencyReport
) -> ScoreBreakdown:
    """Unified, JD-agnostic scoring path.

    technical_evidence and career_fit come from the JD's OWN requirements via the
    hybrid semantic match (not hardcoded keyword sets or category branches), so
    the same code scores an AI JD and a sales JD — only the parsed requirements
    differ. Behavioral/trust use the schema-driven signals (any schema), and the
    penalty layer combines the AI risk flags, the general consistency auditor,
    and semantic disqualifier hits. seniority/logistics reuse the spine helpers.
    """
    # Technical evidence is the semantic fit to must/nice requirements, nudged up
    # when the candidate's CAREER text (not just skills) carries the evidence.
    semantic_fit = float(match_result.semantic_fit)
    lexical_fit = float(match_result.lexical_fit)
    career_lexical = _term_coverage(ev.career_text, job.must_have)
    technical = clamp(0.80 * semantic_fit + 0.20 * lexical_fit)
    # Career fit rewards requirement coverage grounded in career history + product co.
    career = clamp(
        0.55 * match_result.coverage
        + 0.20 * career_lexical
        + 0.15 * semantic_fit
        + (0.10 if ev.product_company_count else 0.0)
    )

    seniority = _seniority_score(ev, job)
    logistics = _logistics_score(ev, job)

    # Behavioral/trust: schema-driven, blended with explicit-field spine scores so
    # the Redrob schema keeps its full fidelity while any schema still works.
    behavioral = clamp(0.34 * schema_sig.get("availability", 0.5)
                       + 0.33 * schema_sig.get("engagement", 0.5)
                       + 0.33 * _behavioral_score(ev))
    trust = clamp(0.5 * _trust_score(ev) + 0.5 * schema_sig.get("trust", 0.5))

    # Penalty: GENERAL signals only — the role-independent consistency auditor
    # plus semantic disqualifier hits derived from THIS JD's own disqualifier
    # requirements. The hybrid path deliberately does NOT use the AI-specific
    # risk_audit term/title lists, so it stays genuinely JD-agnostic (a sales or
    # design JD is scored with no AI-keyword assumptions).
    flags = list(consistency.codes)
    penalty = consistency.penalty
    disq_hits: tuple = ()
    if match_result.disqualifier_hit >= 0.5:
        penalty += 0.12 * match_result.disqualifier_hit
        disq_hits = tuple(m.req_text for m in match_result.requirement_matches
                          if m.kind == "disqualifier" and m.score >= 0.5)
        flags.append("semantic_disqualifier_overlap")

    # Low-relevance penalty: a candidate who genuinely doesn't match the role's
    # must-haves (low coverage AND low semantic fit) must not ride seniority +
    # behavioral defaults into a high rank. This separates clearly-irrelevant
    # candidates from real fits, which matters most on terse resumes where all the
    # other factors compress. Scaled so a borderline-adjacent candidate is nudged,
    # an off-role candidate is pushed firmly down.
    if match_result.coverage < 0.34 and semantic_fit < 0.30:
        penalty += 0.10 + 0.20 * (0.30 - semantic_fit)  # up to ~0.16
        flags.append("low_role_relevance")

    # Top matched must/nice requirements (grounded evidence for reasoning): the
    # best-scoring requirements with the candidate's actually-matched keywords.
    pos_matches = sorted(
        (m for m in match_result.requirement_matches
         if m.kind in {"must_have", "nice_to_have"} and m.score >= 0.30),
        key=lambda m: -m.score,
    )
    matched_requirements = tuple(
        (m.req_text, m.matched_keywords, getattr(m, "evidence_span", "")) for m in pos_matches[:4])
    concern_notes = tuple(c.detail for c in consistency.flags[:3])

    # Top-10 eligibility: real requirement coverage AND no internal impossibility.
    # Uses only the GENERAL consistency signals (role-independent), not AI-specific
    # flags, so eligibility means the same thing for any JD.
    top10_eligible = (
        match_result.coverage >= 0.34
        and not consistency.is_impossible
        and "semantic_disqualifier_overlap" not in flags
    )
    if not top10_eligible:
        penalty += 0.04

    confidence = clamp(
        0.40 * match_result.coverage
        + 0.25 * semantic_fit
        + 0.15 * (1.0 if career_lexical >= 0.34 else 0.0)
        + 0.10 * schema_sig.get("engagement", 0.5)
        + (0.10 if not flags else 0.0)
    )

    weights = job.weights
    raw = (
        weights["technical_evidence"] * technical
        + weights["career_fit"] * career
        + weights["seniority"] * seniority
        + weights["logistics"] * logistics
        + weights["behavioral"] * behavioral
        + weights["trust"] * trust
    )
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
        semantic_fit=round(semantic_fit, 6),
        lexical_fit=round(lexical_fit, 6),
        requirement_coverage=round(float(match_result.coverage), 6),
        disqualifier_hits=disq_hits,
        engine="hybrid",
        matched_requirements=matched_requirements,
        concern_notes=concern_notes,
    )

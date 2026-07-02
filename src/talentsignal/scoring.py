from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from .features import CandidateEvidence
from .jd_parser import JobSpec
from .risk_audit import risk_flags, risk_penalty


# Short but real tech skills that the generic ">=3 chars" filter would wrongly drop.
_SHORT_SKILLS = frozenset({
    "go", "r", "c", "ml", "ai", "js", "qa", "ux", "ui", "bi", "c#", "c++",
    ".net", "ci", "cd", "ab", "nlp", "llm",
})


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


@lru_cache(maxsize=4096)
def _tokenize(text: str) -> frozenset:
    """Whole-token set of a text, lowercased. Cached because the same JD term
    lists are tokenized for every candidate."""
    return frozenset(re.findall(r"[a-z0-9+#]+", text.lower()))


def _term_coverage(text: str, terms: tuple[str, ...]) -> float:
    """Graded coverage of `terms` by WHOLE TOKENS in `text`.

    Whole-token matching (not substring) eliminates the bug where 'ml' matched
    inside 'html'/'xml'. Each term contributes the FRACTION of its salient words
    that match, not a binary hit — so a multi-word requirement like "account
    management" is only fully covered when BOTH words appear, and "account" alone
    (e.g. inside "Accountant" on a Customer-Success JD) contributes ~0.5, not 1.0.
    This raises the bar for coincidental single-word overlaps that let off-role
    candidates leak in, while staying fully role-agnostic (no keyword lists).
    """
    if not terms:
        return 0.0
    tokens = _tokenize(text)
    total = 0.0
    for term in terms:
        # keep words >=3 chars, but also keep short, real tech tokens (go, r, c,
        # ml, ai, js, qa, c#, .net, c++) — dropping these erased real skills.
        words = [w for w in re.split(r"[\s/\-]+", term.lower())
                 if len(w) >= 3 or w in _SHORT_SKILLS]
        if not words:
            continue
        hits = sum(1 for w in words if w in tokens)
        if hits == 0:
            continue
        if len(words) == 1:
            total += 1.0                      # single-word term: binary
        elif hits >= 2 or hits / len(words) >= 0.6:
            total += 1.0                      # solid match: 2+ words or most of them
        else:
            total += 0.4                      # only 1 word of a multi-word term:
                                              # partial credit, can't fully "cover"
                                              # (stops coincidental single-word leaks)
    return total / len(terms)


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
    # Relevance-gate fields (council architecture): R = relevance to THIS JD's own
    # requirements (the dominant signal); Q = generic quality (seniority/logistics/
    # behavioral/trust). final = R^GAMMA * (Q_FLOOR + (1-Q_FLOOR)*Q) * soft * veto.
    role_relevance: float = 0.0
    general_quality: float = 0.0


# Relevance-gate constants (tuned once, role-agnostic — NOT per category).
# GAMMA super-linear so weak relevance is punished harder than rewarded; Q_FLOOR
# guarantees a perfectly-relevant candidate still scores meaningfully on generic
# signals alone. These make "matches THIS JD" dominate "is generically strong"
# for ANY role, by construction — no per-category code anywhere.
RELEVANCE_GAMMA = 1.1
QUALITY_FLOOR = 0.45


def _quality_blend(seniority: float, logistics: float, behavioral: float,
                   trust: float, weights: dict) -> float:
    """Generic quality Q in [0,1]: blend of ONLY the four generic factors,
    renormalized over them (technical/career never enter Q — they carry no
    independent score mass in the gated model)."""
    keys = ("seniority", "logistics", "behavioral", "trust")
    vals = {"seniority": seniority, "logistics": logistics,
            "behavioral": behavioral, "trust": trust}
    total = sum(float(weights.get(k, 0.0)) for k in keys) or 1.0
    return clamp(sum(float(weights.get(k, 0.0)) * vals[k] for k in keys) / total)


def _gate(relevance: float, quality: float, *, soft_multiplier: float = 1.0,
          hard_veto: float = 1.0) -> float:
    """The one JD-agnostic scoring law shared by both engines."""
    base = (clamp(relevance) ** RELEVANCE_GAMMA) * (QUALITY_FLOOR + (1.0 - QUALITY_FLOOR) * clamp(quality))
    return clamp(base) * clamp(soft_multiplier, 0.0, 1.0) * (1.0 if hard_veto else 0.0)


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


def _recency_factor(last_active_months: int) -> float:
    """How much to trust availability signals given profile freshness."""
    return (1.0 if last_active_months <= 1 else 0.75 if last_active_months <= 3
            else 0.35 if last_active_months <= 6 else 0.1)


def _open_to_work_term(ev: CandidateEvidence) -> float:
    """Recency-gated availability term in [0,1] (HR council decision).

    The self-declared open_to_work flag is a weak, noisy signal, so we interpret
    it THROUGH recency instead of trusting it flat:
      - open + recently active  -> ~1.0  (best case)
      - not-open + recently active -> ~0.35 (real but mild passive-candidate penalty)
      - either flag when STALE   -> decays toward 0.55 neutral (an old flag is not a
        promise in either direction; recency already penalizes staleness elsewhere)
      - flag MISSING/unknown     -> 0.55 neutral prior (unknown != unavailable)
    No availability signal ever vetoes a candidate."""
    rf = _recency_factor(ev.last_active_months)
    if ev.open_to_work is True:
        return 0.55 + 0.45 * rf
    if ev.open_to_work is False:
        return 0.55 - 0.20 * rf
    return 0.55  # unknown/unset -> neutral prior


def insufficient_evidence(ev: CandidateEvidence) -> bool:
    """True when a candidate carries essentially NO usable profile evidence — e.g. an
    off-schema record (wrong field names, missing profile) that the pipeline filled
    with defaults. Such a record must NOT be scored as a confident 'standout'; it
    should be flagged honestly so a naive integration doesn't get silent garbage."""
    text = (getattr(ev, "all_text", "") or "").strip()
    title = (ev.title or "").strip()
    return len(text) < 3 and not title and not ev.years


def _has_activity_data(ev: CandidateEvidence) -> bool:
    """True only when the candidate actually carries platform activity/response
    signals. A pasted/uploaded résumé has none — last_active defaults to the 999
    sentinel and response_rate to 0 — and we must NOT read that absence as 'stale'
    (unknown != inactive; that misleads and unfairly penalizes)."""
    return ev.last_active_months < 999 or ev.response_rate > 0.0


def reachability(ev: CandidateEvidence) -> tuple[str, float]:
    """A recruiter-facing reachability read, orthogonal to fit. Observed behavior
    (recent activity + response rate) dominates the self-declared flag.
    Returns (label, score in [0,1]) — display + within-band tiebreak only; this is
    a VIEW over signals already inside Q, not an extra penalty.

    When there is NO activity data at all (e.g. a résumé with no platform signals),
    returns an honest 'unknown' with a neutral score instead of a misleading 'stale'
    penalty. If the profile explicitly says open-to-work, that's surfaced too."""
    if not _has_activity_data(ev):
        # honest neutral read — we simply don't know reachability from a bare résumé
        if ev.open_to_work is True:
            return "reachable", 0.6   # self-declared open, no activity data to gate it
        return "unknown", 0.5
    rf = _recency_factor(ev.last_active_months)
    score = clamp(0.45 * rf + 0.35 * ev.response_rate + 0.20 * _open_to_work_term(ev))
    recent = ev.last_active_months <= 3
    responsive = ev.response_rate >= 0.4
    if recent or responsive:
        # active/responsive => reachable regardless of the flag; "passive" if not-open
        label = "passive" if ev.open_to_work is False else "reachable"
    elif ev.last_active_months >= 6 or ev.response_rate < 0.15:
        label = "stale"
    else:
        label = "passive"
    return label, round(score, 3)


def _behavioral_score(ev: CandidateEvidence) -> float:
    # No platform behavioral signals at all (e.g. a pasted/uploaded résumé)? Return a
    # NEUTRAL score rather than penalizing the candidate for data a résumé can't carry.
    # (unknown != unavailable — the same principle as the reachability read.)
    if not _has_activity_data(ev) and not ev.notice_period_days and ev.profile_completeness == 0:
        return 0.5
    response_time_score = clamp(1.0 - ev.response_time_hours / 240.0)
    notice_score = 1.0 if ev.notice_period_days <= 30 else 0.7 if ev.notice_period_days <= 60 else 0.35 if ev.notice_period_days <= 90 else 0.15
    active_score = _recency_factor(ev.last_active_months)
    # Council Change C: observed behavior (recency, response rate) weighted above the
    # self-declared flag. open_to_work 0.16->0.12, freed 0.04 to response+recency.
    behavioral = (
        0.18 * (ev.profile_completeness / 100.0)
        + 0.20 * active_score
        + 0.12 * _open_to_work_term(ev)
        + 0.20 * ev.response_rate
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

    # Same recency-gated availability treatment as the spine path (shared helper,
    # so both engines stay identical on availability scoring).
    behavioral = _behavioral_score(ev)

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
    weights = job.weights

    # ---- RELEVANCE GATE (council architecture; one law, no per-category code) ----
    # R = how well the candidate satisfies THIS JD's OWN parsed requirements.
    # Computed identically for every role (nurse, welder, AI engineer): must-have
    # coverage in career evidence first, then anywhere, plus a title-match credit.
    # A small nice-to-have credit rewards depth without lifting an off-role profile.
    relevance = max(
        career_must_have_coverage,
        0.85 * must_have_coverage,
        0.5 * title_coverage,
    )
    relevance = clamp(relevance + 0.10 * nice_to_have_coverage)
    if not job.must_have:
        # No parseable must-haves -> degrade gracefully to broad text coverage so we
        # still rank, rather than zeroing everyone.
        relevance = clamp(max(must_have_coverage, title_coverage,
                              0.5 * nice_to_have_coverage, 0.4))

    # Q = generic quality (ONLY seniority/logistics/behavioral/trust). Never carries
    # technical/career mass — those are display-only now.
    quality = _quality_blend(seniority, logistics, behavioral, trust, weights)

    # Penalties split into a hard veto (zeroes the score) and ONE soft multiplier.
    flags_set = set(flags)
    soft_penalty = risk_penalty(flags)
    if disqualifier_coverage >= 0.34 and must_have_coverage < 0.34:
        soft_penalty += 0.06
    hard_veto = 1.0
    try:
        from .consistency_audit import audit_candidate
        raw_record = getattr(ev, "_raw", None)
        consistency = audit_candidate(raw_record) if raw_record is not None else None
        if consistency is not None:
            if consistency.is_impossible:
                hard_veto = 0.0
            else:
                soft_penalty += consistency.penalty
            for code in consistency.codes:
                if code not in flags:
                    flags.append(code)
    except Exception:  # noqa: BLE001 - auditing must never break scoring
        consistency = None
    soft_multiplier = clamp(1.0 - soft_penalty, 0.6, 1.0)

    # Off-schema / empty record guard: a candidate with no usable evidence must not be
    # scored as a confident "standout". Flag it honestly and floor its relevance so it
    # sinks instead of silently ranking on default values.
    no_evidence = insufficient_evidence(ev)
    concern_notes: tuple = ()
    if no_evidence:
        relevance = 0.0
        flags = list(flags) + ["insufficient_evidence"]
        concern_notes = ("insufficient profile data to assess — the record has no usable "
                         "skills, career text, or title (check the input format)",)

    final = _gate(relevance, quality, soft_multiplier=soft_multiplier, hard_veto=hard_veto)

    # top-10 eligibility: must clear a minimum relevance and not be vetoed.
    top10_eligible = bool(hard_veto) and relevance >= 0.34 and not no_evidence
    # confidence tracks relevance + evidence depth (display/back-compat).
    confidence = 0.0 if no_evidence else clamp(
                       0.6 * relevance + 0.25 * career_must_have_coverage
                       + 0.10 * (1.0 if ev.career_production_terms else 0.0)
                       + 0.05 * (1.0 if not flags else 0.0))
    penalty = round(soft_penalty if hard_veto else 1.0, 6)
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
        concern_notes=concern_notes,
        engine="spine",
        role_relevance=round(relevance, 6),
        general_quality=round(quality, 6),
        requirement_coverage=round(must_have_coverage, 6),
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
    soft_penalty = consistency.penalty
    disq_hits: tuple = ()
    hard_veto = 1.0
    if match_result.disqualifier_hit >= 0.5:
        disq_hits = tuple(m.req_text for m in match_result.requirement_matches
                          if m.kind == "disqualifier" and m.score >= 0.5)
        flags.append("semantic_disqualifier_overlap")
        # A disqualifier match only HARD-vetoes when the candidate does NOT also meet
        # the role's core requirements. Someone who clearly covers the must-haves and
        # merely mentions a disqualifier term (e.g. "research AND shipped to
        # production" against a "no pure research" disqualifier) is a likely false
        # positive — downgrade to a strong soft penalty rather than deleting them.
        # Prevents losing genuinely strong candidates (measured: ~6/100k) to a
        # semantic keyword overlap; a clear disqualifier with weak coverage still zeroes.
        if match_result.coverage < 0.5:
            hard_veto = 0.0      # true disqualifier: no counter-evidence
        else:
            soft_penalty += 0.20  # keyword overlap despite strong fit -> heavy soft penalty
    if consistency.is_impossible:
        hard_veto = 0.0          # internally-impossible profile is a hard veto

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

    # ---- RELEVANCE GATE (same law as the spine path; one architecture) ----
    # R = relevance to THIS JD's OWN parsed requirements, using the GRADED semantic
    # must-fit (already a weighted aggregate of per-requirement scores) + coverage +
    # career-grounded lexical evidence. No category branch, no keyword lists.
    if job.must_have:
        relevance = clamp(
            0.55 * semantic_fit          # graded must/nice semantic aggregate
            + 0.30 * match_result.coverage  # fraction of must-haves genuinely matched
            + 0.15 * career_lexical       # exact-term evidence in career history
        )
    else:
        relevance = clamp(max(semantic_fit, 0.4))  # no must-haves -> graceful degrade
    # Q = generic quality (seniority/logistics/behavioral/trust ONLY).
    quality = _quality_blend(seniority, logistics, behavioral, trust, job.weights)
    soft_multiplier = clamp(1.0 - soft_penalty, 0.6, 1.0)

    # Off-schema / empty record guard (same as the spine path).
    no_evidence = insufficient_evidence(ev)
    if no_evidence:
        relevance = 0.0
        if "insufficient_evidence" not in flags:
            flags = list(flags) + ["insufficient_evidence"]
        concern_notes = (("insufficient profile data to assess — the record has no usable "
                          "skills, career text, or title (check the input format)",)
                         + tuple(concern_notes))[:3]

    final = _gate(relevance, quality, soft_multiplier=soft_multiplier, hard_veto=hard_veto)

    top10_eligible = bool(hard_veto) and relevance >= 0.34 and not no_evidence
    penalty = round(soft_penalty if hard_veto else 1.0, 6)
    confidence = 0.0 if no_evidence else clamp(
        0.50 * relevance
        + 0.20 * match_result.coverage
        + 0.15 * (1.0 if career_lexical >= 0.34 else 0.0)
        + 0.10 * schema_sig.get("engagement", 0.5)
        + (0.05 if not flags else 0.0)
    )
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
        role_relevance=round(relevance, 6),
        general_quality=round(quality, 6),
    )

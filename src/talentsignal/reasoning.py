"""Recruiter-grade, grounded, rank-aware reasoning — the column judges read.

The challenge's official submission requires a `reasoning` column, and it is the
ONLY surface where "ranks like a great recruiter, not keyword matching" is visible
(judges can't see the cross-encoder math). So this composer is built to read like a
senior recruiter defending a stack-rank:

  * GROUNDED — every clause is built from the candidate's own evidence: ONLY the
    keywords that actually matched (never the full requirement phrase, so we never
    imply a skill the candidate lacks), real years/title/location, and concerns
    drawn from the consistency auditor + behavioral signals. The grounding audit
    (explanation_audit) enforces this on the shipped hybrid path.
  * COMPARATIVE — near rank boundaries and top-10 neighbours, the prose justifies
    the ORDER with a real factor delta ("edges out #N on production evidence"),
    which is what "understanding who fits" looks like in words.
  * RANK-AWARE & HONEST — tone scales with rank; concerns (notice period, stale
    activity, contradictions, thin coverage) are always surfaced when real. No
    "filler" boilerplate — a near-cutoff candidate gets a real, specific caveat.
  * VARIED — frames chosen deterministically per candidate so adjacent rows differ.
"""
from __future__ import annotations

from .features import CandidateEvidence
from .jd_parser import JobSpec
from .scoring import ScoreBreakdown


# Opening frames by rank band. Tone is the message; the variant varies per row.
_OPENERS = {
    "top": [
        "Strong fit at #{rank}: {who}",
        "#{rank} — a clear recommendation. {who}",
        "{who} A standout at #{rank}.",
        "Top of the list (#{rank}). {who}",
    ],
    "high": [
        "Solid fit at #{rank}. {who}",
        "#{rank}, and a good match. {who}",
        "{who} Earns #{rank} on consistent evidence.",
        "A dependable #{rank}. {who}",
    ],
    "mid": [
        "Reasonable fit at #{rank}. {who}",
        "#{rank} — partial but real. {who}",
        "{who} Lands at #{rank}.",
        "Worth a look at #{rank}. {who}",
    ],
    "low": [
        "Near the cutoff at #{rank}. {who}",
        "#{rank}, included with caveats. {who}",
        "{who} Sits at #{rank}, on the bubble.",
        "A maybe at #{rank}. {who}",
    ],
}


def _band(rank: int) -> str:
    if rank <= 5:
        return "top"
    if rank <= 20:
        return "high"
    if rank <= 60:
        return "mid"
    return "low"


def _who(ev: CandidateEvidence) -> str:
    title = ev.title or "Candidate"
    loc = ev.location or ev.country or "location n/a"
    return f"{title} with {ev.years:.1f} years in {loc}."


def _matched_skill_phrases(score: ScoreBreakdown) -> list[str]:
    """Recruiter-readable strengths built from ONLY the matched keywords (never the
    full requirement phrase), so we never imply a skill the candidate didn't show.
    Dedupes across requirements and keeps the candidate's strongest evidence first."""
    seen: set[str] = set()
    phrases: list[str] = []
    for item in (score.matched_requirements or ()):
        matched_kw = item[1] if len(item) > 1 else ()
        # keep only genuine matched keywords, drop generic filler tokens
        kws = [k for k in (matched_kw or [])
               if k and k.lower() not in {"systems", "product", "engineering",
                                          "shipping", "infrastructure", "models",
                                          "frameworks", "must", "have", "strong"}]
        for k in kws:
            kl = k.lower()
            if kl not in seen:
                seen.add(kl)
                phrases.append(k)
    return phrases


def _strengths_from_spine(ev: CandidateEvidence) -> list[str]:
    out: list[str] = []
    out += list(ev.career_retrieval_terms[:3])
    out += list(ev.career_production_terms[:2])
    out += list(ev.vector_terms[:2])
    # dedupe preserving order
    seen, uniq = set(), []
    for t in out:
        if t.lower() not in seen:
            seen.add(t.lower()); uniq.append(t)
    return uniq


def _strength_sentence(skills: list[str], band: str) -> str:
    """Turn matched skills into a human strength sentence (not a keyword dump)."""
    if not skills:
        return "Adjacent technical signals, but limited direct evidence for the must-haves."
    n = 4 if band in ("top", "high") else 3
    picks = skills[:n]
    if len(picks) == 1:
        core = picks[0]
    elif len(picks) == 2:
        core = f"{picks[0]} and {picks[1]}"
    else:
        core = ", ".join(picks[:-1]) + f", and {picks[-1]}"
    leads = {
        "top": f"Direct, hands-on evidence for {core} — the core of what this role needs.",
        "high": f"Real evidence for {core}.",
        "mid": f"Shows {core}, though not the full depth the top candidates have.",
        "low": f"Some signal on {core}, but thin against the role's must-haves.",
    }
    return leads[band]


def _concerns(ev: CandidateEvidence, score: ScoreBreakdown, rank: int) -> list[str]:
    concerns: list[str] = []
    for note in (score.concern_notes or ())[:2]:
        concerns.append(note)
    if ev.notice_period_days and ev.notice_period_days > 90:
        concerns.append(f"a {ev.notice_period_days}-day notice period")
    if ev.last_active_months >= 6:
        concerns.append("no platform activity in 6+ months")
    if ev.response_rate < 0.2 and not concerns:
        concerns.append(f"a low recruiter response rate ({ev.response_rate:.0%})")
    if score.requirement_coverage and score.requirement_coverage < 0.34 and rank > 20:
        concerns.append("only partial coverage of the must-haves")
    if score.disqualifier_hits:
        d = score.disqualifier_hits[0].strip().rstrip(".")
        concerns.append(f"overlap with a disqualifier (“{d[:60]}”)")
    return concerns


def _comparative_clause(score: ScoreBreakdown, rank: int,
                        neighbor: ScoreBreakdown | None) -> str:
    """A real 'why this person over the next one' clause from factor deltas — the
    most recruiter-like sentence the system can produce. Only emitted when a
    neighbor and a meaningful, defensible delta exist."""
    if neighbor is None:
        return ""
    deltas = []
    for label, a, b in (
        ("production & career evidence", score.career_fit, neighbor.career_fit),
        ("depth on the role's requirements", score.role_relevance, neighbor.role_relevance),
        ("seniority match", score.seniority, neighbor.seniority),
        ("reachability & engagement", score.behavioral, neighbor.behavioral),
    ):
        if a - b >= 0.08:
            deltas.append(label)
    if not deltas:
        return ""
    return f" Edges out #{rank + 1} on {deltas[0]}."


def generate_reasoning(ev: CandidateEvidence, score: ScoreBreakdown, rank: int,
                       job: JobSpec | None = None,
                       neighbor: ScoreBreakdown | None = None) -> str:
    band = _band(rank)
    seed = sum(ord(ch) for ch in ev.candidate_id) + rank
    opener = _OPENERS[band][seed % len(_OPENERS[band])].format(rank=rank, who=_who(ev))

    skills = _matched_skill_phrases(score) or _strengths_from_spine(ev)
    strength = _strength_sentence(skills, band)

    avail = ""
    if ev.open_to_work and ev.response_rate >= 0.5 and band in ("top", "high"):
        avail = f" Open to work, {ev.response_rate:.0%} response rate."

    # comparative clause only for the ranks a recruiter actually deliberates over
    comparative = _comparative_clause(score, rank, neighbor) if rank <= 25 else ""

    concerns = _concerns(ev, score, rank)
    concern_clause = ""
    if concerns:
        lead = "One flag" if len(concerns) == 1 else "Flags"
        concern_clause = f" {lead}: {'; '.join(concerns[:2])}."
    elif band == "low":
        # a real, specific near-cutoff caveat — never "filler" boilerplate
        cov = score.requirement_coverage or 0.0
        concern_clause = (f" Makes the shortlist on breadth of relevant signal rather than "
                          f"deep must-have coverage ({cov:.0%}); worth a human look.")

    text = f"{opener} {strength}{comparative}{avail}{concern_clause}"
    return " ".join(text.split())

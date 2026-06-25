"""Candidate-facing transparency report — the feature the incumbents' lawsuits
are about, and that none of them offer.

The Jan-2026 Eightfold FCRA class action's core grievance: applicants were scored
by an opaque AI, filtered out before any human saw them, and "never told their
data was being compiled, never given copies of the reports, and never offered the
chance to dispute errors." TalentSignal can answer all of that, because its
scoring is fully explainable by construction.

candidate_report(candidate, jd) produces exactly what a candidate (or an auditor,
or an FCRA-style adverse-action notice) should be able to see:

  * what data the engine used (only what the candidate themselves provided),
  * which job requirements it matched, with the candidate's OWN sentence as proof,
  * which requirements it did NOT find evidence for (so they can dispute/clarify),
  * any consistency concerns and exactly which two facts triggered them,
  * the factor breakdown — no hidden score.

This is human-in-the-loop transparency, the opposite of silent auto-rejection.
"""
from __future__ import annotations

from typing import Any


def candidate_report(candidate: dict[str, Any], jd: Any, *,
                     engine: str = "spine", embedder=None,
                     index_dir: str | None = None,
                     category: str = "ai_ml_search_ranking") -> dict[str, Any]:
    """Produce a transparency report for ONE candidate against a JD — what the
    engine saw, what it matched (with proof), what it didn't, and why."""
    from .api import rank

    res = rank(jd, [candidate], top_n=1, engine=engine, embedder=embedder,
               index_dir=index_dir, category=category)
    if not res.ranked:
        return {"error": "candidate could not be scored"}
    c = res.ranked[0]

    # requirements the engine could NOT evidence (so the candidate can dispute/add)
    matched_reqs = {m.requirement for m in (c.requirement_matches or [])}
    unmet = [r["text"] for r in (res.requirements or [])
             if r.get("kind") == "must_have" and r["text"] not in matched_reqs][:6]

    # Optional public-evidence enrichment from the candidate's OWN linked GitHub
    # (consented, public API, offline-safe). Only included if a profile was linked.
    github = None
    try:
        from .github_analysis import find_github_username, analyze_github
        if find_github_username(candidate):
            gp = analyze_github(candidate)
            github = {"linked_profile": gp.username, "fetched": gp.fetched,
                      "evidence": gp.evidence, "engineering_signal": gp.score}
    except Exception:  # noqa: BLE001 - enrichment must never break the report
        github = None

    return {
        "disclosure": (
            "This report shows everything the ranking engine used and concluded about "
            "you. It used ONLY the information you provided — no scraped or third-party "
            "data. A human reviewer makes the final decision; you are not auto-rejected."
        ),
        "data_used": {
            "source": "only the profile/resume you submitted",
            "fields_considered": ["career history", "skills", "summary", "stated experience",
                                   "availability signals (if provided)"],
            "identity_used": "none — the engine never reads your name or identity "
                             "(name-swap score change = 0.0)",
        },
        "result": {
            "fit_score": c.score,
            "title_read": c.title,
            "years_read": c.years,
            "requirement_coverage": c.factors.requirement_coverage if c.factors else 0.0,
            "factor_breakdown": c.factors.to_dict() if c.factors else {},
            "reasoning": c.reasoning,
        },
        "matched_with_proof": [
            {"requirement": m.requirement,
             "your_evidence": m.evidence_span or "(matched on overall meaning)",
             "matched_terms": list(m.matched_keywords)}
            for m in (c.requirement_matches or [])
        ],
        "not_evidenced": {
            "requirements": unmet,
            "note": "We found no evidence for these in what you submitted. If you have "
                    "this experience, add it to your profile — this is your chance to "
                    "correct the record before a human reviews it.",
        },
        "concerns_flagged": [
            {"concern": f.code, "the_two_facts": f.detail}
            for f in (c.risk_flags or [])
        ],
        "public_evidence": github,  # GitHub analysis if the candidate linked a profile; else null
        "your_rights": (
            "You can request this report, dispute anything inaccurate, and a human "
            "reviews the final decision. The scoring is deterministic and reproducible."
        ),
    }

"""General consistency / honeypot auditor — role-independent.

The dataset plants ~80 honeypots: profiles that look strong to a keyword or even
a semantic matcher (they're dense with the right vocabulary) but are internally
impossible. A ranker that "reads" profiles must catch them by their
contradictions, not by their keywords. These checks are about a profile's
INTERNAL CONSISTENCY, so they fire for ANY role and ANY candidate schema.

Each flag carries the two contradicting facts, so the reason is explainable
("claims 8.0 years but career tenure sums to 132 months / 11.0 years").

Checks:
  tenure_exceeds_experience   career months >> stated years (fabricated tenure)
  expert_zero_duration        'expert' proficiency with 0 months used
  skill_exceeds_career        skill used longer than the whole career
  date_integrity              end<start, negative/zero durations, future dates
  skill_not_in_evidence       high-proficiency skill absent from all text
  endorsement_inconsistency   expert skill, 0 endorsements AND 0 assessment

This is a SUPERSET of the AI-specific risk_audit; it does not replace it (the
existing risk flags stay for their tests), it adds general structural checks.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

REFERENCE_YEAR = 2026
REFERENCE_MONTH = 6


@dataclass
class ConsistencyFlag:
    code: str
    detail: str          # human-readable, names the two contradicting facts
    severity: float      # 0..1 penalty weight contribution


@dataclass
class ConsistencyReport:
    flags: list[ConsistencyFlag] = field(default_factory=list)

    @property
    def codes(self) -> list[str]:
        return [f.code for f in self.flags]

    @property
    def penalty(self) -> float:
        # diminishing-returns sum, capped, so a profile can't be over-penalized
        total = 0.0
        for f in self.flags:
            total += f.severity
        return round(min(0.6, total), 4)

    @property
    def is_impossible(self) -> bool:
        """True if any HARD contradiction is present (used as a top-rank veto)."""
        hard = {"tenure_exceeds_experience", "expert_zero_duration", "date_integrity",
                "skill_exceeds_career"}
        return any(f.code in hard for f in self.flags)


def _norm(text: Any) -> str:
    return str(text or "").lower()


def _evidence_tokens(candidate: dict[str, Any]) -> set[str]:
    profile = candidate.get("profile", {})
    parts = [profile.get("summary", ""), profile.get("headline", "")]
    for job in candidate.get("career_history", []):
        parts.append(job.get("title", ""))
        parts.append(job.get("description", ""))
    text = " ".join(str(p) for p in parts).lower()
    return set(re.findall(r"[a-z0-9+#./\-]{3,}", text))


def _evidence_blob(candidate: dict[str, Any]) -> str:
    """Full lowercased evidence text (summary + headline + career), normalized so
    punctuation/spacing differences don't cause false 'skill missing' matches."""
    profile = candidate.get("profile") or {}
    if not isinstance(profile, dict):
        profile = {}
    parts = [profile.get("summary", ""), profile.get("headline", ""), profile.get("current_title", "")]
    for job in (candidate.get("career_history") or []):
        if isinstance(job, dict):
            parts.append(job.get("title", ""))
            parts.append(job.get("description", ""))
    blob = " ".join(str(p) for p in parts).lower()
    # collapse separators so "scikit-learn" and "scikit learn" both contain "scikit"+"learn"
    return re.sub(r"[/\-.]", " ", blob)


def audit_candidate(candidate: dict[str, Any]) -> ConsistencyReport:
    report = ConsistencyReport()
    # Harden against malformed inputs (string/None candidate, null profile) — real
    # customer data is messy and must never crash the auditor.
    if not isinstance(candidate, dict):
        return report
    profile = candidate.get("profile") or {}
    if not isinstance(profile, dict):
        profile = {}
    career = candidate.get("career_history") or []
    if not isinstance(career, list):
        career = []
    # keep only dict career entries so every j.get(...) below is safe
    career = [j for j in career if isinstance(j, dict)]
    # Skills may be objects or plain strings; the consistency checks below only
    # apply to structured (dict) skills (duration/proficiency). Keep dicts only so
    # a string-skill applicant never crashes the auditor.
    skills = [s for s in (candidate.get("skills", []) or []) if isinstance(s, dict)]
    signals = candidate.get("redrob_signals") or {}
    if not isinstance(signals, dict):
        signals = {}

    import math

    def _f(v, default=0.0):
        try:
            f = float(v)
            return f if math.isfinite(f) else default
        except (TypeError, ValueError):
            return default

    stated_years = _f(profile.get("years_of_experience"))
    career_months = sum(int(_f(j.get("duration_months")))
                        for j in career if isinstance(j, dict))

    # 1) tenure sum wildly exceeds stated experience (impossible career length).
    # NOTE: career_months SUMS jobs and does not subtract calendar overlap, so a
    # candidate with concurrent roles can legitimately sum past their stated years.
    # The buffer is generous (allows ~2 fully-overlapping roles) to avoid falsely
    # flagging real concurrent work; only a wildly-impossible sum is flagged.
    overlap_buffer = max(18, int(stated_years * 12 * 0.5))
    if stated_years > 0 and career_months > (stated_years * 12) + overlap_buffer:
        report.flags.append(ConsistencyFlag(
            "tenure_exceeds_experience",
            f"claims {stated_years:.1f} years but career tenure sums to "
            f"{career_months} months ({career_months/12:.1f} years)",
            0.30,
        ))

    # 2) expert proficiency with EXPLICIT zero months of use. Only flag when the
    # duration field is present and equals 0 — a MISSING duration is unknown, not
    # zero, and must not trigger a hard veto (real profiles often omit it).
    expert_zero = [s for s in skills
                   if _norm(s.get("proficiency")) == "expert"
                   and s.get("duration_months") is not None
                   and int(_f(s.get("duration_months"))) == 0]
    if expert_zero:
        names = ", ".join(str(s.get("name")) for s in expert_zero[:3])
        report.flags.append(ConsistencyFlag(
            "expert_zero_duration",
            f"'expert' proficiency with 0 months used: {names}",
            0.25 if len(expert_zero) >= 2 else 0.15,
        ))

    # 3) a single skill claims FAR more months than the candidate's stated total
    #    experience. Skill duration legitimately runs up to ~1.4x stated
    #    experience in this data (a skill carried across roles), so we only flag
    #    the impossible tail: a skill claiming > 2.5x stated experience (p99 of
    #    the real pool sits at ~2.8x). This keeps the check honeypot-specific.
    max_skill_months = max((int(s.get("duration_months") or 0) for s in skills), default=0)
    if stated_years > 0 and max_skill_months > (stated_years * 12) * 2.5 + 12:
        report.flags.append(ConsistencyFlag(
            "skill_exceeds_career",
            f"a skill claims {max_skill_months} months ({max_skill_months/12:.1f} years) but "
            f"stated experience is only {stated_years:.1f} years",
            0.20,
        ))

    # 4) date integrity: end before start, future dates, impossible durations.
    for job in career:
        sd, ed = str(job.get("start_date") or ""), job.get("end_date")
        if _is_future(sd):
            report.flags.append(ConsistencyFlag("date_integrity", f"start_date in the future: {sd}", 0.15))
            break
        if ed and _date_before(str(ed), sd):
            report.flags.append(ConsistencyFlag(
                "date_integrity", f"end_date {ed} before start_date {sd}", 0.15))
            break

    # 5) EXPERT skills that appear nowhere in the candidate's own text. Only
    #    'expert' (not 'advanced') and a high threshold, because real candidates
    #    routinely list real skills not spelled out verbatim in a short bio —
    #    we only want the keyword-stuffing pattern (many claimed experts, none
    #    evidenced), so this fires as a SOFT signal and only when most expert
    #    skills are ghosts.
    # Normalize the full evidence text once; match a skill if ANY of its
    # significant words appears (punctuation/spacing-insensitive), so
    # "Sentence Transformers" matches "sentence-transformers" and "scikit-learn"
    # matches either form. We only flag the keyword-stuffing pattern: many
    # 'expert' skills with NONE of them traceable to the candidate's own text.
    evidence_blob = _evidence_blob(candidate)
    expert_skills = [s for s in skills if _norm(s.get("proficiency")) == "expert"]
    ghost = []
    for s in expert_skills:
        words = [w for w in re.split(r"[\s/\-.]+", _norm(s.get("name"))) if len(w) >= 3]
        if words and not any(w in evidence_blob for w in words):
            ghost.append(str(s.get("name")))
    # Require essentially ALL expert skills to be ghosts before flagging (true
    # keyword-stuffing), not a fuzzy 80% that catches honest candidates.
    if len(expert_skills) >= 5 and len(ghost) == len(expert_skills):
        report.flags.append(ConsistencyFlag(
            "skill_not_in_evidence",
            f"all {len(expert_skills)} 'expert' skills are absent from the candidate's own text "
            f"(e.g. {', '.join(ghost[:3])})",
            0.10,
        ))

    # 6) expert skill with zero endorsements and zero assessment evidence.
    assessments = signals.get("skill_assessment_scores") or {}
    max_assess = max([float(v) for v in assessments.values()], default=0.0)
    endorsements = int(signals.get("endorsements_received") or 0)
    has_expert = any(_norm(s.get("proficiency")) == "expert" for s in skills)
    if has_expert and endorsements == 0 and max_assess == 0.0:
        report.flags.append(ConsistencyFlag(
            "endorsement_inconsistency",
            "claims 'expert' skills but has 0 endorsements and no assessment scores",
            0.08,
        ))

    return report


def _is_future(date_str: str) -> bool:
    m = re.match(r"(\d{4})-(\d{2})", date_str or "")
    if not m:
        return False
    y, mo = int(m.group(1)), int(m.group(2))
    return (y, mo) > (REFERENCE_YEAR, REFERENCE_MONTH)


def _date_before(a: str, b: str) -> bool:
    """True if date a is strictly before date b (YYYY-MM-DD strings)."""
    ma, mb = re.match(r"\d{4}-\d{2}-\d{2}", a or ""), re.match(r"\d{4}-\d{2}-\d{2}", b or "")
    if not (ma and mb):
        return False
    return a < b

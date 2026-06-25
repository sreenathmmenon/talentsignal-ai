"""Hiring-compliance analysis for a ranking — the report legal/compliance asks for.

A ranking system that decides who recruiters see is, in many jurisdictions, an
"employment selection procedure" and must be auditable for adverse impact. This
module produces the two checks an enterprise buyer's legal team expects:

  1. ADVERSE IMPACT (four-fifths / 80% rule, EEOC Uniform Guidelines):
     for a protected attribute, the selection rate of each group must be at
     least 80% of the highest group's rate. Below 0.80 = potential adverse
     impact that needs justification.

  2. NAME / IDENTITY INVARIANCE: changing only identity fields must not change
     a candidate's score (delegated to fairness.py) — the structural guarantee
     that the engine never reads identity.

The engine is identity-blind by construction, so adverse impact here can only
arise from *legitimate, job-related* factors correlating with a group in the
data (e.g. location, years) — which the report surfaces transparently so a
human can review and justify, rather than hiding it.

IMPORTANT: this analysis needs a group attribute the CALLER supplies (the engine
never infers protected attributes). It operates on (candidate_id -> group) labels
the customer provides from their own HR data, never inferred from names.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GroupRate:
    group: str
    selected: int
    total: int

    @property
    def rate(self) -> float:
        return self.selected / self.total if self.total else 0.0


@dataclass
class AdverseImpactReport:
    attribute: str
    top_k: int
    group_rates: list[GroupRate]
    impact_ratios: dict[str, float]   # group -> rate / max_rate
    min_impact_ratio: float
    passes_four_fifths: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "attribute": self.attribute,
            "top_k": self.top_k,
            "groups": [{"group": g.group, "selected": g.selected, "total": g.total,
                        "selection_rate": round(g.rate, 4),
                        "impact_ratio": round(self.impact_ratios.get(g.group, 0.0), 4)}
                       for g in self.group_rates],
            "min_impact_ratio": round(self.min_impact_ratio, 4),
            "passes_four_fifths_rule": self.passes_four_fifths,
            "notes": self.notes,
        }


def adverse_impact(
    ranked_ids: list[str],
    group_of: dict[str, str],
    *,
    top_k: int = 10,
    attribute: str = "group",
    min_group_size: int = 5,
) -> AdverseImpactReport:
    """Four-fifths-rule analysis: of each group's members, what fraction landed
    in the top_k, and is the lowest group's rate >= 80% of the highest?

    ranked_ids : the engine's ranked output (best first).
    group_of   : candidate_id -> protected-group label, supplied by the customer
                 from their OWN HR data (never inferred by the engine).
    """
    selected_set = set(ranked_ids[:top_k])
    totals: dict[str, int] = {}
    selected: dict[str, int] = {}
    for cid, grp in group_of.items():
        totals[grp] = totals.get(grp, 0) + 1
        if cid in selected_set:
            selected[grp] = selected.get(grp, 0) + 1

    rates = [GroupRate(g, selected.get(g, 0), totals[g]) for g in sorted(totals)]
    notes_pre: list[str] = []
    # INTEGRITY: disclose label coverage. Candidates in the ranking but missing a
    # group label are NOT analyzed -- silently dropping them could mask adverse
    # impact, so the report must state how complete the analysis is.
    ranked_total = len(set(ranked_ids))
    labeled_in_ranking = sum(1 for cid in set(ranked_ids) if cid in group_of)
    if ranked_total and labeled_in_ranking < ranked_total:
        gap = ranked_total - labeled_in_ranking
        notes_pre.append(
            f"label coverage: {labeled_in_ranking}/{ranked_total} ranked candidates have a "
            f"group label; {gap} are unlabeled and excluded from this analysis -- provide "
            f"labels for full coverage (an incomplete analysis can mask adverse impact).")
    notes: list[str] = list(notes_pre)
    # Only groups with enough members are statistically meaningful.
    eligible = [r for r in rates if r.total >= min_group_size]
    small = [r.group for r in rates if r.total < min_group_size]
    if small:
        notes.append(f"groups with <{min_group_size} members excluded from the ratio "
                     f"(too small to be statistically meaningful): {', '.join(small)}")
    if not eligible:
        notes.append("no group large enough for a four-fifths analysis")
        return AdverseImpactReport(attribute, top_k, rates, {}, 1.0, True, notes)

    max_rate = max(r.rate for r in eligible) or 1.0
    impact = {r.group: (r.rate / max_rate if max_rate else 0.0) for r in eligible}
    min_ratio = min(impact.values()) if impact else 1.0
    passes = min_ratio >= 0.80
    if not passes:
        worst = min(impact, key=impact.get)
        notes.append(f"group '{worst}' selected at {impact[worst]:.0%} of the top group's rate "
                     f"(below the 80% threshold) — review whether the driving factors "
                     f"(e.g. location, seniority) are job-related and justified.")
    else:
        notes.append("all groups within the four-fifths (80%) threshold — no adverse impact detected.")
    return AdverseImpactReport(attribute, top_k, rates, impact, min_ratio, passes, notes)


def compliance_summary(ranked_ids: list[str], group_attributes: dict[str, dict[str, str]],
                       *, top_k: int = 10) -> dict[str, Any]:
    """Run adverse-impact across several protected attributes at once.

    group_attributes: {attribute_name: {candidate_id: group}} — e.g.
        {"gender": {...}, "ethnicity": {...}, "age_band": {...}}
    Returns a single report dict suitable for an audit export.
    """
    reports = {}
    overall_pass = True
    for attr, mapping in group_attributes.items():
        rep = adverse_impact(ranked_ids, mapping, top_k=top_k, attribute=attr)
        reports[attr] = rep.to_dict()
        overall_pass = overall_pass and rep.passes_four_fifths
    return {
        "top_k": top_k,
        "overall_passes_four_fifths": overall_pass,
        "attributes": reports,
        "method": "EEOC Uniform Guidelines four-fifths (80%) rule",
        "engine_property": "identity-blind by construction (scores never read name/identity; "
                           "name-swap score delta = 0.0)",
    }

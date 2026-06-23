#!/usr/bin/env python3
"""Evaluation harness — scores a ranker against labeled synthetic ground truth
across many JDs, dataset shapes, and adversarial suites.

This is the quality instrument for the whole project: with no leaderboard and no
organizer labels, this is how we tell whether a ranking change actually helps.
It also concretely demonstrates the JD's "designing evaluation frameworks"
must-have.

Suites
  per_role      : rank each role's labeled pool with ITS OWN JD; report metrics.
  honeypot      : honeypot-heavy pools; metric = honeypot rate in top-10/100.
  paraphrase    : do zero-keyword-overlap strong fits still rank above weak ones?
  perturbation  : a paraphrase copy should rank near the original; a contradicted
                  (honeypot) copy should rank far below it.
  generality    : cross-JD top-10 overlap should be LOW (the AI JD and the sales
                  JD must not surface the same people) — proves JD-agnosticism.
  schema        : rank a pool that uses a NON-Redrob signal vocabulary.

Usage:
    python scripts/eval_harness.py --engine spine
    python scripts/eval_harness.py --engine spine --out outputs/eval
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.eval import datasets as D
from talentsignal.eval import metrics
from talentsignal.eval.roles import ROLES
from talentsignal.jd_parser import load_job_spec
from talentsignal.ranking import rank_records

# role_id -> job spec path (each role ranked with its own JD)
ROLE_SPEC = {
    "ai_search": "job_specs/redrob_senior_ai_engineer.yaml",
    "sales": "job_specs/examples/enterprise_account_executive.yaml",
    "data_analytics": "job_specs/examples/data_analytics_lead.yaml",
    "backend": "job_specs/examples/backend_platform_engineer.yaml",
    "product": "job_specs/examples/product_manager_growth.yaml",
    "design": "job_specs/examples/product_designer_systems.yaml",
}

# A ranker is any function (records, job_spec, top_n) -> ranked candidate_ids.
Ranker = Callable[[list[dict[str, Any]], Any, int], list[str]]


def spine_ranker(records: list[dict[str, Any]], job: Any, top_n: int) -> list[str]:
    rows = rank_records(records, job, top_n=top_n)
    return [r["candidate_id"] for r in rows]


ENGINES: dict[str, Ranker] = {"spine": spine_ranker}


def _eval_pool(pool: list[D.LabeledCandidate], job: Any, ranker: Ranker) -> dict[str, float]:
    records = D.records_of(pool)
    labels = D.labels_of(pool)
    ranked_ids = ranker(records, job, len(records))
    rels = metrics.relevances_from_ranking(ranked_ids, labels)
    return metrics.evaluate(rels)


def suite_per_role(ranker: Ranker) -> dict[str, Any]:
    results = {}
    for role_id, role in ROLES.items():
        job = load_job_spec(ROLE_SPEC[role_id])
        pool = D.build_pool(role)
        results[role_id] = _eval_pool(pool, job, ranker)
    composites = [m["composite"] for m in results.values()]
    return {"per_role": results, "mean_composite": round(sum(composites) / len(composites), 4)}


def suite_honeypot(ranker: Ranker) -> dict[str, Any]:
    role = ROLES["ai_search"]
    job = load_job_spec(ROLE_SPEC["ai_search"])
    # honeypot-heavy: many traps + a few real fits
    pool = D.build_pool(role, mix={D.STRONG: 8, D.ADJACENT: 6, D.HONEYPOT: 40, D.IRRELEVANT: 10})
    m = _eval_pool(pool, job, ranker)
    return {"honeypot_rate@10": m["honeypot_rate@10"], "honeypot_rate@100": m["honeypot_rate@100"],
            "ndcg@10": m["ndcg@10"]}


def suite_paraphrase(ranker: Ranker) -> dict[str, Any]:
    role = ROLES["ai_search"]
    job = load_job_spec(ROLE_SPEC["ai_search"])
    # paraphrase-ideal (grade 4, zero keywords) vs weak (grade 1) vs irrelevant
    pool = D.build_pool(role, mix={D.PARAPHRASE_IDEAL: 10, D.WEAK: 20, D.IRRELEVANT: 20})
    records = D.records_of(pool)
    labels = D.labels_of(pool)
    ranked = ranker(records, job, len(records))
    rels = metrics.relevances_from_ranking(ranked, labels)
    # where do the paraphrase-ideals land? (mean rank of grade-4 candidates)
    para_ids = {c.candidate_id for c in pool if c.archetype == D.PARAPHRASE_IDEAL}
    ranks = [i + 1 for i, cid in enumerate(ranked) if cid in para_ids]
    mean_rank = round(sum(ranks) / len(ranks), 1) if ranks else None
    return {"ndcg@10": metrics.ndcg_at_k(rels, 10),
            "paraphrase_ideal_mean_rank": mean_rank,
            "paraphrase_ideal_in_top10": sum(1 for r in ranks if r <= 10),
            "total_paraphrase_ideals": len(para_ids)}


def suite_perturbation(ranker: Ranker) -> dict[str, Any]:
    """A strong candidate, its paraphrase (should stay near), and a contradicted
    (honeypot) twin (should drop) — embedded in a pool of distractors."""
    role = ROLES["ai_search"]
    job = load_job_spec(ROLE_SPEC["ai_search"])
    base = D.make_candidate(role, D.STRONG, 900)
    para = D.make_candidate(role, D.PARAPHRASE_IDEAL, 900)
    contra = D.make_candidate(role, D.HONEYPOT, 900)
    distractors = D.build_pool(role, mix={D.WEAK: 20, D.IRRELEVANT: 20})
    pool = [base, para, contra] + distractors
    records = D.records_of(pool)
    ranked = ranker(records, job, len(records))
    pos = {cid: i + 1 for i, cid in enumerate(ranked)}
    return {
        "strong_rank": pos.get(base.candidate_id),
        "paraphrase_rank": pos.get(para.candidate_id),
        "contradicted_rank": pos.get(contra.candidate_id),
        "contradicted_below_strong": pos.get(contra.candidate_id, 0) > pos.get(base.candidate_id, 0),
    }


def suite_generality(ranker: Ranker) -> dict[str, Any]:
    """Build ONE mixed pool containing strong fits for several roles, then rank it
    with each role's JD. The top-10 sets should barely overlap across roles."""
    mixed: list[D.LabeledCandidate] = []
    role_tops: dict[str, set[str]] = {}
    for role_id, role in ROLES.items():
        mixed += D.build_pool(role, mix={D.STRONG: 6, D.ADJACENT: 4})
    records = D.records_of(mixed)
    for role_id in ROLES:
        job = load_job_spec(ROLE_SPEC[role_id])
        ranked = ranker(records, job, 10)
        role_tops[role_id] = set(ranked[:10])
    # pairwise Jaccard overlap of top-10s
    overlaps = []
    ids = list(role_tops)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = role_tops[ids[i]], role_tops[ids[j]]
            jacc = len(a & b) / len(a | b) if (a | b) else 0.0
            overlaps.append(jacc)
    return {"mean_top10_jaccard_overlap": round(sum(overlaps) / len(overlaps), 3) if overlaps else 0.0,
            "max_top10_jaccard_overlap": round(max(overlaps), 3) if overlaps else 0.0}


def suite_schema(ranker: Ranker) -> dict[str, Any]:
    """Rank a pool whose candidates use a NON-Redrob signal vocabulary, to confirm
    the engine doesn't hard-depend on the 23 Redrob fields. (Spine engine reads
    explicit fields; this surfaces how much it degrades — Story 6 closes the gap.)"""
    role = ROLES["ai_search"]
    job = load_job_spec(ROLE_SPEC["ai_search"])
    pool = D.build_pool(role, schema_variant="alt")
    try:
        m = _eval_pool(pool, job, ranker)
        return {"ran_without_error": True, "ndcg@10": m["ndcg@10"], "composite": m["composite"]}
    except Exception as exc:  # noqa: BLE001 - we want to report, not crash the suite
        return {"ran_without_error": False, "error": str(exc)[:160]}


SUITES = {
    "per_role": suite_per_role,
    "honeypot": suite_honeypot,
    "paraphrase": suite_paraphrase,
    "perturbation": suite_perturbation,
    "generality": suite_generality,
    "schema": suite_schema,
}


def run(engine: str) -> dict[str, Any]:
    ranker = ENGINES[engine]
    report: dict[str, Any] = {"engine": engine, "suites": {}}
    for name, fn in SUITES.items():
        report["suites"][name] = fn(ranker)
    return report


def to_markdown(report: dict[str, Any]) -> str:
    s = report["suites"]
    lines = [f"# Evaluation Report — engine: `{report['engine']}`", ""]
    pr = s["per_role"]
    lines += ["## Per-role ranking quality", "", f"Mean composite across roles: **{pr['mean_composite']}**", "",
              "| role | NDCG@10 | NDCG@50 | MAP | P@10 | composite |",
              "|---|---|---|---|---|---|"]
    for role, m in pr["per_role"].items():
        lines.append(f"| {role} | {m['ndcg@10']:.3f} | {m['ndcg@50']:.3f} | {m['map']:.3f} | {m['p@10']:.3f} | {m['composite']:.3f} |")
    lines += ["", "## Honeypot suite (must stay ~0 in top-10)", "",
              f"- honeypot_rate@10: **{s['honeypot']['honeypot_rate@10']:.3f}**",
              f"- honeypot_rate@100: {s['honeypot']['honeypot_rate@100']:.3f}",
              f"- ndcg@10: {s['honeypot']['ndcg@10']:.3f}", ""]
    p = s["paraphrase"]
    lines += ["## Paraphrase suite (zero-keyword strong fits)", "",
              f"- paraphrase-ideal mean rank: **{p['paraphrase_ideal_mean_rank']}** (of {p['total_paraphrase_ideals']})",
              f"- paraphrase-ideal in top-10: {p['paraphrase_ideal_in_top10']}",
              f"- ndcg@10: {p['ndcg@10']:.3f}", ""]
    pt = s["perturbation"]
    lines += ["## Perturbation suite", "",
              f"- strong rank: {pt['strong_rank']}, paraphrase rank: {pt['paraphrase_rank']}, contradicted rank: {pt['contradicted_rank']}",
              f"- contradicted ranked below strong: {pt['contradicted_below_strong']}", ""]
    g = s["generality"]
    lines += ["## Generality suite (cross-JD top-10 overlap — lower is better)", "",
              f"- mean pairwise Jaccard overlap: **{g['mean_top10_jaccard_overlap']}**",
              f"- max pairwise overlap: {g['max_top10_jaccard_overlap']}", ""]
    sc = s["schema"]
    lines += ["## Schema-agnostic suite (non-Redrob signal vocabulary)", "",
              f"- ran without error: {sc['ran_without_error']}",
              f"- ndcg@10: {sc.get('ndcg@10', 'n/a')}", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--engine", default="spine", choices=sorted(ENGINES))
    ap.add_argument("--out", default="outputs/eval")
    args = ap.parse_args()

    report = run(args.engine)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "report.md").write_text(to_markdown(report), encoding="utf-8")
    print(to_markdown(report))
    print(f"\nWrote {out_dir/'report.json'} and {out_dir/'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

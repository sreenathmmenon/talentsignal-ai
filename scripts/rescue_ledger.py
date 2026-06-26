#!/usr/bin/env python3
"""Rescue ledger — the brief's thesis, proven on the organizers' own 100K.

"Recruiters miss the right person because keyword filters can't see what matters."
This script ranks the full candidate pool two ways — our engine vs a credible
keyword-only baseline — and lists the candidates the KEYWORD filter buries
(keyword_rank > KEYWORD_CUTOFF) that OUR engine surfaces into the top OUR_TOP, each
with the candidate's own evidence sentence and the requirement they match by
MEANING despite low keyword overlap. Every rescued candidate must have passed the
consistency/honeypot auditor — we never rescue a fabricated profile.

    python scripts/rescue_ledger.py --candidates <jsonl> [--engine hybrid] \
        --out outputs/rescue_ledger.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.jd_parser import load_job_spec
from talentsignal.io import iter_candidates
from talentsignal.baseline_ranker import keyword_rank
from talentsignal.api import rank as engine_rank
from talentsignal.consistency_audit import audit_candidate


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--job-spec", default="job_specs/redrob_senior_ai_engineer.yaml")
    ap.add_argument("--engine", default="hybrid", choices=["spine", "hybrid"])
    ap.add_argument("--index-dir", default="outputs/index")
    ap.add_argument("--our-top", type=int, default=100)
    ap.add_argument("--keyword-cutoff", type=int, default=100)
    ap.add_argument("--out", default="outputs/rescue_ledger.csv")
    args = ap.parse_args()

    job = load_job_spec(args.job_spec)
    records = list(iter_candidates(args.candidates))
    by_id = {c["candidate_id"]: c for c in records}

    # 1) keyword baseline over the whole pool
    kw_rank = keyword_rank(records, job)

    # 2) our engine — top OUR_TOP (hybrid uses the precomputed index)
    idx = args.index_dir if args.engine == "hybrid" else None
    res = engine_rank(job, records, top_n=args.our_top, engine=args.engine,
                      index_dir=idx, category=job.category)

    rescued = []
    for c in res.ranked:
        kr = kw_rank.get(c.candidate_id, len(records))
        if kr > args.keyword_cutoff:  # keyword filter would bury them
            cand = by_id.get(c.candidate_id, {})
            if audit_candidate(cand).is_impossible:
                continue  # never rescue a fabricated profile
            # the evidence span + the requirement matched by meaning
            span, req = "", ""
            for m in (c.requirement_matches or []):
                if getattr(m, "evidence_span", ""):
                    span = m.evidence_span
                    req = m.requirement
                    break
            rescued.append({
                "candidate_id": c.candidate_id,
                "our_rank": c.rank,
                "keyword_rank": kr,
                "title": c.title,
                "matched_requirement": (req or "")[:80],
                "their_own_words": (span or "")[:200],
            })

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["candidate_id", "our_rank", "keyword_rank",
                                          "title", "matched_requirement", "their_own_words"])
        w.writeheader()
        w.writerows(rescued)

    # headline stats for the deck: how blind is a keyword filter to our shortlist?
    import json
    kr_of_ours = [kw_rank.get(c.candidate_id, len(records)) for c in res.ranked]
    below_50 = sum(1 for k in kr_of_ours if k > 50)
    below_100 = sum(1 for k in kr_of_ours if k > 100)
    summary = {
        "jd": job.title,
        "pool_size": len(records),
        "our_shortlist": len(res.ranked),
        "keyword_ranks_below_50": below_50,
        "keyword_ranks_below_100": below_100,
        "headline": (f"Of the {len(res.ranked)} candidates we shortlist, a keyword filter "
                     f"ranks {below_100} outside its own top 100 — a recruiter relying on "
                     f"keyword search would never see {below_100}% of who we recommend."),
        "rescued_with_proof": rescued[:25],
    }
    Path("outputs/rescue_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(summary["headline"])
    print(f"  ({below_50} of our {len(res.ranked)} also fall below keyword-rank #50.)")
    print(f"\nSample rescues (strong people keyword search buries, with their own words):")
    for r in rescued[:6]:
        print(f"  we #{r['our_rank']} / keyword #{r['keyword_rank']}: {r['title']} — "
              f"\"{r['their_own_words'][:80]}\"")
    print(f"\nWrote {args.out} and outputs/rescue_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

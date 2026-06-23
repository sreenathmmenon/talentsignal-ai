#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from talentsignal.jd_parser import load_job_spec
from talentsignal.ranking import (
    _rows_from_scored,
    rank_candidates,
    score_pool_hybrid,
    write_evidence_packets,
    write_factor_scores,
    write_risk_report,
    write_risk_summary,
    write_submission,
)
from talentsignal.io import iter_candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank candidates for a job description.")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl or candidates.jsonl.gz")
    parser.add_argument("--out", required=True, help="Output submission CSV path")
    parser.add_argument("--job-spec", default="job_specs/redrob_senior_ai_engineer.yaml")
    parser.add_argument("--factor-scores", default="outputs/factor_scores.csv")
    parser.add_argument("--evidence-packets", default="outputs/evidence_packets.jsonl")
    parser.add_argument("--risk-report", default="outputs/risk_report.csv")
    parser.add_argument("--risk-summary", default="outputs/risk_summary.json")
    parser.add_argument("--engine", default="spine", choices=["spine", "hybrid"],
                        help="spine = structured ranker (no deps); hybrid = + precomputed semantic index")
    parser.add_argument("--index-dir", default="outputs/index",
                        help="precomputed embedding index dir (hybrid engine)")
    args = parser.parse_args()

    start = time.perf_counter()
    job = load_job_spec(args.job_spec)
    if args.engine == "hybrid":
        # Hybrid loads the precomputed numpy index (built offline by precompute.py);
        # it never imports sentence-transformers at rank time. Falls back to
        # lexical-only inside score_pool_hybrid if the index is absent.
        scored = score_pool_hybrid(iter_candidates(args.candidates), job, index_dir=args.index_dir)
        rows = _rows_from_scored(scored, job, 100)
    else:
        rows = rank_candidates(args.candidates, job, top_n=100)
    write_submission(rows, args.out)
    write_factor_scores(rows, args.factor_scores)
    write_evidence_packets(rows, args.evidence_packets)
    write_risk_report(rows, args.risk_report)
    write_risk_summary(rows, args.risk_summary)
    elapsed = time.perf_counter() - start
    print(f"Wrote {args.out} with {len(rows)} rows in {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

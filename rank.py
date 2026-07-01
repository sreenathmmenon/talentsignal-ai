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
    rank_records,
    score_pool_hybrid,
    write_evidence_packets,
    write_factor_scores,
    write_risk_report,
    write_risk_summary,
    write_submission,
)
from talentsignal.io import iter_candidates


def rank_candidates_rows(records, job, top_n=100):
    """Rank in-memory records (spine) -> the row dicts the writers expect."""
    return rank_records(records, job, top_n=top_n)


def _rerank_rows(rows, records, job):
    """Cross-encoder rerank of already-scored rows, in place of the facade (so the
    writers keep their _score/_evidence rows). Offline-safe: rows unchanged if the
    model can't load."""
    try:
        from talentsignal import reranker
        if not reranker.available():
            print("[rerank] cross-encoder unavailable; using retrieval order")
            return rows
        by_id = {c["candidate_id"]: c for c in records}
        jd_text = job.title + ". " + " ".join(r.text for r in (getattr(job, "requirements", ()) or ()))
        head = rows[:60]
        pairs, idx = [], []
        for i, row in enumerate(head):
            cand = by_id.get(row["candidate_id"])
            if cand is not None:
                pairs.append((jd_text, reranker._evidence_text(cand)))
                idx.append(i)
        if not pairs:
            return rows
        scores = reranker._load().predict(pairs, batch_size=64, show_progress_bar=False)
        lo, hi = float(min(scores)), float(max(scores))
        span = (hi - lo) or 1.0
        # blended display score = 0.5 retrieval + 0.5 normalized cross-encoder, so
        # the score column stays MONOTONIC with the new rerank order (the official
        # validator requires non-increasing scores).
        blended = []
        for i, ce in zip(idx, scores):
            ce_norm = (float(ce) - lo) / span
            base = float(head[i]["score"])
            blended.append((i, 0.5 * base + 0.5 * ce_norm))
        blended.sort(key=lambda x: -x[1])
        reranked_head = []
        for new_pos, (i, new_score) in enumerate(blended):
            row = head[i]
            # force strictly non-increasing scores after rounding
            row["score"] = f"{max(0.0, new_score - new_pos * 0.000001):.6f}"
            reranked_head.append(row)
        tail = rows[60:]
        # keep the tail strictly below the reranked head's last score
        floor = float(reranked_head[-1]["score"]) if reranked_head else 0.0
        for j, row in enumerate(tail):
            row["score"] = f"{max(0.0, floor - (j + 1) * 0.000001):.6f}"
        return reranked_head + tail
    except Exception as exc:  # noqa: BLE001 - rerank must never break ranking
        print(f"[rerank] skipped ({exc}); using retrieval order")
        return rows


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
    parser.add_argument("--rerank", action="store_true",
                        help="apply the cross-encoder rerank stage to the shortlist "
                             "(higher accuracy on vocabulary-overlapping roles; needs "
                             "the offline cross-encoder model)")
    parser.add_argument("--allow-lexical-fallback", action="store_true",
                        help="permit the hybrid engine to run lexical-only when the "
                             "embedding index is missing (produces a DIFFERENT ranking, "
                             "not the submitted CSV; off by default so reproductions fail loudly)")
    args = parser.parse_args()

    start = time.perf_counter()
    job = load_job_spec(args.job_spec)
    records = list(iter_candidates(args.candidates))
    # Stage 1 — retrieve. When reranking, retrieve a larger shortlist first.
    retrieve_n = 100 if not args.rerank else max(100, 60)
    if args.engine == "hybrid":
        # Hybrid loads the precomputed numpy index (built offline by precompute.py);
        # it never imports sentence-transformers at rank time.
        #
        # REPRODUCIBILITY GUARD: the submitted CSV is the hybrid engine's output, so
        # a reproduction MUST use the real index. If the index is missing or is an
        # un-pulled Git-LFS pointer, hybrid would silently degrade to a lexical-only
        # ranking and emit a valid-but-DIFFERENT top-100 — a Stage-3 reproduction
        # failure that looks like success. We fail loudly instead. Pass
        # --allow-lexical-fallback to opt into the degraded path intentionally.
        from talentsignal import artifacts
        id_to_row, _emb, _meta = artifacts.load_candidate_index(args.index_dir)
        if id_to_row is None and not args.allow_lexical_fallback:
            print(
                f"ERROR: hybrid engine requested but no usable embedding index was found "
                f"at '{args.index_dir}'.\n"
                f"  - If you just cloned the repo, run:  git lfs install && git lfs pull\n"
                f"  - To build it from scratch, run:      python3 precompute.py\n"
                f"  - To rank WITHOUT semantics anyway:   add --allow-lexical-fallback "
                f"(produces a different, spine-like ranking — NOT the submitted CSV).",
                file=sys.stderr,
            )
            return 2
        scored = score_pool_hybrid(records, job, index_dir=args.index_dir)
        rows = _rows_from_scored(scored, job, retrieve_n)
    else:
        rows = rank_candidates_rows(records, job, top_n=retrieve_n)

    # Stage 2 — optional cross-encoder rerank of the retrieved rows (the same model
    # the product UI uses). Reorders the shortlist by (JD, candidate) pair scoring;
    # offline-safe (no model -> rows unchanged). Then cut to the final 100.
    if args.rerank:
        rows = _rerank_rows(rows, records, job)
    rows = rows[:100]
    for i, r in enumerate(rows, 1):  # re-number ranks after rerank/cut
        r["rank"] = i
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

#!/usr/bin/env python3
"""Self-contained demo / sandbox entrypoint.

Drop in ANY job description (free-text .md/.txt or structured .yaml) and ANY
candidate file (.jsonl), and get a ranked, explainable shortlist as CSV — the
"this is a product, not a one-JD script" demonstration and the hackathon sandbox.

Works on a small sample within the compute budget. With the embedding model
available it uses the hybrid engine (live-embeds the sample); otherwise it
degrades to the spine engine — either way it produces a valid ranking.

Usage:
    python scripts/demo_rank.py --jd demo/data/sales_jd.md \
        --candidates demo/data/sales_candidates.jsonl --engine hybrid --top-n 10
    python scripts/demo_rank.py --jd job_specs/redrob_senior_ai_engineer.yaml \
        --candidates demo/data/ai_search_candidates.jsonl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal import artifacts
from talentsignal.io import iter_candidates
from talentsignal.jd_parser import load_job_spec, job_spec_from_jd_text
from talentsignal.ranking import (
    _rows_from_scored, rank_records, score_pool_hybrid, write_submission,
)


def build_job(jd_path: str, category: str):
    p = Path(jd_path)
    if p.suffix in {".yaml", ".yml"}:
        return load_job_spec(p)
    return job_spec_from_jd_text(p.read_text(encoding="utf-8"),
                                 job_id=p.stem, category=category)


def hybrid_rows(records, job, top_n):
    try:
        import os
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        texts = [artifacts.evidence_text_of(c) for c in records]
        ids = [c["candidate_id"] for c in records]
        emb = model.encode(texts, batch_size=128, convert_to_numpy=True, normalize_embeddings=True)
        req_texts = [r.text for r in getattr(job, "requirements", ()) or ()]
        req_emb = model.encode(req_texts, convert_to_numpy=True, normalize_embeddings=True) if req_texts else None
        scored = score_pool_hybrid(records, job, candidate_embeddings=({c: i for i, c in enumerate(ids)}, emb),
                                   req_embeddings=req_emb)
        return _rows_from_scored(scored, job, top_n)
    except Exception as exc:  # noqa: BLE001
        print(f"(embedding model unavailable: {exc}; falling back to lexical-only hybrid)")
        scored = score_pool_hybrid(records, job)
        return _rows_from_scored(scored, job, top_n)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jd", required=True, help="JD file: free-text .md/.txt or structured .yaml")
    ap.add_argument("--candidates", required=True, help="candidate .jsonl file")
    ap.add_argument("--engine", default="hybrid", choices=["spine", "hybrid"])
    ap.add_argument("--category", default="ai_ml_search_ranking")
    ap.add_argument("--top-n", type=int, default=10)
    ap.add_argument("--out", default="outputs/demo_submission.csv")
    args = ap.parse_args()

    job = build_job(args.jd, args.category)
    records = list(iter_candidates(args.candidates))
    print(f"JD: {job.title} ({len(job.requirements)} requirements) | candidates: {len(records)} | engine: {args.engine}")

    if args.engine == "hybrid":
        rows = hybrid_rows(records, job, args.top_n)
    else:
        rows = rank_records(records, job, top_n=args.top_n)

    write_submission(rows, args.out)
    by_id = {c["candidate_id"]: c for c in records}
    print(f"\nTop {min(args.top_n, len(rows))} shortlist:\n")
    for r in rows[: args.top_n]:
        title = by_id[r["candidate_id"]]["profile"].get("current_title", "")
        print(f"  #{r['rank']:>2} {r['candidate_id']}  [{title}]")
        print(f"      {r['reasoning']}")
    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

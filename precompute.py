#!/usr/bin/env python3
"""Offline precompute — build the semantic index for the hybrid ranker.

This is the ONLY entry point that loads sentence-transformers. It runs OFFLINE
and is allowed to exceed the 5-minute ranking budget (the challenge explicitly
permits precomputation). It embeds every candidate's evidence text and each JD's
requirement texts, then persists float32 matrices via artifacts.py. At rank time
nothing here is imported — rank.py loads only the numpy arrays.

Determinism / reproducibility:
  * model is pinned (all-MiniLM-L6-v2 by default)
  * single-thread, eval mode, vectors L2-normalized
  * offline flags set so no network call is attempted

Usage:
    python precompute.py --candidates <candidates.jsonl> [--job-spec ...] [--index-dir outputs/index]
    python precompute.py --candidates demo/data/ai_search_candidates.jsonl --job-spec job_specs/redrob_senior_ai_engineer.yaml
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Force offline so a missing/blocked network can never turn into a silent hang.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

sys.path.insert(0, str(Path(__file__).parent / "src"))

from talentsignal import artifacts
from talentsignal.io import iter_candidates
from talentsignal.jd_parser import load_job_spec, job_spec_from_jd_text

DEFAULT_MODEL = "all-MiniLM-L6-v2"


def _load_model(model_name: str):
    import numpy as np  # noqa: F401  (ensure numpy present)
    import torch
    from sentence_transformers import SentenceTransformer

    torch.set_num_threads(max(1, (os.cpu_count() or 2)))
    model = SentenceTransformer(model_name, device="cpu")
    model.eval()
    return model


def embed_candidates(candidates_path: str, model, batch_size: int, index_dir: str) -> int:
    ids: list[str] = []
    texts: list[str] = []
    for cand in iter_candidates(candidates_path):
        ids.append(str(cand["candidate_id"]))
        texts.append(artifacts.evidence_text_of(cand))
    t0 = time.perf_counter()
    vectors = model.encode(texts, batch_size=batch_size, show_progress_bar=True,
                           convert_to_numpy=True, normalize_embeddings=True)
    artifacts.save_candidate_index(ids, vectors, model._first_module().auto_model.config._name_or_path
                                   if hasattr(model, "_first_module") else DEFAULT_MODEL, index_dir)
    print(f"Embedded {len(ids)} candidates in {time.perf_counter()-t0:.1f}s -> {index_dir}")
    return len(ids)


def embed_requirements(job, model, index_dir: str) -> int:
    reqs = list(getattr(job, "requirements", ()) or ())
    if not reqs:
        print(f"Job {job.id} has no structured requirements; skipping requirement embeddings.")
        return 0
    texts = [r.text for r in reqs]
    vectors = model.encode(texts, batch_size=64, convert_to_numpy=True, normalize_embeddings=True)
    out = artifacts.save_requirement_embeddings(job.id, vectors, index_dir)
    print(f"Embedded {len(reqs)} requirements for job '{job.id}' -> {out}")
    return len(reqs)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--job-spec", help="YAML scorecard whose requirements to embed")
    ap.add_argument("--jd-text", help="free-text JD file whose requirements to embed")
    ap.add_argument("--job-id", default="ingested_jd", help="id used when --jd-text is given")
    ap.add_argument("--category", default="ai_ml_search_ranking")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--index-dir", default=artifacts.DEFAULT_INDEX_DIR)
    args = ap.parse_args()

    model = _load_model(args.model)
    embed_candidates(args.candidates, model, args.batch_size, args.index_dir)

    if args.job_spec:
        embed_requirements(load_job_spec(args.job_spec), model, args.index_dir)
    if args.jd_text:
        text = Path(args.jd_text).read_text(encoding="utf-8")
        job = job_spec_from_jd_text(text, job_id=args.job_id, category=args.category)
        embed_requirements(job, model, args.index_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

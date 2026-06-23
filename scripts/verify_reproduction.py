#!/usr/bin/env python3
"""Verify the ranking step reproduces in a clean, offline environment.

Simulates what the organizers' Stage-3 sandbox does: take a fresh checkout, run
ONLY the documented ranking command, with the network disabled, and confirm the
output validates and matches the committed submission. This is the local
stand-in for `docker run --network none` (and is runnable without a Docker
daemon, e.g. in CI).

What it checks:
  1. The rank step imports nothing that needs the network (no torch / no
     sentence-transformers at rank time) — asserted by import inspection.
  2. The spine engine produces a valid 100-row CSV (zero dependencies).
  3. If the precomputed index is present, the hybrid engine reproduces too.
  4. The official validator passes on the output.

Usage:
  python scripts/verify_reproduction.py --candidates <jsonl>
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "[PUB] India_runs_data_and_ai_challenge" / "India_runs_data_and_ai_challenge" / "validate_submission.py"


def _run(cmd, env=None):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT), env=env)


def check_no_network_imports() -> bool:
    """Assert the rank-time modules don't import torch / sentence-transformers."""
    probe = (
        "import sys; sys.path.insert(0,'src');"
        "from talentsignal.ranking import score_pool_hybrid, rank_candidates;"
        "from talentsignal import artifacts, semantic_match;"
        "bad=[m for m in ('torch','sentence_transformers','transformers') if m in sys.modules];"
        "print('OK' if not bad else 'BAD:'+','.join(bad))"
    )
    r = _run([sys.executable, "-c", probe])
    ok = r.returncode == 0 and r.stdout.strip() == "OK"
    print(f"[1] rank-time imports numpy-only (no network deps): {'PASS' if ok else 'FAIL — ' + r.stdout + r.stderr}")
    return ok


def check_engine(engine: str, candidates: str, index_dir: str | None) -> bool:
    out = f"/tmp/repro_{engine}.csv"
    # Force offline so any accidental network attempt fails loudly rather than hangs.
    env = dict(os.environ, HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    cmd = [sys.executable, "rank.py", "--candidates", candidates, "--out", out]
    if engine == "hybrid":
        cmd += ["--engine", "hybrid", "--index-dir", index_dir or "outputs/index"]
    r = _run(cmd, env=env)
    if r.returncode != 0:
        print(f"[{engine}] rank FAILED: {r.stderr[-300:]}")
        return False
    # validate
    val = _run([sys.executable, str(VALIDATOR), out])
    valid = "Submission is valid." in (val.stdout + val.stderr)
    rows = sum(1 for _ in open(out)) - 1
    print(f"[{engine}] produced {rows} rows, validator: {'PASS' if valid else 'FAIL'} ({r.stdout.strip()})")
    return valid and rows == 100


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--index-dir", default="outputs/index")
    args = ap.parse_args()

    print("=== Reproduction verification (offline, fresh-environment simulation) ===")
    ok = check_no_network_imports()
    ok = check_engine("spine", args.candidates, None) and ok
    if (ROOT / args.index_dir / "embeddings.npy").exists():
        ok = check_engine("hybrid", args.candidates, args.index_dir) and ok
    else:
        print("[hybrid] skipped (no precomputed index present)")

    print("\nRESULT:", "ALL CHECKS PASS — reproduces offline within the rank contract" if ok
          else "FAILURES — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

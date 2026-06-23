#!/usr/bin/env python3
"""Synthetic Data & JD Factory.

Writes schema-valid candidate datasets (.jsonl) and their job descriptions (both
free-text .md and structured .yaml) to disk, so:
  * the demo has realistic content beyond the challenge dataset,
  * we can export varied datasets (many roles, many shapes) to prove generality,
  * the free-text JD ingestion path has real inputs to parse.

IMPORTANT: this NEVER touches the challenge candidates.jsonl. All output goes to
eval/data/ (for evaluation) and demo/data/ (for the demo), clearly separated and
never submitted.

Usage:
    python scripts/generate_datasets.py                # default: all roles -> demo/data
    python scripts/generate_datasets.py --out eval/data --roles ai_search sales
    python scripts/generate_datasets.py --schema alt   # non-Redrob signal vocabulary
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.eval import datasets as D
from talentsignal.eval.jd_library import JDS
from talentsignal.eval.roles import ROLES

# A compact demo-friendly mix (<=100 candidates so it fits the sandbox budget).
DEMO_MIX = {
    D.STRONG: 6,
    D.PARAPHRASE_IDEAL: 5,
    D.ADJACENT: 8,
    D.WEAK: 12,
    D.IRRELEVANT: 15,
    D.HONEYPOT: 6,
    D.BEHAVIORAL_TWIN: 3,
}


def write_role(role_id: str, out_dir: Path, schema_variant: str, mix: dict) -> dict:
    role = ROLES[role_id]
    jd = JDS[role_id]
    pool = D.build_pool(role, mix=mix, schema_variant=schema_variant)

    # candidates.jsonl (records only — labels withheld, as a ranker would see)
    cand_path = out_dir / f"{role_id}_candidates.jsonl"
    with cand_path.open("w", encoding="utf-8") as fh:
        for cand in pool:
            fh.write(json.dumps(cand.record, ensure_ascii=False) + "\n")

    # labels.json (ground truth, for the eval harness / scoring our own ranking)
    labels_path = out_dir / f"{role_id}_labels.json"
    labels_path.write_text(
        json.dumps({c.candidate_id: {"grade": c.grade, "archetype": c.archetype} for c in pool}, indent=2),
        encoding="utf-8",
    )

    # job_description.md (free text) — the input for JD ingestion / the demo
    jd_md = out_dir / f"{role_id}_jd.md"
    jd_md.write_text(jd.text, encoding="utf-8")

    return {
        "role_id": role_id,
        "title": jd.title,
        "candidates": str(cand_path),
        "labels": str(labels_path),
        "jd_text": str(jd_md),
        "jd_spec": jd.spec_path,
        "count": len(pool),
        "schema_variant": schema_variant,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="demo/data")
    ap.add_argument("--roles", nargs="*", default=sorted(ROLES), choices=sorted(ROLES))
    ap.add_argument("--schema", default="redrob", choices=["redrob", "alt"])
    ap.add_argument("--full", action="store_true", help="use the larger eval mix instead of the compact demo mix")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    mix = D.DEFAULT_MIX if args.full else DEMO_MIX

    manifest = [write_role(r, out_dir, args.schema, mix) for r in args.roles]
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote {len(manifest)} role datasets to {out_dir}/ (schema={args.schema}):")
    for m in manifest:
        print(f"  {m['role_id']:16s} {m['count']:3d} candidates -> {Path(m['candidates']).name}, {Path(m['jd_text']).name}")
    print(f"Manifest: {out_dir/'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

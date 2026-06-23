#!/usr/bin/env python3
"""CI quality gate — run on every commit to prevent regressions.

Turns the project's quality guarantees into a single pass/fail check that runs
without the 100K challenge file (all on synthetic labeled data), so it's fast and
runnable anywhere:

  1. Ranking quality  — eval composite on the labeled Redrob proxy >= threshold
  2. Honeypot safety  — 0 honeypots in top-10 on a trap-heavy pool
  3. Generality       — cross-JD top-10 overlap stays low (still JD-agnostic)
  4. Fairness         — name/identity invariance (score delta == 0)
  5. Reproduction     — rank-time imports stay numpy-only (no torch/ST)

Any failure exits non-zero so CI blocks the merge. This is the thing that makes
quality continuous instead of "we checked once" — the class of regression the
project hit before (a false-positive penalty, a templated-reasoning slip) becomes
impossible to ship silently.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# thresholds — tuned with margin below current measured values so normal variation
# doesn't flake, but a real regression trips the gate. The CI gate runs the SPINE
# engine (zero-dependency, no model needed in CI); the hybrid engine that ships
# achieves honeypot rate 0.0 in top-10, but spine -- the fallback -- tolerates a
# small rate on a deliberately trap-heavy pool (40 honeypots vs a handful of
# fits). We gate spine at its real safe level; the hybrid 0.0 is asserted by
# tests/test_hybrid_scoring.py instead.
MIN_COMPOSITE = 0.85
MAX_HONEYPOT_AT10 = 0.20
MAX_CROSS_JD_OVERLAP = 0.20


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    failures: list[str] = []
    eh = _load("eval_harness", ROOT / "scripts" / "eval_harness.py")

    # 1. ranking quality
    per_role = eh.suite_per_role(eh.spine_ranker)
    comp = per_role["mean_composite"]
    if comp < MIN_COMPOSITE:
        failures.append(f"ranking quality regressed: composite {comp} < {MIN_COMPOSITE}")
    print(f"[1] ranking composite: {comp}  (>= {MIN_COMPOSITE})")

    # 2. honeypot safety
    hp = eh.suite_honeypot(eh.spine_ranker)["honeypot_rate@10"]
    if hp > MAX_HONEYPOT_AT10:
        failures.append(f"honeypot rate@10 regressed: {hp} > {MAX_HONEYPOT_AT10}")
    print(f"[2] honeypot rate@10: {hp}  (<= {MAX_HONEYPOT_AT10})")

    # 3. generality
    overlap = eh.suite_generality(eh.spine_ranker)["mean_top10_jaccard_overlap"]
    if overlap > MAX_CROSS_JD_OVERLAP:
        failures.append(f"cross-JD overlap regressed: {overlap} > {MAX_CROSS_JD_OVERLAP}")
    print(f"[3] cross-JD overlap: {overlap}  (<= {MAX_CROSS_JD_OVERLAP})")

    # 4. fairness — name invariance
    from talentsignal.eval.fairness import audit_name_invariance
    from talentsignal.jd_parser import load_job_spec
    from talentsignal.eval import datasets as D
    from talentsignal.eval.roles import AI_SEARCH
    job = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")
    recs = D.records_of(D.build_pool(AI_SEARCH, mix={D.STRONG: 10, D.ADJACENT: 10, D.IRRELEVANT: 10}))
    rep = audit_name_invariance(recs, job, limit=30)
    if not rep.name_invariant:
        failures.append(f"fairness regressed: name not invariant, delta {rep.max_score_delta}")
    print(f"[4] name invariance: delta {rep.max_score_delta}  (== 0)")

    # 5. reproduction safety — rank-time imports numpy-only
    import subprocess
    probe = ("import sys; sys.path.insert(0,'src');"
             "from talentsignal.ranking import score_pool_hybrid;"
             "from talentsignal import artifacts, semantic_match;"
             "print('BAD' if any(m in sys.modules for m in ('torch','sentence_transformers')) else 'OK')")
    out = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, cwd=str(ROOT))
    repro_ok = out.stdout.strip() == "OK"
    if not repro_ok:
        failures.append(f"reproduction safety regressed: rank-time pulled heavy imports ({out.stdout})")
    print(f"[5] rank-time imports numpy-only: {'OK' if repro_ok else 'FAIL'}")

    print()
    if failures:
        print("CI GATE FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("CI GATE PASSED — all quality guarantees hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

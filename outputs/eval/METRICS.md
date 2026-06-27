# TalentSignal — Canonical Metrics (single source of truth)

Every number quoted in the README, deck, and submission metadata must match a row
here, and must name its **engine** and **source**. Regenerate with:

```
python3 scripts/eval_harness.py --engine spine  --out outputs/eval
python3 scripts/eval_harness.py --engine hybrid --out outputs/eval_hybrid
python3 scripts/rescue_ledger.py --candidates <100k.jsonl> --engine hybrid
```

## Ranking quality — labeled multi-JD eval (6 roles)

| metric | **spine** (default, no deps) | **hybrid** (+ embeddings) | source |
|---|---|---|---|
| mean composite | **0.9515** | **0.9728** | `outputs/eval/report.md`, `outputs/eval_hybrid/report.md` |
| honeypot rate @ top-10 (trap-heavy suite) | **0.000** | **0.000** | same |
| honeypot rate @ top-100 (trap-heavy suite) | 0.781 | 0.781 | same |
| zero-keyword paraphrase fits in top-10 | **10 / 10** | **10 / 10** | same |

> The honeypot **@100 = 0.781** is on a deliberately trap-heavy *stress suite* (the
> pool is mostly honeypots by construction) — it measures detection pressure, not
> the product. On the **actual submitted top-100** the count is **0 internally-
> impossible profiles** (`outputs/risk_summary.json`: `top10_ineligible: 0`).

## The hero metric — rescued by meaning (real 100K, Senior AI Engineer JD)

| metric | value | source |
|---|---|---|
| candidates we shortlist that a keyword filter ranks **outside its top 100** | **28 / 100** | `outputs/rescue_summary.json` |
| ...that a keyword filter ranks below #50 | 60 / 100 | same |
| pool size | 100,000 | same |

**Headline:** *a recruiter using keyword search would never see 28% of who we recommend* — each rescue carries the candidate's own evidence sentence (`outputs/rescue_ledger.csv`).

## Submission & system

| metric | value | source |
|---|---|---|
| official validator | **PASS** (100 rows, exact header, valid CAND ids) | organizers' `validate_submission.py` |
| internally-impossible profiles in submitted top-100 | **0** | `outputs/risk_summary.json` |
| rank-time for 100K | ~30s spine / ~67s hybrid (CPU, no network) | measured |
| budget | <5 min / <16 GB / CPU-only / offline ✓ | challenge limits |
| test suite | **158 passing** | `pytest tests/` |

_Last regenerated from current code. Do not quote a metric that isn't in this file._

# talentsignal-ai

TalentSignal AI is an agentic talent-intelligence ranker for the Redrob Intelligent Candidate Discovery and Ranking Challenge.

Tagline: **Evidence-backed hiring decisions for any role.**

It turns a job description into a structured scorecard, extracts evidence from candidate profiles, ranks candidates with inspectable factor scores, flags risk patterns, and generates grounded shortlist reasoning. The challenge artifact is a valid top-100 CSV; the product artifact is a recruiter-facing evidence workflow.

## Architecture (JD-agnostic hybrid engine)

TalentSignal ranks **any** job description against **any** candidate dataset — the challenge's JD/dataset are proof-case #1, not the whole system.

- **JD ingestion** (`src/talentsignal/jd_ingest.py`) — parse any free-text or structured JD into a weighted requirement model (must-have / nice-to-have / disqualifier).
- **Hybrid semantic matching** (`src/talentsignal/semantic_match.py`) — match each requirement to candidate evidence by sentence-embedding cosine **plus** lexical overlap, so a candidate who "built the recommendation engine serving the homepage" matches "shipped a ranking system" with zero shared keywords.
- **Schema-driven signals** (`src/talentsignal/schema_profile.py`) — behavioral/availability/trust scoring adapts to whatever signal fields a dataset provides (not hardcoded to Redrob's 23).
- **General consistency auditor** (`src/talentsignal/consistency_audit.py`) — role-independent internal-contradiction checks that veto impossible honeypots (e.g. 8 years at a company that has tenure beyond the candidate's stated experience, expert skill with 0 months).
- **Unified scoring** (`src/talentsignal/scoring.py`) — one JD-requirement-weighted path; same code for an AI JD and a sales JD.
- **Evaluation suite** (`src/talentsignal/eval/`, `scripts/eval_harness.py`) — NDCG@10/@50, MAP, P@10 over labeled synthetic data across multiple JDs and dataset shapes. Every ranking change is measured, not guessed.

**Two engines.** `spine` is the zero-dependency structured ranker that always produces a valid CSV in budget. `hybrid` adds the precomputed semantic index (numpy-only at rank time) and measurably improves ranking: on labeled multi-JD eval, mean composite **0.95 vs 0.88**, zero-keyword paraphrase fits reach **10/10 in top-10 (vs 3/10)**, and honeypot rate in top-10 drops to **0%**.

### Run the evaluation suite

```bash
python3 scripts/eval_harness.py --engine spine   # writes outputs/eval/report.md
python3 scripts/eval_harness.py --engine hybrid   # needs the embedding model installed
```

### Rank with the hybrid engine

```bash
# 1) offline, once (~9 min): build the embedding index (may exceed the 5-min budget)
make precompute      # or: python3 precompute.py --candidates <jsonl> --job-spec <yaml> --index-dir outputs/index

# 2) the ranking step itself loads only numpy arrays, offline, within budget
make rank-hybrid     # or: python3 rank.py --engine hybrid --index-dir outputs/index --candidates <jsonl> --out <csv>
```

### Demo: rank any JD + candidates

```bash
python3 scripts/demo_rank.py --jd demo/data/sales_jd.md \
  --candidates demo/data/sales_candidates.jsonl --engine hybrid --top-n 10
```

## Repository

- GitHub: https://github.com/sreenathmmenon/talentsignal-ai
- Author: Sreenath
- Contact: sreenathmmmenon@gmail.com

## Current Status

The repository is a validated checkpoint, not the final frozen submission. The ranking engine, local submission package, API, and recruiter cockpit are validated against the provided candidate data. We will keep iterating until final submission freeze.

Implemented checkpoint:

- Challenge command-center docs.
- Redrob Senior AI Engineer scorecard.
- Universal JD scorecard taxonomy and example scorecards across backend, data, product, sales, and design.
- Dataset profiler and archetype sampler.
- Deterministic offline ranker.
- Evidence extraction and factor scoring.
- V2 decision modules for candidate comparison, boundary review, trap examples, and interview kits.
- Risk audit and top-10 eligibility.
- Explanation audit.
- Top-25 audit and candidate comparison tools.
- Production-grade recruiter cockpit checkpoint.
- Methodology, metadata, interview defense, and final validation reports.

## Requirements

The core ranker uses only the Python standard library.

Recommended:

```bash
python3 --version
```

Python 3.11 was used during development.

## Reproduce Final Submission

```bash
python3 rank.py \
  --candidates '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl' \
  --out outputs/final_submission.csv
```

This also writes:

- `outputs/factor_scores.csv`
- `outputs/evidence_packets.jsonl`
- `outputs/risk_report.csv`
- `outputs/risk_summary.json`

## Validate

Run tests:

```bash
python3 -m pytest tests/test_baseline_pipeline.py tests/test_app_rest.py -q
```

Run official challenge validator:

```bash
python3 '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py' \
  outputs/final_submission.csv
```

Run full internal validation:

```bash
python3 scripts/validate_all.py \
  --candidates '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl' \
  --submission outputs/final_submission.csv
```

Run explanation audit:

```bash
python3 scripts/audit_explanations.py --evidence-packets outputs/evidence_packets.jsonl --strict
```

Run live UI browser validation:

```bash
python3 app.py --host 127.0.0.1 --port 8765
npx playwright test tests/ui-live.spec.js --reporter=line
```

The Playwright suite drives the browser UI against the local REST API and the real challenge candidate JSONL. It verifies ranking execution, ranked rows, candidate evidence details, filtering, sorting, CSV download, and desktop/mobile screenshots.

## Audit And Review

Generate top-25 audit:

```bash
python3 scripts/audit_top_candidates.py \
  --evidence-packets outputs/evidence_packets.jsonl \
  --out-csv outputs/top25_audit.csv \
  --out-md outputs/top25_audit.md
```

Compare two candidates:

```bash
python3 scripts/compare_candidates.py CAND_0079387 CAND_0018499 \
  --evidence-packets outputs/evidence_packets.jsonl
```

## Live Recruiter Cockpit

Start the local product UI:

```bash
python3 app.py --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/` in a browser.

The UI uses the Helix control-plane design system for a production-grade hiring intelligence cockpit. It generates a ranked shortlist from the selected candidate JSONL and JD scorecard, shows fit factors and grounded evidence, exposes risk flags, supports search/sort/risk filtering, and downloads generated CSV/evidence/risk artifacts.

The product direction is a universal JD-to-hiring-decision command center: role intelligence, evidence ranking, candidate comparison, boundary review, trust/trap review, interview probes, and exports. See `REDROB_BUSINESS_PLAN_PRODUCT_STRATEGY.md` for the Redrob business-plan signal and roadmap implication, and `TALENTSIGNAL_V2_PRODUCT_AND_ACTION_PLAN.md` for the V2 product plan.

## Docker Reproduction

The Dockerfile is intentionally minimal and uses the standard-library ranker.

```bash
docker build -t talentsignal-ai .
docker run --rm talentsignal-ai
```

The raw `candidates.jsonl` is ignored by git because it is large. For external reproduction, place the provided challenge data at the documented path or pass another mounted path to `rank.py`.

## Project Structure

- `rank.py`: final ranking command.
- `app.py`: live REST API and recruiter cockpit UI.
- `src/talentsignal/`: core package.
- `job_specs/`: machine-readable JD scorecards.
- `scripts/`: profiling, audit, validation, comparison.
- `docs/`: challenge brief, methodology support, audit evidence, interview prep.
- `outputs/`: generated submission/audit artifacts.
- `tests/`: focused pipeline, REST, and Playwright UI tests.

## Important Docs

- `AIM.md`
- `HACKATHON_CHALLENGE_AND_WORK_PREPARED.md`
- `PROJECT_COMPLETION_RULE.md`
- `PROJECT_AUTHORSHIP_RULE.md`
- `PROJECT_TAGLINE_DECISION.md`
- `COUNCIL_REVIEW_JUNE_16_2026.md`
- `PROJECT_EXECUTION_STORIES_AND_TASKS.md`
- `TALENTSIGNAL_V2_PRODUCT_AND_ACTION_PLAN.md`
- `WORLD_CLASS_EXECUTION_PLAN.md`
- `FIRST_PRIZE_PREMORTEM.md`
- `AGENTIC_AI_TALENT_INTELLIGENCE_RESEARCH.md`
- `REDROB_BUSINESS_PLAN_PRODUCT_STRATEGY.md`
- `REDROB_RESEARCH_AND_BIG_BET_STRATEGY_JUNE_17_2026.md`
- `methodology.md`
- `docs/final_completion_evidence.md`
- `docs/v2_completion_evidence.md`

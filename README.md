# talentsignal-ai

TalentSignal AI is an agentic talent-intelligence ranker for the Redrob Intelligent Candidate Discovery and Ranking Challenge.

It turns a job description into a structured scorecard, extracts evidence from candidate profiles, ranks candidates with inspectable factor scores, flags risk patterns, and generates grounded shortlist reasoning. The challenge artifact is a valid top-100 CSV; the product artifact is a recruiter-facing evidence workflow.

## Repository

- GitHub: https://github.com/sreenathmmenon/talentsignal-ai
- Author: Sreenath
- Contact: sreenathmmmenon@gmail.com

## Current Status

Epics 1-12 are implemented for the current challenge-submission scope:

- Challenge command-center docs.
- Redrob Senior AI Engineer scorecard.
- Dataset profiler and archetype sampler.
- Deterministic offline ranker.
- Evidence extraction and factor scoring.
- Risk audit and top-10 eligibility.
- Explanation audit.
- Top-25 audit and candidate comparison tools.
- Static recruiter cockpit demo.
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
python3 -m pytest tests/test_baseline_pipeline.py -q
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

## Demo

Generate a static recruiter cockpit:

```bash
python3 app.py \
  --evidence-packets outputs/evidence_packets.jsonl \
  --submission outputs/final_submission.csv \
  --out demo/recruiter_cockpit.html
```

Open `demo/recruiter_cockpit.html` in a browser. It shows ranked candidates, score factors, evidence terms, risk flags, and reasoning.

## Docker Reproduction

The Dockerfile is intentionally minimal and uses the standard-library ranker.

```bash
docker build -t talentsignal-ai .
docker run --rm talentsignal-ai
```

The raw `candidates.jsonl` is ignored by git because it is large. For external reproduction, place the provided challenge data at the documented path or pass another mounted path to `rank.py`.

## Project Structure

- `rank.py`: final ranking command.
- `app.py`: static recruiter cockpit generator.
- `src/talentsignal/`: core package.
- `job_specs/`: machine-readable JD scorecards.
- `scripts/`: profiling, audit, validation, comparison.
- `docs/`: challenge brief, methodology support, audit evidence, interview prep.
- `outputs/`: generated submission/audit artifacts.
- `tests/`: focused pipeline tests.

## Important Docs

- `AIM.md`
- `PROJECT_COMPLETION_RULE.md`
- `PROJECT_AUTHORSHIP_RULE.md`
- `PROJECT_EXECUTION_STORIES_AND_TASKS.md`
- `WORLD_CLASS_EXECUTION_PLAN.md`
- `FIRST_PRIZE_PREMORTEM.md`
- `AGENTIC_AI_TALENT_INTELLIGENCE_RESEARCH.md`
- `methodology.md`
- `docs/final_completion_evidence.md`


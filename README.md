# talentsignal-ai

TalentSignal AI is an agentic talent-intelligence ranker for the Redrob Intelligent Candidate Discovery and Ranking Challenge.

The project turns a job description into a structured scorecard, extracts evidence from candidate profiles, ranks candidates with inspectable factor scores, flags risk patterns, and generates grounded shortlist reasoning.

## Current Status

Epics 1-3 baseline are implemented:

- Challenge command-center docs.
- Redrob Senior AI Engineer scorecard.
- Dataset profiler and archetype sampler.
- Deterministic baseline ranker.
- Valid baseline top-100 CSV.

Baseline validation:

- Unit tests pass.
- Full 100,000-candidate dataset profiled.
- Baseline ranker produced 100 rows in about 13 seconds locally.
- Official challenge validator passes for `outputs/baseline_submission.csv`.

## Reproduce Baseline

```bash
python3 rank.py \
  --candidates '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl' \
  --out outputs/baseline_submission.csv
```

Validate:

```bash
python3 '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py' \
  outputs/baseline_submission.csv
```

Run tests:

```bash
python3 -m pytest tests/test_baseline_pipeline.py -q
```

## Important Docs

- `AIM.md`
- `PROJECT_COMPLETION_RULE.md`
- `PROJECT_AUTHORSHIP_RULE.md`
- `PROJECT_EXECUTION_STORIES_AND_TASKS.md`
- `WORLD_CLASS_EXECUTION_PLAN.md`
- `FIRST_PRIZE_PREMORTEM.md`
- `AGENTIC_AI_TALENT_INTELLIGENCE_RESEARCH.md`
- `docs/epic_1_3_completion_evidence.md`

## Authorship

Author: Sreenath


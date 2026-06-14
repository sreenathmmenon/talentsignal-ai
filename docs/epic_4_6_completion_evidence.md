# Epic 4-6 Completion Evidence

Date: June 14, 2026

Scope:

- Epic 4: Candidate Evidence Intelligence
- Epic 5: Risk Audit And Trap Avoidance
- Epic 6: Scoring Optimization And Manual Audit Loop

Completion standard: `PROJECT_COMPLETION_RULE.md`.

## Epic 4: Candidate Evidence Intelligence

Completed implementation:

- `CandidateEvidence` object in `src/talentsignal/features.py`.
- Source-separated evidence extraction:
  - profile text
  - career text
  - skill text
  - title/category signals
  - behavioral signals
  - company/product/service signals
- Technical evidence extraction:
  - retrieval/search/ranking/recommendation
  - vector/embedding/search infrastructure
  - ML/LLM/fine-tuning/Python terms
  - evaluation terms
  - production/shipping terms
- Talent graph dictionaries in `src/talentsignal/talent_graph.py`.
- Evidence packet export in `outputs/evidence_packets.jsonl`.

Acceptance evidence:

- Every top-100 candidate has an evidence packet.
- Factor scores include evidence counts and source terms.
- Reasoning is generated from evidence fields.

Artifacts:

- `outputs/evidence_packets.jsonl`
- `outputs/factor_scores.csv`

## Epic 5: Risk Audit And Trap Avoidance

Completed implementation:

- Suspicious profile rules in `src/talentsignal/risk_audit.py`.
- Risk flags for:
  - non-tech AI keyword stuffing
  - AI terms without career evidence
  - expert skills with zero duration
  - service-only without product/search evidence
  - stale low-response candidates
  - shallow AI-tool interest
- Risk penalties included in scoring.
- Top-10 eligibility flag included in scoring.
- Confidence score included in scoring.
- Risk report and summary export.

Acceptance evidence:

```text
risk_summary {'rows': 100, 'top10_ineligible': 0, 'risk_flag_counts': {}, 'top100_with_any_risk_flag': 0}
```

This means the current top 100 has no flagged suspicious profiles under the implemented risk policy, and every top-10 candidate is top-10 eligible.

Artifacts:

- `outputs/risk_report.csv`
- `outputs/risk_summary.json`

## Epic 6: Scoring Optimization And Manual Audit Loop

Completed implementation:

- Factor score export with:
  - final score
  - technical evidence
  - career fit
  - seniority
  - logistics
  - behavioral score
  - trust score
  - confidence
  - top-10 eligibility
  - penalty
  - risk flags
  - evidence counts
  - evidence terms
- Top-25 audit generator.
- Candidate comparison CLI.
- Updated top-25 audit output.

Acceptance evidence:

```text
python3 scripts/audit_top_candidates.py --evidence-packets outputs/evidence_packets.jsonl --out-csv outputs/top25_audit.csv --out-md outputs/top25_audit.md
Wrote 25 audit rows to outputs/top25_audit.csv
```

```text
top10_all_eligible True
```

Candidate comparison smoke test:

```text
python3 scripts/compare_candidates.py CAND_0018499 CAND_0046525 --evidence-packets outputs/evidence_packets.jsonl
```

Result: comparison prints rank, score, factor scores, confidence, eligibility, evidence terms, risk flags, and reasoning for both candidates.

Artifacts:

- `outputs/factor_scores.csv`
- `outputs/top25_audit.csv`
- `outputs/top25_audit.md`
- `scripts/audit_top_candidates.py`
- `scripts/compare_candidates.py`

## End-To-End Validation

Tests:

```text
python3 -m pytest tests/test_baseline_pipeline.py -q
4 passed in 0.01s
```

Compile check:

```text
PYTHONPYCACHEPREFIX=.pycache_compile python3 -m compileall -q src scripts rank.py
```

Result: passed.

Full ranking:

```text
python3 rank.py --candidates '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl' --out outputs/baseline_submission.csv
Wrote outputs/baseline_submission.csv with 100 rows in 16.56s
```

Official validation:

```text
python3 '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py' outputs/baseline_submission.csv
Submission is valid.
```

Internal validation:

```text
internal_validation_errors 0
```

## Current Top-10 Quality Gate

Current top-10 IDs:

- `CAND_0079387`
- `CAND_0018499`
- `CAND_0027801`
- `CAND_0011687`
- `CAND_0027691`
- `CAND_0006567`
- `CAND_0081846`
- `CAND_0028793`
- `CAND_0046525`
- `CAND_0069905`

All top-10 candidates are `top10_eligible=True` and have direct career retrieval/ranking evidence under the current evidence policy.

## Status

Epics 4-6 are complete for the current baseline/product scope.

This is still not the final competition submission. Later epics must add:

- stronger explanation validation,
- methodology and README finalization,
- clean reproduction packaging,
- demo/recruiter cockpit,
- deeper raw-profile manual review before final submission.


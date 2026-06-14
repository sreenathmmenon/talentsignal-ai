# Final Completion Evidence

Date: June 14, 2026

Scope: Epics 1-12 current project/submission package.

Completion standard: `PROJECT_COMPLETION_RULE.md`.

## Final Artifacts

- Final CSV: `outputs/final_submission.csv`
- Reproduced CSV: `outputs/repro_submission.csv`
- Factor scores: `outputs/factor_scores.csv`
- Evidence packets: `outputs/evidence_packets.jsonl`
- Risk report: `outputs/risk_report.csv`
- Risk summary: `outputs/risk_summary.json`
- Explanation audit: `outputs/explanation_audit.json`
- Final validation report: `outputs/final_validation_report.json`
- Top-25 audit: `outputs/top25_audit.csv`, `outputs/top25_audit.md`
- Demo: `demo/recruiter_cockpit.html`
- Methodology: `methodology.md`
- Metadata: `submission_metadata.yaml`
- Interview defense: `docs/interview_defense.md`
- Candidate case studies: `docs/candidate_case_studies.md`
- Portfolio story: `docs/portfolio_story.md`

## Validation Results

Unit tests:

```text
python3 -m pytest tests/test_baseline_pipeline.py -q
5 passed in 0.01s
```

Compile check:

```text
PYTHONPYCACHEPREFIX=.pycache_compile python3 -m compileall -q src scripts rank.py app.py
```

Result: passed.

Final ranking:

```text
python3 rank.py --candidates '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl' --out outputs/final_submission.csv
Wrote outputs/final_submission.csv with 100 rows in 16.94s
```

Official validator:

```text
Submission is valid.
```

Full validation:

```json
{
  "row_count": 100,
  "sha256": "fc20f28872c4e3eb27d224e994d7d37b335a0fac0173c901f7e9153bd9a10d4a",
  "internal_error_count": 0,
  "official_validator_returncode": 0,
  "official_validator_stdout": "Submission is valid.",
  "explanation_warning_count": 0
}
```

Clean reproduction:

- `outputs/repro_submission.csv` has the same SHA256 as `outputs/final_submission.csv`.
- Byte-identical: true.
- Reproduced CSV official validator: `Submission is valid.`

Audit checks:

- Top-10 all eligible: true.
- Top-25 automated audit non-keep count: 0.
- Top-100 risk flags under current risk policy: 0.

Demo smoke:

```text
python3 app.py --evidence-packets outputs/evidence_packets.jsonl --submission outputs/final_submission.csv --out demo/recruiter_cockpit.html
Wrote demo/recruiter_cockpit.html with 25 candidates
```

Candidate comparison smoke:

```text
python3 scripts/compare_candidates.py CAND_0079387 CAND_0018499 --evidence-packets outputs/evidence_packets.jsonl
```

Result: printed rank, score, factor scores, eligibility, evidence, risk flags, and reasoning for both candidates.

## Completion Status

The repository is complete for the current local submission package and passes the implemented end-to-end gates.

One user-owned portal field remains outside local execution:

- `primary_contact.phone` must be filled by Sreenath before official portal upload.

The hosted sandbox URL is represented by the GitHub README demo/Docker instructions. If the portal strictly requires a hosted URL rather than a repo/Docker recipe, Sreenath must deploy the static demo or app to a chosen host and update `submission_metadata.yaml`.


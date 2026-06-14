# Runtime Report

Command:

```bash
python3 rank.py --candidates '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl' --out outputs/baseline_submission.csv
```

Observed baseline result:

- Candidates processed: 100,000
- Output rows: 100
- Runtime: 12.94 seconds on local Mac environment
- Final command network usage: none
- Final command GPU usage: none
- Hosted API usage: none

Status:

- Runtime is well below the 5-minute challenge limit for this baseline.
- Memory was not externally profiled in this run; the implementation streams candidates and stores only score/evidence objects needed for sorting.

## Final Run

Command:

```bash
python3 rank.py --candidates '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl' --out outputs/final_submission.csv
```

Observed result:

- Candidates processed: 100,000
- Output rows: 100
- Runtime: 16.94 seconds on local Mac environment
- Final command network usage: none
- Final command GPU usage: none
- Hosted API usage: none
- Official validator: `Submission is valid.`
- Internal validation errors: 0
- Explanation audit warnings: 0
- SHA256: `fc20f28872c4e3eb27d224e994d7d37b335a0fac0173c901f7e9153bd9a10d4a`

Clean reproduction:

- Reproduced CSV: `outputs/repro_submission.csv`
- Reproduced SHA256: `fc20f28872c4e3eb27d224e994d7d37b335a0fac0173c901f7e9153bd9a10d4a`
- Byte-identical to final CSV: true

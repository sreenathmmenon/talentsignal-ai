# TalentSignal — reproducible commands.
#
# Two engines:
#   spine  : structured ranker, pure stdlib, always reproduces in budget.
#   hybrid : spine + precomputed semantic index (numpy-only at rank time).

CANDIDATES ?= [PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl
JOB_SPEC   ?= job_specs/redrob_senior_ai_engineer.yaml
OUT        ?= outputs/final_submission.csv
INDEX_DIR  ?= outputs/index
VALIDATOR  ?= [PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py

.PHONY: rank rank-hybrid precompute eval test validate clean

## Produce the submission CSV (spine engine) and validate it.
rank:
	python3 rank.py --candidates "$(CANDIDATES)" --out "$(OUT)" --job-spec "$(JOB_SPEC)"
	$(MAKE) validate

## Produce the submission CSV with the hybrid engine (needs a precomputed index).
rank-hybrid:
	python3 rank.py --engine hybrid --index-dir "$(INDEX_DIR)" \
		--candidates "$(CANDIDATES)" --out "$(OUT)" --job-spec "$(JOB_SPEC)"
	$(MAKE) validate

## Offline: build the embedding index (allowed to exceed the 5-min ranking budget).
precompute:
	python3 precompute.py --candidates "$(CANDIDATES)" --job-spec "$(JOB_SPEC)" --index-dir "$(INDEX_DIR)"

## Run the evaluation suite (spine + hybrid) and write outputs/eval/report.md.
eval:
	python3 scripts/eval_harness.py --engine spine --out outputs/eval

## Validate the submission CSV against the official validator.
validate:
	cp "$(OUT)" /tmp/team_submission.csv
	python3 "$(VALIDATOR)" /tmp/team_submission.csv

test:
	python3 -m pytest -q

clean:
	rm -rf outputs/repro_* outputs/eval /tmp/team_submission.csv

prove:
	python3 scripts/prove.py

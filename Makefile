# TalentSignal — reproducible commands.
#
# Two engines:
#   spine  : structured ranker, pure stdlib, always reproduces in budget.
#   hybrid : spine + precomputed semantic index (numpy-only at rank time).

CANDIDATES ?= [PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl
JOB_SPEC   ?= job_specs/redrob_senior_ai_engineer.yaml
# SUBMISSION is the committed source-of-truth CSV — never overwritten by a repro run.
SUBMISSION ?= outputs/final_submission.csv
# Reproductions write HERE (a separate path) so the committed CSV stays pristine.
OUT        ?= outputs/repro_submission.csv
INDEX_DIR  ?= outputs/index
VALIDATOR  ?= [PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py

.PHONY: reproduce rank rank-hybrid precompute eval test validate verify-reproduction clean

## THE canonical reproduce command: regenerate the submitted (hybrid) CSV to a
## separate path and prove it byte-matches the committed submission.
reproduce: rank-hybrid verify-reproduction

## Regenerate with the SUBMITTED (hybrid) engine to $(OUT), then validate.
rank-hybrid:
	python3 rank.py --engine hybrid --index-dir "$(INDEX_DIR)" \
		--candidates "$(CANDIDATES)" --out "$(OUT)" --job-spec "$(JOB_SPEC)"
	$(MAKE) validate

## Byte-diff the regenerated CSV against the committed submission (fails if they differ).
verify-reproduction:
	@diff -q "$(OUT)" "$(SUBMISSION)" \
		&& echo "REPRODUCTION OK: $(OUT) is byte-identical to $(SUBMISSION)" \
		|| (echo "REPRODUCTION MISMATCH: $(OUT) != $(SUBMISSION)"; exit 1)

## Zero-dependency fallback: spine engine to $(OUT) (a DIFFERENT, also-valid ranking).
rank:
	python3 rank.py --candidates "$(CANDIDATES)" --out "$(OUT)" --job-spec "$(JOB_SPEC)"
	$(MAKE) validate

## Offline: build the embedding index (allowed to exceed the 5-min ranking budget).
precompute:
	python3 precompute.py --candidates "$(CANDIDATES)" --job-spec "$(JOB_SPEC)" --index-dir "$(INDEX_DIR)"

## Regenerate TOP10_REPORT.md from the committed submission (so it never drifts).
report:
	python3 scripts/gen_top10_report.py

## Measure résumé-attack resistance (non-circular; no labels needed).
adversarial:
	python3 scripts/adversarial_report.py

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

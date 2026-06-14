# Decision Log

## 2026-06-14: Build Deterministic Baseline First

Decision: implement a deterministic Python baseline ranker before UI or advanced experiments.

Reason: the challenge rewards a valid reproducible CSV and top-10 precision. A baseline output enables real candidate inspection and iterative scoring.

Alternatives considered:

- Start with a polished demo first.
- Use live LLM/API ranking during final command.
- Build generic JD support before Redrob-specific scoring.

Consequence: first development work focuses on docs, scorecard, data profiling, loader, scoring, reasoning, and validator pass.

## 2026-06-14: Redrob JD Scorecard As Default Config

Decision: encode the Redrob JD as `job_specs/redrob_senior_ai_engineer.yaml`.

Reason: this keeps scoring explainable, reproducible, and extensible to other JDs later.

Consequence: v1 parser loads a curated scorecard, while generic JD parsing remains simple.


# Redrob Challenge Brief

## Objective

Build an intelligent candidate ranking system for the provided Senior AI Engineer founding-team JD. Submit only the top 100 candidates from the 100,000-candidate pool.

## Required Output

CSV columns, in this exact order:

```text
candidate_id,rank,score,reasoning
```

Rules:

- Exactly 100 data rows plus one header row.
- Ranks must be integers `1` through `100`, each appearing once.
- Candidate IDs must be unique and must follow `CAND_XXXXXXX`.
- Scores must be floats and monotonically non-increasing by rank.
- Reasoning is strongly recommended and should be 1-2 grounded sentences.

## Scoring

Hidden composite:

- `NDCG@10`: 50%
- `NDCG@50`: 30%
- `MAP`: 15%
- `P@10`: 5%

Implication: top-10 precision matters most. We should prefer a conservative top 10 with strong direct evidence over broad but risky keyword matches.

## Final Ranking Constraints

These constraints apply to the submitted reproduction command, not to development/research:

- Runtime: <= 5 minutes wall clock.
- Memory: <= 16 GB RAM.
- Compute: CPU only.
- Network: off.
- No hosted LLM/API calls during ranking.
- Disk: <= 5 GB intermediate state.

## Evaluation Stages

1. Format validation.
2. Hidden ranking score.
3. Code reproduction plus honeypot check.
4. Manual review of reasoning, methodology, git history, and code quality.
5. Defend-your-work interview.

Stage 3 disqualifiers include inability to reproduce within limits, missing/fabricated code, or honeypot rate above 10% in top 100.

Stage 4 risks include hallucinated reasoning, generic/templated reasoning, methodology not matching code, flat git history, or code made mostly of live LLM calls.

## Redrob Signals

Important behavioral signals:

- Profile completeness.
- Last active date.
- Open-to-work flag.
- Recruiter response rate.
- Average response time.
- Skill assessment scores.
- Notice period.
- Preferred work mode.
- Willingness to relocate.
- GitHub activity.
- Search appearances.
- Saved by recruiters.
- Interview completion rate.
- Offer acceptance rate.
- Email/phone/LinkedIn verification.

These should modify hireability: a technically strong candidate who is stale, unresponsive, and unavailable should not outrank a comparable active candidate.

## Primary JD Interpretation

The target is a Senior AI Engineer for Redrob's founding AI engineering team. The real fit is not "most AI keywords"; it is evidence of production ML/search/ranking/retrieval systems plus product-engineering judgment.

Must-have signals:

- Production ML systems.
- Embeddings, retrieval, ranking, search, recommender, vector/hybrid search, or similar.
- Strong Python.
- Evaluation frameworks for ranking systems: NDCG, MRR, MAP, A/B tests, offline-to-online correlation.
- Product shipping and willingness to own practical systems.

Preferred signals:

- LLM fine-tuning, LoRA, QLoRA, PEFT.
- Learning-to-rank.
- HR-tech, recruiting tech, marketplace products.
- Distributed systems or inference optimization.
- Open-source/papers/talks/external validation.

Negative signals:

- Pure research without production deployment.
- Shallow recent LangChain/OpenAI demo experience only.
- No recent production coding.
- Service-only career path without product-company evidence.
- CV/speech/robotics focus without significant NLP/IR/search relevance.
- AI keyword stuffing without career evidence.

## Completion Gate

Any submission candidate must pass:

- Official `validate_submission.py`.
- Internal candidate ID existence checks.
- Top-25 manual audit.
- Runtime measurement.
- Reasoning review.
- Premortem-driven risk review.


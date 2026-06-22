# Hackathon Challenge And Work Prepared

Date: June 22, 2026

Project: TalentSignal AI  
Tagline: Evidence-backed hiring decisions for any role.

## 1. What Is The Hackathon Challenge?

The Redrob / India Runs challenge asks participants to build an intelligent candidate ranking system.

The core problem:

> Given a large candidate dataset and the target job description, identify the best 100 candidates for a Senior AI Engineer founding-team role at Redrob, ranked from strongest to weakest fit.

The system must output a CSV with exactly these columns:

```text
candidate_id,rank,score,reasoning
```

The challenge is not a normal keyword search problem. The stated and implied difficulty is that many candidates may mention AI, ML, LLMs, or trending tools, but may not have real production evidence for the actual role.

The winning solution must understand the job requirement, extract candidate evidence, avoid keyword traps, rank candidates defensibly, and produce a reproducible submission.

## 2. Official Submission Requirements

The final CSV must satisfy:

- Exactly 100 data rows.
- Candidate IDs must be valid and unique.
- Ranks must be exactly 1 through 100.
- Scores must be non-increasing by rank.
- Reasoning should be grounded, factual, and specific.

The final reproducible ranking command must follow the official challenge constraints:

- CPU only.
- No GPU.
- No network calls.
- No hosted LLM/API calls.
- Runtime under 5 minutes.
- Memory under 16 GB.
- Deterministic and reproducible.

Development can use any tools, models, assistants, cloud machines, UI frameworks, or APIs, but the final scoring command must obey the offline constraints.

## 3. Scoring And Why Top 10 Matters Most

The hidden challenge scoring weights are:

- NDCG@10: 50%
- NDCG@50: 30%
- MAP: 15%
- P@10: 5%

This means the top 10 matters more than anything else. A flashy but risky candidate in the top 10 can hurt badly. Our ranking policy is therefore conservative at the top: prefer candidates with direct production evidence over candidates with broad but weak keyword matches.

## 4. Target Job Understanding

The target role is:

> Senior AI Engineer, founding team, Redrob AI.

Important positive signals:

- Production ML systems.
- Retrieval, ranking, search, recommendation, matching, or personalization.
- Embeddings, vector search, hybrid search, semantic search, BM25, FAISS, Pinecone, Elasticsearch, OpenSearch, etc.
- Ranking evaluation: NDCG, MRR, MAP, precision/recall, A/B tests, offline/online evaluation.
- Strong Python and ML engineering.
- Product engineering and shipping practical systems.
- Startup/product-company ownership.
- 5-9 years experience, especially around 6-8 years.
- India and preferred locations such as Pune/Noida, or willingness to relocate.
- Active, responsive, reachable candidates.

Important negative signals:

- AI keywords without career evidence.
- Shallow LangChain/OpenAI demo experience only.
- Pure research without production deployment.
- Non-technical candidates with AI buzzwords.
- Expert skills with zero duration or weak endorsements.
- Stale candidates with low response rate.
- Service-only career paths without product/search evidence.
- CV/speech/robotics focus without relevant NLP/search/retrieval/ranking evidence.

## 5. What Data We Have

Challenge assets include:

- `candidates.jsonl`: 100,000 candidate profiles.
- `job_description.docx`: target Redrob job description.
- `candidate_schema.json`: schema for candidate records.
- `redrob_signals_doc.docx`: Redrob behavioral signal documentation.
- `submission_spec.docx`: rules and evaluation constraints.
- `sample_submission.csv`: expected format.
- `validate_submission.py`: official validator.
- `submission_metadata_template.yaml`: metadata template.

Each candidate includes profile fields, career history, skills, education, and Redrob behavioral signals such as activity, response rate, notice period, verification, recruiter saves, interview completion, and offer acceptance.

## 6. What We Prepared

### Core Ranking Engine

Implemented:

- `rank.py`: final offline ranking command.
- `src/talentsignal/features.py`: candidate evidence extraction.
- `src/talentsignal/scoring.py`: factor scoring and penalties.
- `src/talentsignal/ranking.py`: ranking pipeline and export writers.
- `src/talentsignal/reasoning.py`: grounded reasoning generation.
- `src/talentsignal/risk_audit.py`: trap/risk flags.
- `src/talentsignal/jd_parser.py`: structured job scorecard loading.

The ranker reads the candidate JSONL, builds evidence, scores candidates, sorts deterministically, and writes the final CSV plus supporting artifacts.

### Job Scorecard

Prepared:

- `job_specs/redrob_senior_ai_engineer.yaml`

This contains:

- Role title and category.
- Preferred experience range.
- Preferred locations.
- Must-have signals.
- Nice-to-have signals.
- Disqualifiers.
- Scoring weights.
- Final-ranking constraints.

Why:

The challenge role has specific meaning. We should not rank using generic "AI" relevance. The scorecard makes the hiring intent explicit and reproducible.

### Evidence Extraction

The system extracts:

- Current title and location.
- Years of experience.
- Career text and skill text.
- Retrieval/search/ranking terms.
- Vector/embedding/tooling terms.
- ML/LLM/Python terms.
- Evaluation terms.
- Production/shipping terms.
- Product-company vs service-company signals.
- Behavioral hireability signals.
- Suspicious profile patterns.

Why:

The challenge likely includes keyword traps. We need to distinguish career evidence from skill-list claims.

### Scoring Factors

The main factor groups are:

- Technical evidence.
- Career fit.
- Seniority.
- Logistics.
- Behavioral availability.
- Trust.
- Risk penalty.
- Confidence/top-10 eligibility.

Why:

Strong hiring fit is not only technical keywords. A candidate must be relevant, senior enough, reachable, responsive, logistically plausible, and trustworthy.

### Risk And Trap Detection

Implemented risk checks include:

- Non-tech AI keyword stuffing.
- AI terms without career evidence.
- Expert skills with zero duration.
- Service-only background without product/search evidence.
- Stale low-response profile.
- Shallow AI-tool interest.

Why:

Manual review and honeypot checks can penalize rankings that promote fake-looking or weak candidates. Risk flags help prevent that.

### Explanations

Each ranked candidate gets concise reasoning based on extracted evidence.

The reasoning mentions:

- Role/title.
- Experience.
- Location.
- Career evidence.
- Production evidence.
- Vector/search/evaluation evidence when applicable.
- Concerns when relevant.

Why:

Reasoning must be factual and defensible. We avoid free-form hallucinated explanations.

### Output Artifacts

Generated artifacts include:

- `outputs/final_submission.csv`
- `outputs/factor_scores.csv`
- `outputs/evidence_packets.jsonl`
- `outputs/risk_report.csv`
- `outputs/risk_summary.json`
- `outputs/final_validation_report.json`

Why:

The CSV is the scoring artifact. The other files help with audit, debugging, defense, and product demonstration.

## 7. Product Layer We Built

The project is not only a CSV generator. We built a recruiter-facing cockpit in:

- `app.py`

The UI includes:

- Role Intelligence.
- Decision Framework.
- Ranked Shortlist.
- Evidence Packet.
- Compare Mode.
- Trust Layer.
- Interview Kit.
- Boundary Review.
- Trap Examples.
- Universal JD Proof.
- CSV/factor/evidence/risk downloads.

Why:

The hackathon prize is not only money. The bigger opportunity is visibility, hiring opportunities, and showing product thinking. A strong UI helps reviewers understand the system, but it must support the ranking proof rather than distract from it.

## 8. Broader Product Direction

After Redrob research, the broader idea evolved from "resume ranker" to:

> TalentSignal Mission Control: the decision and verification layer for Redrob's hiring graph.

Redrob appears to be building a larger system around:

- People search.
- Company search.
- Job data.
- Enrichment.
- Assessments.
- Mock interviews.
- Deep research.
- APIs.
- Workflows.

Our bigger product direction is to convert a hiring requirement into a full talent mission:

- Role mission intake.
- Market map.
- Discovery strategy.
- Evidence ranking.
- Verification plan.
- Outreach strategy.
- Interview loop.
- Hiring decision memo.
- Learning feedback.

For the hackathon, the deterministic Evidence Ranker is the core proof case.

## 9. Universal JD Work

We added early support for multiple job categories:

- Backend Platform Engineer.
- Data Analytics Lead.
- Enterprise Account Executive.
- Product Designer.
- Product Manager.

Files:

- `src/talentsignal/category_taxonomy.py`
- `job_specs/examples/`
- `scripts/evaluate_multi_jd.py`
- `outputs/multi_jd_candidate_review.md`

Why:

The long-term product should support any JD, not only the Redrob AI role.

Current honest status:

- The Redrob AI/search path is strongest.
- Data/backend behavior is partly plausible.
- Sales/product/design categories still need stronger category-specific evidence extraction and title gating.
- We should not overclaim "any JD" until this is improved.

## 10. Validation Completed

Validation performed during development includes:

- Python compile checks.
- Backend pytest suite.
- REST API tests.
- Playwright live UI tests.
- Official submission validator.
- Internal validation script.
- Explanation audit.
- Multi-JD candidate review.

Recent known validation:

- Backend tests passed: `9 passed`.
- Official validator has passed for generated final submission.
- Live UI validation has passed in earlier Playwright runs.

Important note:

Some artifacts became stale after later scoring changes. The council review identified that docs such as top-25 audit and case studies must be regenerated before any final submission freeze.

## 11. Why We Made These Choices

### Why deterministic instead of hosted LLM ranking?

The final command cannot use network or hosted APIs. A deterministic ranker is reproducible, fast, auditable, and challenge-compliant.

### Why evidence-based instead of keyword matching?

The role requires real production ML/search/ranking experience. Keyword matching can promote shallow or fake-looking candidates. Evidence separation is necessary.

### Why risk flags?

The dataset likely includes honeypots and traps. Risk flags reduce the chance of ranking weak keyword-stuffed candidates highly.

### Why behavioral signals?

Hiring fit is not only technical ability. A stale, unresponsive candidate may be less useful than a similarly qualified active candidate.

### Why a UI?

The CSV wins the scoring stage, but the UI helps manual review, interview defense, and hiring-opportunity visibility.

### Why broader Redrob product research?

Redrob's platform direction is broader than resume ranking. To stand out, the project should show a roadmap idea that fits Redrob's people/search/enrichment/assessment ecosystem.

## 12. Current Risks And Open Work

P0 risks before final freeze:

1. Regenerate all stale artifacts from the current final CSV.
2. Fix substring matching false positives.
3. Tighten phrase coverage scoring.
4. Re-audit top 25 from raw profiles.
5. Add #90-#110 boundary review and #100 vs #101 defense.
6. Add baseline comparison against keyword/BM25-style ranking.
7. Vendor or inline the selected Helix CSS for external demo reproducibility.
8. Keep product claims precise and avoid overclaiming production/legal readiness.

P1 product improvements:

1. Raw JD intake.
2. Scorecard approval workflow.
3. Candidate review states.
4. Hiring-manager decision memo.
5. Better Compare Mode tradeoff narratives.
6. Interview rubrics with score anchors.
7. Stronger category-specific evidence extraction for non-AI roles.

## 13. How To Reproduce The Current Challenge Submission

Run:

```bash
python3 rank.py \
  --candidates '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl' \
  --out outputs/final_submission.csv
```

Validate:

```bash
python3 '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py' \
  outputs/final_submission.csv
```

Run backend tests:

```bash
python3 -m pytest tests/test_baseline_pipeline.py tests/test_app_rest.py -q
```

Run UI:

```bash
python3 app.py --host 127.0.0.1 --port 8766
```

Open:

```text
http://127.0.0.1:8766/
```

## 14. Short Pitch

TalentSignal AI is evidence-based hiring decision support for the Redrob candidate ranking challenge.

It converts the Redrob Senior AI Engineer JD into a role scorecard, extracts structured evidence from 100,000 candidate profiles, ranks candidates with transparent factor scores, avoids keyword-stuffing traps, generates grounded reasoning, and provides a recruiter-facing cockpit for evidence review, comparison, trust checks, interview planning, and export.

The immediate goal is to submit the best possible validator-clean top-100 CSV. The broader goal is to show a Redrob-aligned product direction: TalentSignal Mission Control, a decision and verification layer for people search, enrichment, assessments, and hiring workflows.


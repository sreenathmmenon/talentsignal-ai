# Project Execution Stories And Tasks

Date: June 14, 2026

Project: `TalentSignal Ranker`

Mission: build a world-class, agentic hiring-intelligence product and a first-prize-caliber Redrob hackathon submission.

## Execution Principles

- Follow `PROJECT_COMPLETION_RULE.md`: no task, story, feature, or milestone is complete unless it works correctly end to end, is production-grade for scope, tested, validated, reviewed, and has no known unresolved critical issue.
- Win the Redrob challenge first; broader product ambition must not dilute top-10 ranking quality.
- Build a product-shaped system, not a one-off script.
- Use agentic thinking in architecture: JD Strategist, Evidence Miner, Talent Graph Builder, Match Judge, Risk Auditor, Explanation Writer, Recruiter Cockpit.
- Keep the final challenge command deterministic, reproducible, offline, CPU-only, and within official limits.
- Use any useful tools during development: AI assistants, APIs, Colab, local Mac, cloud, notebooks, UI frameworks, Docker, manual review.
- Every top candidate must be defensible from extracted evidence.
- Every important decision must be documented.
- Every generated CSV must pass validation before being considered real.

## Delivery Milestones

### M0: Command Center Ready

Outcome: all challenge rules and product decisions are visible in the repo.

Completion signal:

- Challenge docs converted/summarized.
- JD analysis written.
- Decision log exists.
- Manual audit template exists.
- Implementation backlog exists.

### M1: Baseline Valid Submission

Outcome: a valid top-100 CSV can be generated end to end.

Completion signal:

- `rank.py` reads 100K JSONL and writes valid CSV.
- Official validator passes.
- Runtime measured.
- Baseline top 25 manually inspected.

### M2: Evidence-Based Ranker

Outcome: ranking uses real career evidence, not only keywords.

Completion signal:

- Candidate evidence objects generated.
- Factor scores exported.
- Top 10 has direct Redrob JD evidence.
- Keyword stuffers and obvious traps are down-ranked.

### M3: Explainable And Auditable Ranker

Outcome: every final row has grounded reasoning and risk checks.

Completion signal:

- Reasoning is specific, varied, and fact-grounded.
- Risk flags exist.
- Internal audit catches suspicious profiles.
- Top 25 audit completed after latest scoring change.

### M4: Product Demo

Outcome: reviewers can see this as an agentic hiring-intelligence product.

Completion signal:

- Demo runs on a small sample.
- Demo shows JD, ranked list, evidence packet, score breakdown, risk flags, and CSV export.
- Demo is documented.

### M5: Submission Ready

Outcome: final CSV, repo, docs, metadata, and interview defense are ready.

Completion signal:

- Final command reproduces final CSV.
- Validator passes.
- README and methodology are complete.
- Metadata complete.
- Demo link or runnable alternative works.
- Interview defense notes are prepared.

## Epic 1: Challenge Command Center

Goal: remove ambiguity and prevent preventable submission failures.

### Story 1.1: Challenge Brief

As a builder, I want a concise challenge brief so that implementation never violates the official rules.

Tasks:

- Extract key points from `submission_spec.docx`.
- Extract key points from `redrob_signals_doc.docx`.
- Extract key points from `job_description.docx`.
- Create `docs/challenge_brief.md`.
- Include scoring weights, format rules, reproduction constraints, metadata requirements, and evaluation stages.

Acceptance criteria:

- The brief states CSV shape exactly.
- The brief states official final-ranking constraints.
- The brief states scoring metric weights.
- The brief states Stage 3, Stage 4, and Stage 5 risks.

Priority: P0

Depends on: none

### Story 1.2: Redrob JD Scorecard

As a ranking system, I want a structured scorecard for the Redrob JD so that candidate evaluation matches the real role.

Tasks:

- Convert the JD into must-have, nice-to-have, disqualifier, logistics, behavioral, and culture categories.
- Create `docs/jd_analysis_redrob_senior_ai_engineer.md`.
- Create machine-readable `job_specs/redrob_senior_ai_engineer.yaml`.
- Add weighting assumptions and anti-keyword-stuffing notes.

Acceptance criteria:

- The scorecard captures production ML, retrieval, ranking, search, embeddings, Python, evaluation, and product shipping.
- Disqualifiers include pure research, shallow API demos, no recent coding, service-only risk, and irrelevant AI domains.
- The YAML can be loaded by code.

Priority: P0

Depends on: Story 1.1

### Story 1.3: Decision Log

As a team, I want a decision log so that reviewers see real iteration and we can defend tradeoffs.

Tasks:

- Create `docs/decision_log.md`.
- Add entries for scoring weights, trap rules, demo platform, dependencies, and final submission choices.
- Update after every major scoring change.

Acceptance criteria:

- At least one initial entry exists.
- Each entry has date, decision, reason, alternatives, and consequence.

Priority: P1

Depends on: none

### Story 1.4: Manual Audit Template

As a reviewer of our own system, I want a manual audit checklist so that top candidates are inspected consistently.

Tasks:

- Create `docs/manual_audit_template.md`.
- Include checks for JD fit, production evidence, title fit, behavior, logistics, risk flags, reasoning support, and rank confidence.
- Include pass/fail/concern fields.

Acceptance criteria:

- Template supports top-25 review.
- Template supports random top-100 review.
- Template includes "reject from top 10" triggers.

Priority: P0

Depends on: Story 1.1

### Story 1.5: Premortem Review Gate

As a team trying to win first prize, I want the premortem reviewed during implementation so that known failure modes actively shape the build.

Tasks:

- Read `FIRST_PRIZE_PREMORTEM.md` before tuning the final ranker.
- Convert the highest-risk failure modes into concrete checks in `docs/final_submission_checklist.md`.
- Map ranking-quality risks to scoring/audit tasks.
- Map reproduction risks to validation tasks.
- Map reasoning risks to explanation validation tasks.
- Map interview-defense risks to `docs/interview_defense.md`.

Acceptance criteria:

- At least 30 premortem risks are explicitly covered by checklist or tests.
- Top-10 audit includes premortem-driven checks.
- Final validation checklist links back to the premortem.

Priority: P0

Depends on: Story 1.4

## Epic 2: Data Profiling And Dataset Intelligence

Goal: understand the candidate pool and traps before final scoring.

### Story 2.1: Dataset Profiler

As a data scientist, I want a profiling script so that we understand distributions and outliers.

Tasks:

- Create `scripts/profile_dataset.py`.
- Count rows, titles, countries, cities, industries, companies, skills, experience bands, behavioral distributions.
- Export `outputs/dataset_profile.json`.
- Export `outputs/dataset_profile.md`.

Acceptance criteria:

- Script processes 100K records.
- Output includes top titles, countries, skills, companies, and key Redrob signal percentiles.
- Runtime is acceptable on local Mac.

Priority: P0

Depends on: none

### Story 2.2: Candidate Archetype Discovery

As a ranker designer, I want candidate archetypes so that scoring can distinguish real fits from traps.

Tasks:

- Identify archetypes: strong AI engineer, search/retrieval engineer, recommender engineer, adjacent backend/data engineer, pure researcher, non-tech AI keyword stuffer, stale candidate, service-only candidate, suspicious profile.
- Write archetype definitions into `docs/candidate_archetypes.md`.
- Sample 5-10 candidates per archetype for manual inspection.

Acceptance criteria:

- Each archetype has positive/negative scoring implications.
- At least 30 candidates sampled across archetypes.

Priority: P0

Depends on: Story 2.1

### Story 2.3: Trap Pattern Research

As a Risk Auditor, I want public and dataset-specific trap rules so that honeypot-like candidates are down-ranked.

Tasks:

- Inspect suspicious profiles from dataset.
- Define rules for skill stuffing, impossible duration, title mismatch, stale behavior, unsupported AI claims, service-only path, pure research-only.
- Create `docs/trap_patterns.md`.

Acceptance criteria:

- Trap rules map to feature extraction logic.
- Trap rules include false-positive caution.
- Rules are testable.

Priority: P0

Depends on: Story 2.2

## Epic 3: Core Ranking Pipeline

Goal: create a valid, fast, deterministic ranker.

### Story 3.1: Project Skeleton

As an engineer, I want a clean project structure so that implementation is maintainable.

Tasks:

- Create `src/talentsignal/`.
- Add modules: `io.py`, `jd_parser.py`, `features.py`, `talent_graph.py`, `scoring.py`, `risk_audit.py`, `reasoning.py`, `ranking.py`, `validation.py`.
- Add `rank.py` CLI at repo root.
- Add `requirements.txt` or `pyproject.toml`.
- Add `tests/`.

Acceptance criteria:

- `python rank.py --help` works.
- Imports are clean.
- No network or GPU dependency required for final command.

Priority: P0

Depends on: Story 1.2

### Story 3.2: Candidate Loader

As a ranker, I want reliable candidate loading so that all 100K records are processed correctly.

Tasks:

- Implement JSONL loading.
- Support `.jsonl` and optionally `.jsonl.gz`.
- Validate required fields lightly.
- Preserve candidate ID and raw candidate object.

Acceptance criteria:

- Loader reads the provided 100K JSONL.
- Loader skips no valid rows.
- Errors include candidate ID and line number where possible.

Priority: P0

Depends on: Story 3.1

### Story 3.3: JD Parser

As a JD Strategist, I want a structured `JobSpec` so that scoring can be role-specific.

Tasks:

- Implement `JobSpec` dataclass or equivalent.
- Load `job_specs/redrob_senior_ai_engineer.yaml`.
- Add basic parser path for arbitrary JD text.
- Support required skills, preferred skills, disqualifiers, experience band, location preferences, category, scoring weights.

Acceptance criteria:

- Redrob YAML loads into a `JobSpec`.
- CLI can use Redrob default.
- General JD field exists even if v1 parser is simple.

Priority: P0

Depends on: Story 1.2, Story 3.1

### Story 3.4: Baseline Scorer

As a Match Judge, I want a first deterministic score so that we can generate a valid baseline quickly.

Tasks:

- Score title relevance.
- Score experience fit.
- Score skill overlap.
- Score location/logistics.
- Score behavioral availability.
- Score simple text similarity or keyword evidence.
- Generate top 100.

Acceptance criteria:

- `rank.py --candidates ... --out outputs/baseline_submission.csv` runs.
- Official validator passes.
- Scores are non-increasing.
- Runtime is measured.

Priority: P0

Depends on: Story 3.2, Story 3.3

## Epic 4: Candidate Evidence Intelligence

Goal: move from shallow scoring to evidence-backed ranking.

### Story 4.1: Evidence Object

As an Evidence Miner, I want each candidate represented by structured evidence so that scoring and explanations share the same facts.

Tasks:

- Define `CandidateEvidence`.
- Extract profile, career, skills, education, behavioral, logistics, and raw text fields.
- Store normalized skill names and career descriptions.
- Export evidence packets for top candidates.

Acceptance criteria:

- Every candidate has a structured evidence object.
- Evidence packet for any candidate can be printed or exported.
- Reasoning uses evidence fields, not raw hallucination.

Priority: P0

Depends on: Story 3.2

### Story 4.2: Technical Evidence Extraction

As a Match Judge, I want technical evidence signals so that real Redrob-fit candidates rank higher.

Tasks:

- Extract retrieval/search/ranking/recommendation signals.
- Extract embeddings/vector database signals.
- Extract Python/ML/LLM/fine-tuning signals.
- Extract evaluation signals: NDCG, MRR, MAP, A/B, offline eval.
- Extract production/shipping signals.
- Track whether evidence appears in career text, summary, title, or skills.

Acceptance criteria:

- Career evidence is distinguishable from skill-list evidence.
- Production evidence can boost rank.
- Skill-only evidence cannot dominate top 10 alone.

Priority: P0

Depends on: Story 4.1

### Story 4.3: Talent Graph And Synonyms

As a Talent Graph Builder, I want role and skill aliases so that plain-language good candidates are not missed.

Tasks:

- Build local dictionaries for AI/ML, retrieval, ranking, search, recommender, vector DBs, evaluation, product engineering.
- Add adjacent role mappings.
- Add category defaults for future non-AI roles.
- Keep dictionaries in code or config with comments.

Acceptance criteria:

- Search engineer, recommender engineer, backend/data engineer with retrieval evidence can be recognized.
- Exact keyword absence does not automatically remove a candidate.
- Dictionary changes are documented.

Priority: P0

Depends on: Story 4.2

### Story 4.4: Behavioral Evidence Scoring

As a recruiter, I want availability and responsiveness reflected so that shortlist quality matches hiring reality.

Tasks:

- Normalize last active date.
- Score open-to-work.
- Score recruiter response rate and response time.
- Score notice period.
- Score verification.
- Score interview completion and offer acceptance.
- Treat missing/sentinel values carefully.

Acceptance criteria:

- A perfect static profile with very poor availability is down-ranked.
- Strong technical candidates are not over-penalized for one imperfect signal.
- Sentinel values like `-1` are handled correctly.

Priority: P0

Depends on: Story 4.1

## Epic 5: Risk Audit And Trap Avoidance

Goal: avoid disqualification and weak manual review.

### Story 5.1: Suspicious Profile Rules

As a Risk Auditor, I want suspicious profile detection so that honeypot-like candidates do not enter top 100.

Tasks:

- Detect expert skills with zero or tiny duration.
- Detect many unrelated AI skills without career evidence.
- Detect non-tech title plus AI keyword stuffing.
- Detect stale and low-response profiles.
- Detect service-only path when no product evidence exists.
- Detect pure research-only signals.

Acceptance criteria:

- Risk flags are exported.
- Risk flags affect scoring.
- Top 100 has low suspicious-profile rate.

Priority: P0

Depends on: Story 2.3, Story 4.1

### Story 5.2: Risk-Aware Top-10 Policy

As a competition optimizer, I want stricter top-10 gates so that NDCG@10 and P@10 are protected.

Tasks:

- Add stricter penalties for top-10 candidates with weak career evidence.
- Add confidence score.
- Add "top-10 eligible" flag.
- Require direct Redrob JD evidence for top-10 eligibility.

Acceptance criteria:

- Top 10 has no obvious keyword stuffers.
- Every top-10 candidate has at least one strong career evidence signal.
- Manual top-10 audit passes.

Priority: P0

Depends on: Story 5.1, Story 4.2

### Story 5.3: Risk Report

As a reviewer, I want a risk report so that we can audit why risky candidates were down-ranked.

Tasks:

- Export `outputs/risk_report.csv`.
- Include candidate ID, rank, risk flags, risk penalty, and reason.
- Add summary counts by risk type.

Acceptance criteria:

- Risk report exists after ranking.
- Top-100 risk flags are easy to inspect.

Priority: P1

Depends on: Story 5.1

## Epic 6: Scoring Optimization And Manual Audit Loop

Goal: iteratively improve ranking quality with evidence, not guesses.

### Story 6.1: Factor Score Export

As a ranker tuner, I want factor scores so that ranking decisions are inspectable.

Tasks:

- Export `outputs/factor_scores.csv`.
- Include all subscores, penalties, confidence, final score, rank.
- Include key evidence counts.

Acceptance criteria:

- Every top-100 row has factor scores.
- Top candidate rank can be explained from factor scores.

Priority: P0

Depends on: Story 4.2, Story 5.1

### Story 6.2: Top-25 Audit Loop

As a competition optimizer, I want a repeatable top-25 audit loop so that the final top candidates are defensible.

Tasks:

- Generate top-25 audit file.
- Review each candidate against manual template.
- Mark keep, demote, investigate, or reject.
- Update scoring rules based on patterns, not one-off preferences.
- Log decisions.

Acceptance criteria:

- At least one complete top-25 audit exists.
- Every scoring adjustment references audit evidence.
- Top 10 passes final manual review.

Priority: P0

Depends on: Story 6.1

### Story 6.3: Candidate Comparison Tool

As a reviewer, I want side-by-side candidate comparison so that close ranking decisions are less arbitrary.

Tasks:

- Build CLI or notebook function to compare two candidate IDs.
- Show factor scores, evidence, risk flags, and reasoning.
- Use for borderline ranks 1-25 and 45-60.

Acceptance criteria:

- Two candidates can be compared in one command/function.
- Comparison supports audit decisions.

Priority: P1

Depends on: Story 6.1

## Epic 7: Reasoning And Evidence Packets

Goal: pass Stage 4 manual review and impress reviewers.

### Story 7.1: Grounded Reasoning Generator

As an Explanation Writer, I want fact-grounded reasoning so that the CSV explanations are credible.

Tasks:

- Generate reasoning from `CandidateEvidence`.
- Mention title, years, relevant evidence, logistics/behavior, and concern where useful.
- Use rank-aware tone.
- Avoid hallucinations.

Acceptance criteria:

- Every top-100 row has reasoning.
- Reasoning is 1-2 sentences.
- Reasoning references only candidate facts.

Priority: P0

Depends on: Story 4.1, Story 6.1

### Story 7.2: Explanation Validation

As a quality auditor, I want explanation checks so that hallucinated reasoning is caught.

Tasks:

- Check that mentioned skills/evidence terms exist in evidence object.
- Check repeated reasoning patterns.
- Check length and empty strings.
- Check rank-tone consistency.

Acceptance criteria:

- Explanation audit runs after ranking.
- Warnings are produced for unsupported or repetitive explanations.

Priority: P0

Depends on: Story 7.1

### Story 7.3: Evidence Packet Export

As a product reviewer, I want detailed evidence packets so that the system feels like a real talent-intelligence product.

Tasks:

- Export `outputs/evidence_packets.jsonl` for top 100.
- Include score breakdown, strengths, concerns, risk flags, and raw fact references.
- Use in demo and methodology.

Acceptance criteria:

- Top-100 evidence packet export exists.
- Packets are useful for demo and interview defense.

Priority: P1

Depends on: Story 7.1

## Epic 8: Validation, Reproducibility, And Performance

Goal: prevent disqualification.

### Story 8.1: Official Validator Integration

As a submitter, I want official validation run automatically so that format mistakes are caught.

Tasks:

- Add a command or script to run provided `validate_submission.py`.
- Document it in README.
- Include validation in final checklist.

Acceptance criteria:

- Validator passes on generated CSV.
- Failure output is easy to read.

Priority: P0

Depends on: Story 3.4

### Story 8.2: Internal Submission Validator

As an engineer, I want internal validation so that issues are caught before official validation.

Tasks:

- Check row count, ranks, candidate IDs, monotonic scores, encoding, duplicate IDs, reasoning non-empty.
- Check candidate IDs exist in loaded dataset.
- Check final output path.

Acceptance criteria:

- Internal validator catches common mistakes.
- Internal validator runs as part of ranking or audit command.

Priority: P0

Depends on: Story 3.4

### Story 8.3: Runtime And Memory Benchmark

As a Stage 3 reviewer, I want evidence that reproduction is within constraints.

Tasks:

- Measure full ranking runtime.
- Estimate or measure memory.
- Add benchmark output to `outputs/runtime_report.md`.
- Mention environment.

Acceptance criteria:

- Runtime is below 5 minutes locally.
- Memory is below 16 GB.
- Report is included in methodology.

Priority: P0

Depends on: Story 6.1

### Story 8.4: Clean Reproduction Test

As a submitter, I want a clean reproduction path so that Stage 3 does not fail.

Tasks:

- Create fresh environment.
- Install dependencies.
- Run documented command.
- Compare output hash if deterministic.
- Record commands in README.

Acceptance criteria:

- A clean reproduction run succeeds.
- README command matches actual command.
- No hidden manual steps required.

Priority: P0

Depends on: Story 8.1, Story 8.3

## Epic 9: Product Demo And Recruiter Cockpit

Goal: make the solution feel world-class and product-ready.

### Story 9.1: Demo Scope Lock

As a product builder, I want demo scope locked so that UI work does not damage core ranking work.

Tasks:

- Choose demo platform based on speed and reliability.
- Define demo input size.
- Define required views.
- Document platform choice in decision log.

Acceptance criteria:

- Demo scope is no more than needed to impress.
- Demo does not block final ranking work.

Priority: P1

Depends on: M2

### Story 9.2: Recruiter Ranking View

As a recruiter, I want to see ranked candidates so that I can inspect the shortlist.

Tasks:

- Build candidate table.
- Show rank, score, title, experience, location, top evidence, risk indicator.
- Add candidate detail expansion.

Acceptance criteria:

- Demo can rank a small sample.
- Table is readable.
- Candidate details are inspectable.

Priority: P1

Depends on: Story 7.3, Story 9.1

### Story 9.3: Evidence And Risk View

As a recruiter, I want evidence and risk flags so that I trust the ranking.

Tasks:

- Show score breakdown.
- Show strengths.
- Show concerns.
- Show risk flags.
- Show grounded reasoning.

Acceptance criteria:

- A reviewer can understand why a candidate ranked high or low.
- Risk flags are visible without overwhelming the UI.

Priority: P1

Depends on: Story 9.2

### Story 9.4: Export View

As a submitter, I want CSV export so that the demo connects to the challenge artifact.

Tasks:

- Add download button.
- Ensure exported CSV follows required columns for sample run.
- Add sample data path.

Acceptance criteria:

- Demo exports valid sample CSV.
- Export path mirrors final submission concept.

Priority: P1

Depends on: Story 9.2

## Epic 10: Documentation And Methodology

Goal: make the work defensible and impressive.

### Story 10.1: README

As a reviewer, I want clear setup and reproduction instructions.

Tasks:

- Add project overview.
- Add setup commands.
- Add final reproduction command.
- Add validation command.
- Add demo instructions.
- Add file structure.

Acceptance criteria:

- A reviewer can run the project from README alone.
- README does not overclaim.

Priority: P0

Depends on: Story 8.4

### Story 10.2: Methodology

As a judge, I want to understand the approach and why it is better than keyword matching.

Tasks:

- Write problem framing.
- Explain JD Strategist, Evidence Miner, Match Judge, Risk Auditor, Explanation Writer.
- Explain scoring components.
- Explain behavioral signals.
- Explain trap avoidance.
- Explain final constraints.
- Explain general product architecture.

Acceptance criteria:

- Methodology is concise but complete.
- It matches the code.
- It supports Stage 4 review.

Priority: P0

Depends on: Story 6.2, Story 7.3, Story 8.3

### Story 10.3: Submission Metadata

As a submitter, I want metadata complete so that portal submission is not blocked.

Tasks:

- Copy template to `submission_metadata.yaml`.
- Fill team, repo, sandbox, reproduce command, compute, AI tools, methodology summary.
- Leave no placeholder fields.

Acceptance criteria:

- Metadata is complete and consistent with portal.
- AI tool declaration is honest.

Priority: P0

Depends on: Story 10.1

## Epic 11: Interview Defense And Hiring Opportunity

Goal: convert a strong submission into career opportunities.

### Story 11.1: Architecture Defense Notes

As the project owner, I want interview notes so that I can confidently explain the system.

Tasks:

- Create `docs/interview_defense.md`.
- Add architecture walkthrough.
- Add why not live LLM in final command.
- Add scoring tradeoffs.
- Add failure modes.
- Add top candidate examples.

Acceptance criteria:

- Can explain architecture in 5 minutes.
- Can defend top-ranked candidates.
- Can explain constraints and tradeoffs.

Priority: P1

Depends on: Story 10.2

### Story 11.2: Candidate Case Studies

As a finalist, I want concrete examples so that interview answers are grounded.

Tasks:

- Select rank 1, rank 5, rank 10, rank 50, rank 100.
- Write evidence packet summaries.
- Explain why each is placed there.
- Include one down-ranked keyword-stuffer example.

Acceptance criteria:

- At least 6 case studies exist.
- Case studies match output and code.

Priority: P1

Depends on: Story 7.3

### Story 11.3: Portfolio Story

As a candidate for jobs, I want a polished story so that the project opens opportunities beyond the hackathon.

Tasks:

- Write a short project pitch.
- Write a technical summary.
- Write a recruiter-friendly summary.
- Capture screenshots of demo.
- Prepare LinkedIn/GitHub project wording without overclaiming.

Acceptance criteria:

- Story explains agentic talent intelligence clearly.
- Story avoids legal/compliance overclaims.
- Story is suitable for interviews.

Priority: P2

Depends on: Story 9.3, Story 10.2

## Epic 12: Final Submission Operations

Goal: submit safely and avoid operational mistakes.

### Story 12.1: Final Candidate Freeze

As a submitter, I want a freeze process so that late changes do not break the ranking.

Tasks:

- Freeze scoring code.
- Generate final CSV.
- Export factor scores and evidence packets.
- Run manual top-25 audit.
- Record final decision log entry.

Acceptance criteria:

- Final CSV is traceable to code version.
- Manual audit completed after final scoring change.

Priority: P0

Depends on: Story 6.2, Story 8.3

### Story 12.2: Final Validation

As a submitter, I want a final validation gate so that the submitted file is valid.

Tasks:

- Run internal validator.
- Run official validator.
- Run clean reproduction.
- Check metadata.
- Check demo link.
- Check README.

Acceptance criteria:

- Every checklist item passes.
- Final CSV hash is recorded.

Priority: P0

Depends on: Story 12.1

### Story 12.3: Submission Package

As a participant, I want a complete submission package so that portal upload is smooth.

Tasks:

- Confirm final CSV filename.
- Confirm GitHub repo URL.
- Confirm sandbox/demo link.
- Confirm metadata fields.
- Confirm AI tools declaration.
- Prepare methodology summary under portal limit.

Acceptance criteria:

- Portal-required fields are ready before upload.
- No placeholder values remain.

Priority: P0

Depends on: Story 12.2

## Suggested Work Sequence

### Day 1: Foundation And Baseline

1. Story 1.1: Challenge Brief.
2. Story 1.2: Redrob JD Scorecard.
3. Story 1.4: Manual Audit Template.
4. Story 2.1: Dataset Profiler.
5. Story 3.1: Project Skeleton.
6. Story 3.2: Candidate Loader.
7. Story 3.3: JD Parser.
8. Story 3.4: Baseline Scorer.

End of day target:

- Valid baseline CSV.
- First runtime measurement.
- First top-25 inspection.

### Day 2: Evidence And Risk

1. Story 2.2: Candidate Archetype Discovery.
2. Story 2.3: Trap Pattern Research.
3. Story 4.1: Evidence Object.
4. Story 4.2: Technical Evidence Extraction.
5. Story 4.3: Talent Graph And Synonyms.
6. Story 4.4: Behavioral Evidence Scoring.
7. Story 5.1: Suspicious Profile Rules.
8. Story 6.1: Factor Score Export.

End of day target:

- Evidence-backed ranking.
- Risk flags.
- Factor score export.

### Day 3: Ranking Quality

1. Story 5.2: Risk-Aware Top-10 Policy.
2. Story 5.3: Risk Report.
3. Story 6.2: Top-25 Audit Loop.
4. Story 6.3: Candidate Comparison Tool.
5. Tune score weights based on patterns.

End of day target:

- Top 10 is defensible.
- Top 25 audit completed.

### Day 4: Reasoning And Validation

1. Story 7.1: Grounded Reasoning Generator.
2. Story 7.2: Explanation Validation.
3. Story 7.3: Evidence Packet Export.
4. Story 8.1: Official Validator Integration.
5. Story 8.2: Internal Submission Validator.
6. Story 8.3: Runtime And Memory Benchmark.

End of day target:

- Valid, explainable top-100 CSV.
- Runtime and validation report.

### Day 5: Demo And Documentation

1. Story 9.1: Demo Scope Lock.
2. Story 9.2: Recruiter Ranking View.
3. Story 9.3: Evidence And Risk View.
4. Story 9.4: Export View.
5. Story 10.1: README.
6. Story 10.2: Methodology.

End of day target:

- Demo works on sample data.
- README and methodology draft complete.

### Day 6: Reproduction And Interview Prep

1. Story 8.4: Clean Reproduction Test.
2. Story 10.3: Submission Metadata.
3. Story 11.1: Architecture Defense Notes.
4. Story 11.2: Candidate Case Studies.
5. Story 11.3: Portfolio Story.

End of day target:

- Clean reproduction passes.
- Interview defense notes ready.

### Day 7: Final Freeze And Submit

1. Story 12.1: Final Candidate Freeze.
2. Story 12.2: Final Validation.
3. Story 12.3: Submission Package.

End of day target:

- Final validated submission package ready.

## P0 Task List

These are non-negotiable for a serious submission:

- Challenge brief.
- Redrob JD scorecard.
- Manual audit template.
- Premortem review gate.
- Dataset profiler.
- Project skeleton.
- Candidate loader.
- JD parser/config.
- Baseline scorer.
- Evidence object.
- Technical evidence extraction.
- Talent graph aliases.
- Behavioral evidence scoring.
- Suspicious profile rules.
- Risk-aware top-10 policy.
- Factor score export.
- Top-25 audit loop.
- Grounded reasoning generator.
- Explanation validation.
- Official validator integration.
- Internal submission validator.
- Runtime benchmark.
- Clean reproduction test.
- README.
- Methodology.
- Metadata.
- Final freeze.
- Final validation.
- Submission package.

## P1 Task List

These strongly improve quality and review impression:

- Decision log.
- Risk report.
- Candidate comparison tool.
- Evidence packet export.
- Demo scope lock.
- Recruiter ranking view.
- Evidence and risk demo view.
- Export view.
- Interview defense notes.
- Candidate case studies.

## P2 Task List

These support career upside and polish:

- Portfolio story.
- Additional category scorecards.
- Advanced UI polish.
- Optional embedding experiments.
- Optional agent-assisted candidate comparison outside final command.
- Optional feedback-loop simulation.

## Definition Of Done For Final Project

The project is done only when all of these are true:

- `PROJECT_COMPLETION_RULE.md` has been satisfied for every P0 story and every submitted artifact.
- Final CSV passes official validator.
- Final CSV has exactly 100 candidates.
- `rank.py` reproduces the CSV from the provided data.
- Runtime is below 5 minutes on CPU.
- No network or GPU is needed for final command.
- Top 25 has been manually audited.
- Top 10 has direct Redrob JD evidence.
- Top 100 has grounded reasoning.
- Risk flags have been reviewed.
- README is accurate.
- Methodology matches code.
- Metadata is complete.
- Demo or runnable alternative works.
- Interview defense notes exist.
- No secrets or API keys are committed.

## Immediate Next Engineering Step

Start with M0 and M1, not the UI:

1. Create `docs/challenge_brief.md`.
2. Create `job_specs/redrob_senior_ai_engineer.yaml`.
3. Create the project skeleton.
4. Implement candidate loading and a baseline scorer.
5. Generate the first valid CSV.

The first valid CSV is the turning point. After that, every improvement can be measured by inspecting actual ranked candidates.

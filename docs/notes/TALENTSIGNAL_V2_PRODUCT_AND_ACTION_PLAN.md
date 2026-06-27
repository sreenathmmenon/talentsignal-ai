# TalentSignal V2 Product And Action Plan

Date: June 16, 2026

## V2 Mission

TalentSignal V2 is a universal JD-to-hiring-decision engine.

It must work for any job description, any category, and any structured candidate/resume data. The Redrob hackathon JD is the first proof case and the highest-priority validation target because that is what the challenge will score.

The product should make one thing obvious:

> TalentSignal does not rank resumes by keywords. It converts a hiring requirement into a defensible decision system.

## Product Thesis

Most resume rankers answer only one question: "Who is first?"

TalentSignal V2 should answer the full hiring decision loop:

1. What does this JD actually require?
2. What evidence exists in each candidate profile?
3. Which candidates are strongest for this role?
4. Why is one candidate above another?
5. Which candidates are risky despite looking good?
6. What should an interviewer verify?
7. Can the result be reproduced under challenge constraints?
8. Can the same framework work for another JD?

## Non-Negotiable Balance

V2 has two equally important truths:

- Universal product: the architecture must generalize to all JDs and categories.
- Hackathon proof: the Redrob Senior AI Engineer JD must receive the strongest validation, tuning, audit, and defense.

Do not hardcode the product around one role. Do not weaken the hackathon score by chasing broad features that do not improve evidence quality, explainability, or trust.

## Product Name And Positioning

Working name: TalentSignal AI.

Positioning:

> An agentic hiring intelligence OS that turns any JD into a role scorecard, ranks candidates with inspectable evidence, audits trust, compares tradeoffs, and prepares interview validation.

Reviewer-facing phrase:

> Universal hiring intelligence engine. Redrob challenge JD is the first proof case.

## V2 Product Surface

### 1. Role Intelligence

Purpose: convert any JD into role DNA.

Capabilities:

- Parse title, seniority, category, function, domain, company stage, work mode, location, and experience expectations.
- Extract must-have skills, nice-to-have skills, disqualifiers, evaluation priorities, logistics constraints, and culture/ownership signals.
- Generate a role-specific scorecard.
- Show why each factor matters.
- Support override and versioning of scorecards.

Hackathon proof:

- Redrob Senior AI Engineer scorecard must emphasize production ML, retrieval, search, ranking, recommendation, embeddings, vector/hybrid search, Python, ranking evaluation, product shipping, logistics, activity, and trust.

### 2. Evidence Miner

Purpose: transform candidate profiles into structured evidence.

Capabilities:

- Extract career evidence from title, company, industry, tenure, descriptions, and achievements.
- Extract skill evidence from listed skills, duration, proficiency, endorsements, assessments, and project context.
- Extract behavioral evidence from activity, open-to-work, response rate, notice period, verification, interview completion, saved-by-recruiter, and offer acceptance signals.
- Extract logistics evidence from location, country, relocation, work mode, and notice period.
- Extract risk evidence from stale profiles, keyword stuffing, shallow AI mentions, title mismatch, inflated skills, missing production proof, and irrelevant domain focus.

Output:

- One evidence packet per candidate.
- Evidence fields must be fact-grounded and inspectable.

### 3. Universal Scorecard Engine

Purpose: score candidates for any JD through configurable factors.

Core factor families:

- Role/domain fit.
- Technical or functional evidence.
- Career trajectory and seniority.
- Production or execution proof.
- Logistics fit.
- Behavioral availability.
- Trust and risk.
- Semantic/textual fit.

Category-specific examples:

- AI/ML: production ML, retrieval/ranking, embeddings, Python, evaluation, deployment.
- Backend engineering: distributed systems, APIs, databases, scale, reliability, ownership.
- Sales: ICP fit, quota history, region, enterprise/mid-market motion, CRM discipline.
- Product: domain judgment, launch evidence, discovery, analytics, cross-functional leadership.
- Design: portfolio evidence, product thinking, systems design, collaboration, usability validation.
- Operations: process ownership, metrics, compliance, stakeholder execution.

Hackathon proof:

- The Redrob scorecard is one generated/curated scorecard instance, not a hardcoded product identity.

### 4. Ranking And Boundary Review

Purpose: produce a defensible ordered shortlist.

Capabilities:

- Top-N ranking with deterministic tie-breaks.
- Rank boundary analysis for #8-#12, #20-#30, #90-#110.
- Candidate movement report after weight changes.
- Precision-first top-10 policy.
- Conservative ranking when evidence is weak.

Hackathon proof:

- Final top 100 must pass validator.
- Top 10 must be manually audited.
- #10 vs #11 and #100 vs #101 must be defensible.

### 5. Compare Mode

Purpose: explain why one candidate outranks another.

Capabilities:

- Compare any two candidates.
- Show factor deltas.
- Show strongest evidence for each.
- Show weakest evidence for each.
- Show risk/trust tradeoffs.
- Generate a short hiring recommendation.

High-value comparisons:

- #1 vs #2.
- #5 vs #6.
- #10 vs #11.
- #25 vs #26.
- #100 vs #101.

### 6. Trust And Trap Detector

Purpose: prevent impressive-looking but weak candidates from ranking too high.

Capabilities:

- Keyword-stuffing detection.
- Shallow AI/API demo detection.
- Stale availability detection.
- Research-only-without-production detection.
- Service-only mismatch detection when product ownership is required.
- Irrelevant AI-domain detection when the role needs a specific domain.
- Weak evidence confidence scoring.
- Rejected-trap examples for demo and defense.

Hackathon proof:

- Show candidates that looked good lexically but were rejected or down-ranked.
- Explain why the product resists honeypots.

### 7. Interview Kit

Purpose: connect ranking to real hiring workflow.

Capabilities:

- Generate candidate-specific interview probes.
- Include technical/functional validation questions.
- Include evidence verification questions.
- Include risk-check questions.
- Include final interviewer decision rubric.

Rule:

- Questions must be grounded in the candidate evidence packet and JD scorecard. Avoid generic interview questions.

### 8. Judge Demo Mode

Purpose: create a sharp, 3-5 minute product story.

Flow:

1. Load JD.
2. Show Role Intelligence.
3. Run ranking.
4. Show top candidate evidence.
5. Compare #10 vs #11.
6. Show a rejected trap candidate.
7. Generate interview kit.
8. Export CSV and evidence reports.

The demo should make the reviewer feel the product is bigger than the challenge, while every screen still supports the challenge outcome.

### 9. Reproducible Challenge Package

Purpose: meet official rules and survive evaluation.

Requirements:

- CPU-only.
- No network calls.
- No hosted LLM/API dependency.
- No GPU.
- Under runtime and memory limits.
- Deterministic output.
- Valid CSV.
- Clean README, methodology, metadata, and defense notes.

## V2 Architecture

### Core Runtime

- `rank.py`: final offline challenge command.
- `src/talentsignal/jd_parser.py`: JD scorecard loading and future JD parsing.
- `src/talentsignal/features.py`: candidate evidence extraction.
- `src/talentsignal/scoring.py`: score components and penalties.
- `src/talentsignal/ranking.py`: ranking pipeline and export writers.
- `src/talentsignal/risk_audit.py`: trust and trap checks.
- `src/talentsignal/reasoning.py`: grounded explanations.
- `src/talentsignal/talent_graph.py`: cross-candidate and evidence structure.
- `app.py`: live recruiter cockpit and REST API.

### V2 Additions

Add or extend:

- `src/talentsignal/scorecard_generator.py`: convert parsed JD intent into factor weights and scoring priorities.
- `src/talentsignal/category_taxonomy.py`: category defaults for AI/ML, engineering, sales, product, design, operations, data, finance, support, and marketing.
- `src/talentsignal/boundary_review.py`: produce #10/#11 and #100/#101 review packets.
- `src/talentsignal/candidate_compare.py`: compare two candidates through score deltas and evidence.
- `src/talentsignal/interview_kit.py`: grounded interview probes.
- `src/talentsignal/trap_detector.py`: down-ranked trap and honeypot examples.
- `job_specs/examples/`: example JDs across categories for generality demos.

## V2 Execution Plan

### Phase 1: Universal JD Foundation

Goal: prove the product is not one-JD hardcoded.

Tasks:

- Define a category taxonomy with default scoring priorities.
- Add 5-8 example job specs across categories.
- Add a scorecard-generation interface that can load a YAML scorecard today and later parse raw JD text.
- Add tests proving multiple job specs load and produce valid factor structures.
- Update UI Role Intelligence to clearly show "role-specific scorecard".

Acceptance criteria:

- At least 5 non-Redrob job specs exist.
- The ranker can accept any valid job spec path.
- The UI displays role intelligence without Redrob-specific copy.
- Redrob job spec remains the primary default.

### Phase 2: Evidence Quality Upgrade

Goal: improve ranking quality through richer candidate facts.

Tasks:

- Audit evidence extraction fields against candidate schema.
- Add stronger career-description evidence extraction.
- Add skill duration/proficiency/endorsement normalization.
- Add behavioral signal normalization.
- Add evidence confidence scoring.
- Add missing-evidence penalties for top ranks.

Acceptance criteria:

- Evidence packets explain the top 25 with concrete facts.
- Top 10 candidates have career evidence, not only skill-list evidence.
- Low-confidence candidates are visible and penalized appropriately.

### Phase 3: Challenge Ranking Improvement

Goal: make the Redrob hackathon ranking stronger.

Tasks:

- Re-audit top 25 manually.
- Review #26-#75 for missed strong candidates.
- Generate #8-#12 and #90-#110 boundary reviews.
- Tune weights only when the evidence supports it.
- Add trap penalties based on observed bad candidates.
- Run validator and internal audits after every scoring change.

Acceptance criteria:

- Top 10 has no obvious weak, stale, irrelevant, or keyword-stuffed candidate.
- #10 beats #11 for documented reasons.
- #100 beats #101 for documented reasons.
- Final CSV remains valid and reproducible.

### Phase 4: Trust And Trap Productization

Goal: make our anti-honeypot work visible.

Tasks:

- Generate a rejected-trap report.
- Add UI panel for "Looked good, rejected because..." examples.
- Add risk distribution dashboard.
- Add reason codes for trap penalties.
- Add tests for known trap scenarios.

Acceptance criteria:

- UI shows at least 3 rejected or down-ranked trap examples from real data.
- Each example has evidence and a clear rejection reason.
- Trust layer is connected to actual score/risk data.

### Phase 5: Compare And Boundary Review

Goal: prove ranking tradeoffs are intentional.

Tasks:

- Add API endpoint or response section for candidate comparison.
- Add compare controls in UI.
- Add prebuilt boundary comparisons.
- Add factor delta visualization.
- Add "why above / why below" explanation.

Acceptance criteria:

- User can compare any two visible candidates.
- #10 vs #11 and #100 vs #101 are available.
- Compare text is grounded in evidence and score factors.

### Phase 6: Interview Kit

Goal: show real recruiter workflow value after ranking.

Tasks:

- Build candidate-specific interview kit generator.
- Include technical/functional, evidence validation, risk validation, and logistics questions.
- Add final interviewer scoring rubric.
- Add UI export/copy support.

Acceptance criteria:

- Selecting any top candidate updates the interview kit.
- Questions cite candidate evidence or weak areas.
- No generic-only question sets.

### Phase 7: Judge Demo Mode

Goal: create the winning walkthrough.

Tasks:

- Add a guided demo route or panel.
- Add step indicators for Role Intelligence -> Ranking -> Evidence -> Compare -> Trust -> Interview -> Export.
- Add concise product copy around each step.
- Keep the main UI operational, not a fake presentation.

Acceptance criteria:

- Demo can be completed in 3-5 minutes.
- Every step uses live or generated project data.
- Playwright validates the demo path.

### Phase 8: Final Hardening

Goal: make the project defensible.

Tasks:

- Run full backend tests.
- Run Playwright desktop and mobile.
- Run official validator.
- Run runtime measurement.
- Rebuild outputs.
- Update README, methodology, metadata, final checklist, and interview defense.
- Confirm no forbidden dependencies in final command.
- Confirm no accidental commits/pushes without explicit ask.

Acceptance criteria:

- All required validations pass.
- Screenshots are current.
- Final docs match actual behavior.
- No known critical issue remains.

## V2 Product Metrics

### Hackathon Metrics

- Valid top-100 CSV.
- Runtime under official limit.
- Memory under official limit.
- Top-10 manual confidence.
- Boundary defensibility.
- Trap rejection quality.
- Explanation grounding quality.

### Product Metrics

- Number of JD categories supported.
- Time from JD to shortlist.
- Evidence coverage per candidate.
- Candidate comparison clarity.
- Risk review usefulness.
- Interview kit specificity.
- Demo completion time.

## What We Must Avoid

- Redrob-only hardcoding disguised as a universal product.
- Generic UI features that do not improve ranking, trust, comparison, or interview workflow.
- Claims of "agentic AI" without clear agent-like responsibilities.
- External API dependency in the final ranking command.
- Theme/design-system copy that pollutes our product language.
- Overfitting to visible examples while ignoring general scorecard architecture.
- Calling V2 complete before backend, REST, UI, real data, and screenshots are all validated.

## Immediate Next Actions

Council review on June 16, 2026 and Redrob big-bet research on June 17, 2026 supersede the older next-action order. See `COUNCIL_REVIEW_JUNE_16_2026.md` and `REDROB_RESEARCH_AND_BIG_BET_STRATEGY_JUNE_17_2026.md`.

1. Fix token/phrase matching false positives.
2. Regenerate stale artifacts from the current final CSV.
3. Add baseline comparison against keyword/BM25-style ranking.
4. Add top-25 raw-profile audit and #90-#110 boundary defense.
5. Vendor or inline the selected Helix CSS before any external judging/demo.
6. Tighten claims from "autonomous universal hiring OS" to evidence-based hiring decision support.
7. Add scorecard-generation abstraction while preserving current YAML path.
8. Add compliance/audit roadmap artifacts for responsible hiring use.

## Definition Of V2 Success

V2 succeeds when a judge can see both of these clearly:

1. This system is strong enough to compete on the Redrob hackathon ranking.
2. This framework could become a real Redrob-style hiring intelligence product for many roles, categories, and hiring workflows.

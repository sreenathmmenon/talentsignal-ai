# World-Class Execution Plan

## Mission

Build the best possible Redrob hackathon submission and a credible hiring-intelligence product. The immediate goal is to win the Redrob challenge. The broader goal is to create a product-quality system that can rank candidates for many job descriptions and become a strong portfolio piece for hiring opportunities.

This is not a plan for a keyword matcher. This is a plan for an evidence-based candidate intelligence system.

## Strategic Thesis

The winning system should do five things well:

1. Understand the JD better than shallow keyword systems.
2. Extract trustworthy evidence from candidate profiles.
3. Rank conservatively for top-10 precision.
4. Explain every decision with grounded facts.
5. Prove reproducibility, product thinking, and engineering maturity.

The Redrob Senior AI Engineer JD is the first-priority benchmark. The architecture should still support other JDs and categories by separating JD parsing, evidence extraction, scoring rubrics, and product presentation.

After agentic AI market research, the product framing should be stronger: this is not only a ranker, it is a compact agentic talent intelligence workflow. The internal modules should behave like a JD Strategist, Evidence Miner, Talent Graph Builder, Match Judge, Risk Auditor, Explanation Writer, and Recruiter Cockpit. The final Redrob submission compiles that workflow into a deterministic offline command.

## Product We Will Build

Working name: `TalentSignal Ranker`.

Core product promise:

> Given a job description and a candidate pool, produce a ranked shortlist with evidence-backed explanations, risk flags, and recruiter-ready reasoning.

Hackathon output:

- A valid top-100 CSV for the provided Redrob JD.
- A reproducible offline ranking command.
- A methodology document that explains the architecture clearly.
- A demo that shows the system can rank a small candidate set for a JD.
- A repo that looks engineered, not assembled at the last minute.

Broader product output:

- JD parser.
- Candidate evidence extractor.
- Configurable scoring rubric.
- Ranking engine.
- Explainability engine.
- Quality and risk audit layer.
- Demo UI.

## System Architecture

### 1. JD Intelligence Layer

Purpose: convert a raw JD into structured hiring intent.

For the Redrob JD, extract:

- Role: Senior AI Engineer, founding team.
- Domain: AI-native talent intelligence, ranking, retrieval, candidate matching.
- Must-have signals: production ML systems, embeddings, retrieval, vector/hybrid search, Python, ranking evaluation, product shipping.
- Nice-to-have signals: LLM fine-tuning, learning-to-rank, HR-tech, marketplace products, distributed systems, open-source validation.
- Disqualifiers: pure research only, shallow LangChain/API demos, no recent production coding, service-only background without product evidence, irrelevant CV/speech/robotics focus.
- Logistics: India, Pune/Noida preferred, relocation acceptable, 5-9 years preferred but flexible.
- Culture: written communication, speed, product judgment, ownership, disagreement tolerance.

For general product use:

- Parse role, seniority, category, required skills, preferred skills, disqualifiers, geography, work mode, experience band, domain, company stage, and evaluation priorities.
- Support a default rubric by category: AI/ML, software engineering, data, product, sales, marketing, operations, finance, support, design.
- Allow explicit rubric overrides for a specific JD.

### 2. Candidate Evidence Layer

Purpose: convert each profile into defensible evidence.

Extract:

- Identity fields: candidate ID, title, location, country, years of experience.
- Career evidence: titles, companies, industries, current role, tenure, descriptions, production language.
- Skill evidence: skill names, proficiency, endorsements, duration, assessment scores.
- Education evidence: degree, field, institution tier when available.
- Behavioral evidence: activity, open-to-work, response rate, response time, notice period, verification, interview completion, offer acceptance, recruiter saves.
- Risk evidence: suspicious skills, stale activity, title mismatch, service-only path, impossible claims, keyword stuffing, weak production evidence.

Design principle: score what the candidate has done, not only what the candidate lists.

### 3. Retrieval And Candidate Generation

Purpose: identify a high-quality candidate subset before final scoring.

Use multiple retrieval channels:

- Structured filters: experience band, country/location fit, current/recent relevant titles.
- Lexical retrieval: TF-IDF over summary, headline, skills, and career descriptions.
- Evidence keyword retrieval: retrieval, ranking, search, recommender, embeddings, vector DB, evaluation, Python, production.
- Anti-keyword-stuffing retrieval: require career-description evidence for top-tier candidates, not just skill-list matches.
- Behavioral retrieval: active, responsive, verified candidates with reasonable notice period.

Competition priority:

- Recall enough strong candidates for top 100.
- Top 10 should be conservative and heavily evidence-backed.

### 4. Scoring Engine

Purpose: combine evidence into a transparent ranking score.

Recommended scoring families:

- JD core fit: role, domain, technical relevance.
- Production ML evidence: shipped systems, ranking/retrieval/search/recommendation, production language.
- Skills depth: relevant skills with duration, proficiency, assessment scores, endorsements.
- Seniority fit: years of experience and role maturity.
- Product/company fit: product-company, startup, marketplace, HR-tech, ownership signals.
- Logistics fit: India, target cities, relocation, work mode, notice period.
- Behavioral availability: recent activity, open-to-work, response rate, verification, recruiter interest.
- Trust/risk: suspicious patterns, stale profile, irrelevant title, keyword stuffing, impossible claims.

The final score should be deterministic and explainable. Every major score component should be inspectable.

### 5. Ranking Policy

Purpose: optimize hidden challenge metrics.

Policy:

- Top 10: precision-first, high-confidence only.
- Top 50: strong relevance with some adjacent candidates.
- Ranks 51-100: broader fit, but avoid traps.
- Penalize uncertainty more strongly in top 10.
- Prefer candidates with career evidence over candidates with only skill-list evidence.
- Use deterministic tie-breaks.

Manual audit policy:

- Inspect top 25 deeply before final submission.
- Inspect candidates ranked 26-60 for obvious missed top-10 candidates.
- Inspect 20 random candidates from 61-100 for hallucinated reasoning or trap patterns.

### 6. Explainability Engine

Purpose: produce grounded, reviewer-friendly reasoning.

Reasoning must:

- Mention facts present in the profile.
- Connect those facts to JD requirements.
- Acknowledge concerns when relevant.
- Match the rank confidence.
- Avoid generic copy-paste language.

Reasoning template style:

- Top 10: strong, specific, confident, evidence-rich.
- Middle ranks: balanced, with one clear concern if applicable.
- Lower ranks: honest about fit limitations.

Example structure:

> "6.8-year ML engineer with career evidence around retrieval/ranking systems and Python production work; location and recent activity are favorable. Minor concern: notice period is longer than ideal."

### 7. Quality Audit Layer

Purpose: prevent disqualification and manual-review failure.

Audits:

- CSV shape and validator pass.
- Candidate IDs exist in dataset.
- No duplicate ranks or candidates.
- Scores non-increasing.
- Reasoning uses only extracted facts.
- No top-100 honeypot-like profiles.
- Runtime within challenge limit.
- Memory within challenge limit.
- No network dependency in final ranking command.
- Top-25 manual audit checklist completed.

### 8. Demo/Product Layer

Purpose: impress reviewers and support hiring conversations.

The demo should show:

- Upload or select a JD.
- Upload or select candidates.
- Run ranking.
- View ranked candidates.
- See score breakdown.
- See grounded explanation.
- See risk flags.
- Download CSV.

Use whichever platform best supports speed and reliability: Streamlit, custom web app, Docker, Colab, or another option. The platform is not the point. The product story is the point.

## Step-By-Step Build Plan

### Phase 0: Ground Truth And Challenge Command Center

1. Convert the challenge `.docx` and PDF docs into readable markdown notes.
2. Create `docs/challenge_brief.md` with rules, scoring, constraints, and submission checklist.
3. Create `docs/jd_analysis_redrob_senior_ai_engineer.md` with extracted JD intent.
4. Create `docs/decision_log.md` to track scoring and architecture choices.
5. Create `docs/manual_audit_template.md` for top-candidate review.

Done when:

- Every challenge rule is visible in markdown.
- The final submission checklist is explicit.
- We can explain the JD in 2 minutes without reading the original doc.

### Phase 1: Data Profiling

1. Build a read-only profiling script for the 100K JSONL.
2. Count titles, industries, countries, locations, experience bands, skills, companies, and behavioral distributions.
3. Identify candidate archetypes: strong AI, adjacent AI, keyword stuffer, stale candidate, service-only, pure research, non-tech with AI keywords.
4. Find likely honeypot patterns.
5. Generate profile summary stats for methodology.

Done when:

- We understand candidate distribution.
- We know which traps are common.
- We can justify scoring thresholds with dataset evidence.

### Phase 2: Baseline Ranker

1. Implement candidate loader.
2. Implement text normalization.
3. Build candidate text fields: profile text, career text, skill text, all text.
4. Implement TF-IDF similarity to the Redrob JD.
5. Implement first structured score using title, skills, experience, location, and behavior.
6. Produce first top-100 CSV.
7. Run the provided validator.

Done when:

- A valid baseline CSV exists.
- Runtime is measured.
- Top 25 has been manually inspected at least once.

### Phase 3: Evidence Extraction

1. Extract production evidence phrases.
2. Extract retrieval/ranking/search/recommendation evidence.
3. Extract vector database and embedding evidence.
4. Extract evaluation evidence: NDCG, MRR, MAP, A/B tests, offline metrics.
5. Extract product-company/startup evidence.
6. Extract service-only career evidence.
7. Extract irrelevant-domain evidence.
8. Extract AI-keyword-stuffing signals.
9. Extract behavioral availability features.
10. Extract location and relocation fit.

Done when:

- Each candidate has a structured evidence object.
- Evidence is available for scoring and reasoning.
- Top-candidate explanations can be generated from facts only.

### Phase 4: Redrob-Specific Scoring Rubric

1. Implement score components with named subscores.
2. Tune top-10 precision first.
3. Make production career evidence outweigh skill-list keyword matches.
4. Add hard penalties for suspicious and irrelevant profiles.
5. Add soft penalties for stale/low-response candidates.
6. Add location/logistics bonuses without overpowering technical fit.
7. Add confidence score separate from fit score.
8. Keep score deterministic.

Done when:

- Top 10 looks like real Senior AI Engineer candidates.
- Obvious keyword stuffers are absent from top 100.
- Every high-ranked candidate has career evidence, not only skills.

### Phase 5: General JD Engine

1. Create `jd_parser.py`.
2. Encode the Redrob JD as a structured `JobSpec`.
3. Add generic fields: role, category, seniority, must-have skills, nice-to-have skills, disqualifiers, location, work mode, experience band, behavioral preferences.
4. Add category-level default rubrics.
5. Allow command-line input for a JD file.
6. Keep Redrob structured spec as the default competition config.

Done when:

- The ranker can technically accept another JD.
- The Redrob config remains optimized for the challenge.
- The methodology can honestly claim general-product architecture.

### Phase 6: Reasoning Generator

1. Build explanation snippets from extracted facts.
2. Add rank-aware tone.
3. Add concern snippets for weaker matches.
4. Prevent hallucinations by only using evidence fields.
5. Add variation across reason strings.
6. Add tests to ensure mentioned skills appear in candidate evidence.

Done when:

- Top 100 has specific, varied explanations.
- Manual review sample should pass fact-grounding.
- No explanation is generic filler.

### Phase 7: Validation And Premortem-Driven Hardening

1. Run official validator.
2. Run internal validation.
3. Run runtime test.
4. Run no-network dependency check.
5. Run top-25 manual audit.
6. Run suspicious-profile audit.
7. Run explanation audit.
8. Run reproducibility on a clean environment.

Done when:

- We can reproduce the same CSV from a clean command.
- The top 25 survives manual scrutiny.
- The repo can be defended.

### Phase 8: Product Demo

1. Build a small-sample demo.
2. Show JD input.
3. Show candidate ranking table.
4. Show score breakdown.
5. Show explanation and risk flags.
6. Add CSV download.
7. Add a short product README.

Done when:

- A reviewer can understand the product in 2 minutes.
- The demo supports the broader product story.
- The demo does not compromise final reproducibility.

### Phase 9: Methodology And Story

1. Write `methodology.md`.
2. Explain why keyword matching fails.
3. Explain evidence-based ranking.
4. Explain behavioral signals.
5. Explain trap avoidance.
6. Explain CPU/runtime design.
7. Explain general JD architecture.
8. Explain manual audit and quality process.

Done when:

- The methodology is clear to an engineer and a recruiter.
- It feels like a real product team built it.
- It can support a 30-minute interview defense.

### Phase 10: Final Submission Readiness

1. Freeze scoring code.
2. Generate final CSV.
3. Validate CSV.
4. Reproduce from scratch.
5. Commit final code and docs.
6. Fill metadata.
7. Check demo link.
8. Prepare interview notes.
9. Submit only after a final top-25 audit.

Done when:

- Submission is valid.
- Repo is reproducible.
- Top candidates are defensible.
- We can explain every major design decision.

## What Will Make It World-Class

1. It is visibly not a keyword matcher.
2. It separates JD understanding from candidate scoring.
3. It uses structured evidence and text evidence together.
4. It ranks by real career proof.
5. It uses behavioral hiring signals intelligently.
6. It flags suspicious candidates.
7. It explains decisions with facts.
8. It is deterministic and reproducible.
9. It has a clean product demo.
10. It can generalize beyond the one JD.
11. It has a strong methodology document.
12. It has tests and validation.
13. It has believable git history.
14. It can be defended in interview.
15. It shows hiring-domain understanding, not just ML knowledge.

## Operating Rules

- Redrob JD performance comes first.
- General product architecture comes second.
- Do not overbuild at the cost of top-10 quality.
- Do not let AI-generated text hallucinate facts.
- Do not submit a CSV that has not passed the official validator.
- Do not trust a score until top candidates are manually inspected.
- Do not add dependencies that make reproduction fragile.
- Do not hide manual decisions; document them.
- Do not pretend the system is perfect; explain tradeoffs honestly.
- Do not confuse development freedom with final reproduction constraints.

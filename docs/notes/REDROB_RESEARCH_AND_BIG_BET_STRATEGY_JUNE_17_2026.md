# Redrob Research And Big Bet Strategy

Date: June 17, 2026

## Why This Document Exists

Sreenath was not impressed with the current direction. That criticism is valid.

TalentSignal V2 is stronger than a plain resume ranker, but it still thinks too much like a challenge solution. Redrob's public product direction is bigger: a unified AI execution system built on people data, company data, job data, language, enrichment, assessments, workflows, and low-cost model infrastructure.

The next version must align with that larger Redrob strategy.

## Fresh Redrob Research Signals

Public Redrob pages indicate several strong strategic themes:

1. Redrob is not only a recruiting product. It presents itself as "India's AI for the Next Billion Professionals" built on 700M+ profiles, 30+ languages, and real data powering hiring, sales, jobs, and research in one system.
2. Redrob's platform promise is unification: "Everything You Do Now Handled in One AI System."
3. Redrob HR is positioned as hiring software to find, verify, evaluate, and hire talent globally with accurate data, sourcing, and response-rate improvement.
4. Redrob HR says hiring is built on verified talent data, real-time candidate intelligence, and search across 700M+ profiles using role, skills, experience, and hiring signals, not just keywords.
5. Redrob's HR workflow is: describe role in plain English, discover candidates, enrich profiles and contacts, shortlist with AI, and push to hiring workflow.
6. Redrob People Search emphasizes natural-language intent search over Boolean filters and claims the system maps intent to profiles, company signals, tenure filters, and seniority classifiers.
7. Redrob API emphasizes 20+ data sources, enrichment, people search, company search, verified contact data, role/hierarchy mapping, hiring/growth signals, market/intent signals, async processing, and production-ready integration.
8. Redrob's ecosystem includes HR, GTM, API, campuses, resume builder, skill tests, interview coach, skills leaderboard, Redrob Code, market pulse, and research.

Sources:

- https://redrob.io/
- https://redrob.io/hr
- https://redrob.io/people-search
- https://redrob.io/gtm/api

## What This Means

Our current product is still centered on:

- job scorecard,
- candidate ranking,
- evidence packet,
- compare mode,
- interview kit,
- exports.

That is useful, but not big enough.

Redrob appears to be building an AI-native professional-work graph:

- people,
- companies,
- jobs,
- skills,
- contacts,
- hiring signals,
- work activity,
- assessments,
- documents,
- communication,
- scheduling,
- research,
- workflow execution.

Therefore, the winning product idea should not be "a better resume ranker."

It should be:

> A Talent Decision Graph layer for Redrob that turns people search, company intelligence, job requirements, assessments, and recruiter feedback into a defensible hiring mission.

## New Big Bet

Name:

> TalentSignal Mission Control

Positioning:

> The decision and verification layer for Redrob's hiring graph.

One-line product:

> Convert any hiring requirement into a live talent mission: market map, candidate discovery, evidence ranking, verification plan, interview loop, outreach strategy, and learning feedback.

Why this is bigger:

- It uses Redrob's people search as discovery.
- It uses Redrob's company search as context.
- It uses Redrob's job search as market calibration.
- It uses Redrob's enrichment/API layer for verification and reachability.
- It uses Redrob's assessments/interview coach as validation.
- It uses Redrob's multilingual/next-billion positioning for global and India-first hiring.
- It turns the hackathon ranker into one module inside a full talent intelligence loop.

## Product Architecture: Talent Mission Loop

### 1. Role Mission Intake

Input:

- raw JD,
- hiring manager notes,
- company context,
- target location,
- compensation/level constraints,
- urgency,
- must-have vs trainable signals.

Output:

- role mission brief,
- scorecard,
- ambiguity flags,
- required evidence,
- search strategy,
- interview validation plan.

Why it matters:

Redrob says users can describe the role in plain English. TalentSignal should not merely load YAML. It should show how plain English becomes a role mission.

### 2. Market Map

Input:

- role mission,
- target geography,
- candidate pool,
- company search / job market signals.

Output:

- available talent clusters,
- target companies,
- seniority supply,
- location supply,
- compensation/notice-risk assumptions,
- likely sourcing difficulty.

Why it matters:

This makes us bigger than ranking. It tells recruiters whether the role is feasible and where talent likely lives.

### 3. Discovery Strategy

Input:

- role mission,
- market map.

Output:

- natural-language search prompts,
- Boolean fallback queries,
- company-source targets,
- adjacent-role expansion,
- diversity-of-sourcing checks,
- passive-candidate strategy.

Why it matters:

Redrob People Search emphasizes natural-language intent search. TalentSignal should generate and audit the search strategy, not only rank what is already provided.

### 4. Evidence Ranker

Input:

- candidate pool,
- role mission,
- source/enrichment fields.

Output:

- ranked shortlist,
- fit bands,
- evidence packets,
- why higher/lower,
- boundary review,
- missing evidence,
- contradiction flags.

Why it matters:

This is where the current hackathon ranker fits. It remains critical, but it becomes the decision engine inside a larger mission.

### 5. Verification Layer

Input:

- ranked candidate evidence,
- risk/missing-evidence findings.

Output:

- what to verify,
- how to verify,
- interview questions,
- skill test recommendation,
- reference/enrichment needs,
- candidate-specific proof checklist.

Why it matters:

Hiring products fail when ranking becomes unsupported judgment. Verification is the trust layer.

### 6. Outreach And Conversion Strategy

Input:

- candidate evidence,
- market map,
- reachability/enrichment,
- candidate motivation signals.

Output:

- personalized outreach angle,
- likely objections,
- recruiter talking points,
- response probability band,
- follow-up sequence.

Why it matters:

Redrob emphasizes verified contacts, faster outreach, and higher response rates. TalentSignal should improve response quality, not just candidate order.

### 7. Interview And Assessment Loop

Input:

- candidate-specific evidence and verification plan.

Output:

- interview panel plan,
- competency rubric,
- expected strong/weak answer signals,
- skill-test recommendation,
- post-interview evidence update.

Why it matters:

Redrob's ecosystem includes skill tests and interview coach. TalentSignal should connect ranking to validation.

### 8. Hiring Decision Memo

Input:

- scorecard,
- ranking,
- interview results,
- verification status,
- recruiter/hiring manager notes.

Output:

- decision memo,
- hire/no-hire rationale,
- risk acceptance,
- compensation/notice plan,
- audit trail.

Why it matters:

This is the artifact a hiring manager can actually use.

### 9. Learning Feedback

Input:

- recruiter feedback,
- interview outcomes,
- offer outcome,
- joining outcome,
- later performance signals if available.

Output:

- scorecard calibration,
- source strategy adjustment,
- evidence-weight updates,
- future mission learnings.

Why it matters:

Without feedback, the system is only a ranker. With feedback, it becomes an operating system.

## Hackathon Translation

The hackathon only requires a ranking system. But our story should be:

> This challenge is one slice of Talent Mission Control: the Evidence Ranker and Verification Layer.

Demo flow for the hackathon:

1. Start with the Redrob role mission.
2. Show the role scorecard.
3. Show why keyword search fails.
4. Show evidence-ranked top candidates.
5. Show #10 vs #11 and #100 vs #101.
6. Show rejected traps.
7. Show verification questions and interview plan.
8. Show how this would plug into Redrob people search, enrichment, skill tests, interview coach, and hiring workflow.

## What We Must Build Next To Become Impressive

The next leap is not more cards in the same UI. The next leap is a mission workflow.

### P0: Fix Current Trust Issues

- Token/phrase-aware matching.
- Dangerous short-term safeguards.
- Regenerate stale artifacts.
- Baseline comparison.
- Top-25 and boundary raw-profile audit.
- Vendor/integrate Helix CSS for reproducible external demo.

### P1: Build Role Mission Intake

- Raw JD paste box.
- Extracted scorecard preview.
- Must-have/trainable/nice-to-have/disqualifier split.
- Ambiguity flags.
- Hiring manager approval state.

### P1: Build Market Map Panel

- Candidate pool distribution by location, title, years, company type, evidence cluster.
- "Is this role feasible?" signal.
- Where strong candidates cluster.
- Which constraints are shrinking the pool.

### P1: Build Discovery Strategy Panel

- Search prompts Redrob People Search could run.
- Company-source targets.
- Adjacent-role expansion suggestions.
- Passive-candidate strategy.

### P1: Build Verification Plan

- Missing evidence by candidate.
- What to verify before interview.
- Which skill test or interview probe validates each risk.
- Expected strong/weak answer indicators.

### P2: Build Outreach Strategy

- Candidate motivation hypothesis.
- Personalized outreach line.
- Response-risk band.
- Follow-up sequence.

### P2: Build Hiring Decision Memo

- One-page memo for hiring manager.
- Final recommendation.
- Top risks.
- Interview plan.
- Boundary rationale.
- Export as markdown/PDF later.

## Product Claim Going Forward

Use:

> TalentSignal Mission Control turns a hiring requirement into a complete talent mission: role intelligence, market map, evidence ranking, verification, interview plan, and decision memo.

For hackathon:

> The submitted ranker is the deterministic Evidence Ranker inside TalentSignal Mission Control.

Avoid:

> We are only a resume ranker.

Avoid:

> We are already a fully autonomous hiring OS.

## Why This Can Impress Redrob

This direction speaks to Redrob's own public strategy:

- Redrob has people search; we add mission-level search strategy and decision validation.
- Redrob has verified contacts; we add outreach reasoning and conversion risk.
- Redrob has company search; we add target-company and talent-market mapping.
- Redrob has skill tests/interview coach; we add evidence-grounded verification plans.
- Redrob has APIs; we design an orchestration layer that could call those APIs.
- Redrob is building for next-billion professionals; we design multilingual, India-aware, region-aware hiring missions.

The product becomes a roadmap idea, not only a challenge submission.

## Immediate Rewrite Of Our Mental Model

Old:

> Candidate ranker plus UI.

Better:

> Evidence-based hiring decision support.

Best:

> Talent mission control for Redrob's hiring graph.


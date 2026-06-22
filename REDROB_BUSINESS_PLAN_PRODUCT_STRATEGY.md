# Redrob Business Plan Signal And Product Strategy

Date: June 15, 2026

## What The Business Plan Access Signals

The hackathon plan screenshot shows a Redrob/India Runs promo plan with high-value platform access, including:

- 2M daily token budget.
- 1,000 enrichment credits per month.
- 790M+ people search records.
- 59M+ company search records.
- 20M+ active jobs.
- Up to 50 mock interview assessments per day.
- Up to 10 image generations per day.
- Up to 10 deep researches per day.
- Resume Ranker.

This is not a small coding-contest signal. It suggests Redrob wants participants to think in product frameworks that can influence their roadmap across candidate discovery, enrichment, matching, assessment, and recruiter workflow.

## Strategic Implication

The minimum challenge output is a ranked top-100 CSV. That is necessary, but it is not enough to stand out.

The winning product should show how a recruiter or hiring team moves from a job description to an evidence-backed decision:

1. Understand the role.
2. Discover or ingest candidates.
3. Rank by a role-specific scorecard.
4. Explain why the best candidates are best.
5. Compare top candidates.
6. Flag weak evidence, stale profiles, risky keyword stuffing, and logistics risk.
7. Generate interview probes that validate the ranking.
8. Export the required challenge artifact and reviewer evidence.

## Product Direction

Build TalentSignal AI as a hiring intelligence command center, not a resume-table UI.

The current Redrob Senior AI Engineer challenge remains the first validation case. The architecture must still generalize to any JD and any structured resume/candidate profile.

### Core Modules

- Role Intelligence: parse the JD into role DNA, must-have signals, disqualifiers, preferred logistics, and factor weights.
- Evidence Ranker: produce a deterministic top-100 ranking from real candidate data.
- Compare Mode: explain tradeoffs between adjacent top candidates.
- Trust Layer: identify risk pressure, low confidence, profile inconsistency, and evidence gaps.
- Interview Kit: generate candidate-specific interview probes from the evidence packet.
- Exports: produce challenge CSV, factor scores, evidence packets, and risk reports.

## How This Beats A Plain Resume Ranker

A plain ranker answers: "Who is ranked first?"

TalentSignal should answer:

- What does the JD really require?
- Why is this candidate stronger than the next one?
- What evidence supports the decision?
- What could be wrong with the profile?
- What should an interviewer verify?
- Can the ranking be reproduced under the official constraints?
- Can the same framework handle 100 different JDs?

## Redrob Ecosystem Fit

The promo plan capabilities suggest a larger Redrob ecosystem:

- People search can feed discovery.
- Company search can enrich context and industry fit.
- Active jobs can benchmark role demand and talent scarcity.
- Mock interviews can validate shortlisted candidates.
- Deep research can enrich candidate/company evidence.
- Resume Ranker can become one module inside a broader hiring command center.

TalentSignal should therefore be presented as a framework that makes these capabilities coherent: role intelligence, evidence ranking, trust review, and interview validation in one loop.

## Immediate Build Decision

The UI should use the selected Helix design direction, but only for visual style. It must not copy unrelated navigation labels, menu items, sample content, or product language from the design system.

The product screens must use our own hiring-intelligence concepts:

- Role Intelligence
- Shortlist
- Compare
- Trust Layer
- Interview Kit
- Exports

## Non-Negotiable Quality Bar

Do not describe the product as complete merely because the UI renders.

For each product module, completion requires:

- It is driven by real candidate/JD data where applicable.
- It works through the live REST API and browser UI.
- It is validated with Playwright.
- It is consistent with the Helix visual system.
- It supports the final challenge artifact rather than distracting from it.


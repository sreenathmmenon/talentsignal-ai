# Interview Defense Notes

## Five-Minute Architecture Walkthrough

TalentSignal AI is a deterministic, evidence-based talent intelligence ranker. It compiles an agentic hiring workflow into an offline ranking command:

1. JD Strategist loads the Redrob scorecard.
2. Evidence Miner extracts profile, career, skill, and behavioral facts.
3. Talent Graph maps titles, skills, search/ranking concepts, production terms, and risk patterns.
4. Match Judge scores candidates across technical, career, seniority, logistics, behavior, and trust factors.
5. Risk Auditor penalizes keyword stuffing and unsupported claims.
6. Explanation Writer writes grounded CSV reasoning.
7. Recruiter Cockpit renders the ranked evidence packets.

## Why Not Live LLM Calls In Final Ranking

The challenge forbids network/API calls during final ranking and requires <=5 minutes CPU-only reproduction. A live LLM over 100,000 candidates would be slow, expensive, non-deterministic, and disallowed. The final ranker therefore uses deterministic compiled judgment: scorecards, dictionaries, evidence extraction, and factor scoring.

## Why This Beats Keyword Search

Keyword search over-ranks people who list AI skills without doing AI work. TalentSignal separates career evidence from skill-list evidence. A top candidate must show career evidence for retrieval/ranking/search/recommendation and production systems, not just have those words in skills.

## Scoring Tradeoffs

- Technical evidence is strongest, but career and behavior matter.
- Location and notice period are modifiers, not primary technical filters.
- Top-10 eligibility requires direct career evidence and no severe risk flags.
- Behavioral signals down-rank unavailable candidates without discarding excellent profiles automatically.

## Failure Modes We Guard Against

- AI keyword stuffing.
- Non-tech candidates with AI skills.
- Pure research without deployment.
- Stale and unresponsive candidates.
- Service-only paths without product/search evidence.
- Hallucinated reasoning.
- Reproduction failure.

## Candidate Defense Examples

Use `docs/candidate_case_studies.md` for rank-specific examples.


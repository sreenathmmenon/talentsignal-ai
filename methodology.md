# Methodology

## Problem Framing

The Redrob challenge is not a keyword-search task. The JD explicitly warns against candidates who list many AI terms without production evidence. The core requirement is to identify candidates who can own ranking, retrieval, matching, and evaluation systems in a product environment.

TalentSignal AI treats the task as an evidence-based talent-intelligence workflow:

1. Convert the JD into a role scorecard.
2. Extract candidate evidence from profile, career history, skills, and behavioral signals.
3. Score candidates with transparent factors.
4. Penalize suspicious or weakly supported profiles.
5. Produce grounded reasoning and audit artifacts.

## Agentic Architecture

The implementation is deterministic for challenge reproduction, but it is organized around agentic responsibilities:

- JD Strategist: loads the Redrob Senior AI Engineer scorecard from `job_specs/redrob_senior_ai_engineer.yaml`.
- Evidence Miner: extracts source-separated facts from profile, career, skills, and Redrob signals.
- Talent Graph Builder: maps roles, skills, search/ranking terminology, vector infrastructure, production terms, and known risk patterns.
- Match Judge: computes factor scores and final ranking.
- Risk Auditor: detects keyword stuffing, shallow AI interest, service-only risk, stale/low-response profiles, and suspicious skills.
- Explanation Writer: generates concise reasoning from extracted facts only.
- Recruiter Cockpit: renders a static UI for ranked candidates, score factors, evidence, and risks.

## Candidate Evidence

Each candidate is converted into a `CandidateEvidence` object containing:

- identity and logistics,
- current title and normalized title category,
- career text,
- skill text,
- retrieval/search/ranking/recommendation terms,
- vector/embedding infrastructure terms,
- ML/LLM/Python terms,
- ranking evaluation terms,
- production/shipping terms,
- product-company and service-company signals,
- behavioral hireability signals,
- suspicious-profile signals.

Career evidence is separated from skill-list evidence. This prevents skill-only keyword stuffing from dominating the ranking.

## Scoring

The final score combines:

- technical evidence,
- career fit,
- seniority,
- logistics,
- behavioral availability,
- trust/market signals,
- risk penalties.

The ranker gives strong credit for direct career evidence around retrieval, ranking, search, recommendation, embeddings/vector search, production systems, and evaluation. It down-ranks non-technical or shallow AI profiles unless career history supports the claim.

## Behavioral Signals

Redrob behavioral signals are treated as hireability modifiers:

- recent activity,
- open-to-work,
- recruiter response rate,
- response time,
- notice period,
- verification,
- interview completion,
- offer acceptance,
- recruiter saves/search appearances.

A perfect static profile with very low availability should not outrank a comparable active and responsive candidate.

## Trap Avoidance

Risk rules flag and penalize:

- non-tech AI keyword stuffing,
- AI terms without career evidence,
- expert skills with zero duration,
- service-only paths without product/search evidence,
- stale low-response candidates,
- shallow AI-tool interest.

The current final top 100 has zero risk flags under this implemented policy, and every top-10 candidate is top-10 eligible.

## Explainability

Reasoning is generated from evidence fields, not free-form model output. The explanation audit checks for empty, repeated, too-short/long, rank-inconsistent, and unsupported terminology.

The submitted CSV reasoning is intentionally concise. The richer evidence packets are exported to `outputs/evidence_packets.jsonl`.

## Reproducibility

The final ranking command:

```bash
python3 rank.py --candidates '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl' --out outputs/final_submission.csv
```

uses:

- CPU only,
- no network,
- no hosted LLM/API calls,
- no GPU,
- standard-library Python.

Measured runtime for the latest full run is recorded in `outputs/final_validation_report.json` and completion evidence.

## General Product Direction

The Redrob JD is the first-priority scorecard, but the system is built around configurable `JobSpec` inputs. Future work can add scorecards for other roles and categories without rewriting the candidate evidence pipeline.

## Known Limits

- The hidden relevance labels are unavailable, so quality is evaluated through JD analysis, premortem risks, factor audits, and top-candidate inspection.
- The current demo is a static recruiter cockpit rather than a hosted multi-user app.
- Final portal submission still requires user-owned contact/portal actions.


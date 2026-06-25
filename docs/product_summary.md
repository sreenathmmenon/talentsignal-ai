# TalentSignal — Product Summary

A universal candidate-intelligence engine that ranks the right people for any job,
explains why in their own words, proves it's fair, and runs on the customer's own
data. Best-in-class ranking with a trust moat the scraping incumbents lack.

## What it does
Drop in any job description and any candidates (PDF/DOCX/TXT/CSV/JSON/LinkedIn/
paste). Get a ranked, explainable, fake-resistant shortlist that reasons beyond
keywords and weighs who's actually hireable — with a per-candidate proof trail.

## Proven quality (measured, not claimed)
- Mean ranking composite **0.97** across 6 role types (vs 0.88 keyword baseline);
  NDCG@10 0.95–1.00, MAP 0.92–1.00.
- Zero-keyword paraphrase fits surfaced **10/10** into the top-10.
- **0 honeypots** in the top-10 on trap-heavy pools; 0 in the submitted top-100.
- Cross-JD top-10 overlap **~0.06** — genuinely JD-agnostic.
- Scales: 5,400 candidates ranked in **~0.45s**; the official 100K in ~47s.
- Reasoning at scale (100-row submission): **0/430 cited keywords hallucinated**,
  61 distinct opening patterns, 20/20 low-rank rows carry honest concerns.

## The trust moat (where the incumbents are exposed)
The 2026 Eightfold FCRA class action and the SeekOut/hireEZ scraping issues show
the market leaders are vulnerable exactly where TalentSignal is strongest:

- **No scraping.** Runs on the customer's own data — no "consumer report" / FCRA
  exposure.
- **Explainable.** Every requirement match quotes the candidate's *own sentence*
  as proof (0 hallucination, audited).
- **Fair & compliant.** EEOC four-fifths adverse-impact report with integrity
  disclosures (label-coverage gaps surfaced); identity-blind by construction
  (name-swap score delta = 0.0).
- **Human-in-the-loop.** Ranks + explains for a human; never silently auto-rejects.
- **Candidate transparency.** A report showing what the engine used, what matched
  with proof, what wasn't (chance to correct), and concerns — the feature the
  incumbents' lawsuits are about, that none of them offer.

## Surfaces (one engine, full parity)
- **Studio** (`studio.py`) — product GUI: rank, candidate transparency, challenge.
- **REST API** (`api_server.py`) — `/rank /compliance /candidate_report /audit /ingest/*`.
- **Python SDK** (`talentsignal.api`, `talentsignal.client`) — embed or call.
- **MCP server** (`mcp_server.py`) — 7 agentic tools incl. compliance & transparency.
- **CLI** (`rank.py`) + batch (`rank_file`, `rank_many_jds`, `rank_to_csv`).
All surfaces default to the best (hybrid) engine when a model is available.

## Engineering quality
- 145 tests; CI quality gate (ranking/honeypot/generality/fairness/reproduction)
  on every push.
- Degrades, never crashes, on hostile input (empty/injection/unicode/null/mistyped).
- Deterministic, reproducible offline; the hackathon submission is valid, 0
  honeypots, and reproduces in budget.
- Self-hostable, offline — the named future direction for privacy-preserving hiring.

See `docs/competitive_analysis.md` for positioning and `learnings.md` for the
issues found and fixed during development.

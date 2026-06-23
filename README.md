# TalentSignal

**A universal candidate-intelligence engine.** Drop in ANY job description and ANY set of resumes/candidates — in ANY format (PDF, DOCX, TXT, CSV, JSON, LinkedIn, or pasted text) — and get back a ranked, explainable, fake-resistant shortlist that reasons *beyond keywords* and weighs who's actually hireable.

Tagline: **The right people for any role — any JD, any resume, any way.**

Use it three ways, all over one engine:
- **MCP server** — agentic: any AI agent (Claude Desktop, agent frameworks) calls it as a tool.
- **REST API + Python SDK** — integrate it into any portal or ATS.
- **Product UI** — a recruiter app: upload a JD + resumes → live, explainable shortlist.

Built for the Redrob *Intelligent Candidate Discovery & Ranking Challenge* — the challenge JD/dataset is proof-case #1, and the submission is a valid top-100 CSV produced by this engine — but the system is the general product the challenge's job is hiring someone to build.

## Why it's different

1. **Reasons beyond keywords.** Hybrid retrieval (sentence-embeddings + lexical) over the JD's *own* requirements means a candidate who "built the recommendation engine serving the homepage" matches "shipped a ranking system" with zero shared keywords.
2. **Rejects fakes.** A role-independent consistency auditor vetoes internally-impossible honeypots (8 years at a company younger than that, expert skill with 0 months) by their contradictions, not their keywords.
3. **Weighs hireability.** Schema-driven behavioral signals down-weight stale, unresponsive candidates — and adapt to whatever signal fields a dataset has.
4. **Proves itself.** A first-class evaluation suite (NDCG@10/@50, MAP, P@10 over labeled data across many JDs) measures every change — not guesswork. On labeled multi-JD eval the hybrid engine scores composite **0.96** with **0%** honeypots in the top-10 and zero-keyword paraphrase fits at **10/10** in the top-10.
5. **JD-agnostic, by measurement.** Cross-JD top-10 overlap ~0.06 — it surfaces genuinely different people for different roles.
6. **Extensible.** A signal-plugin framework means new intelligence (background verification, GitHub-repo analysis) is added without touching the core.

## Surfaces (quickstart)

```bash
# Product UI — upload any JD + resumes, see a ranked explainable shortlist
python product_ui.py            # http://127.0.0.1:8800

# REST API + SDK — integrate into a portal/ATS
python api_server.py            # POST /rank, /ingest/jd, /ingest/resume, /audit

# MCP server — expose the engine as agentic tools
python mcp_server.py            # see docs/mcp.md

# Python — embed the engine directly
python -c "from talentsignal.api import rank; print(rank('Senior AI Engineer ...', candidates)[:3])"
```

```python
# Ingest ANY format, then rank — one clean call
from talentsignal.ingest import ingest
from talentsignal.api import rank
candidates = ingest(["alice.pdf", "bob.docx", "team.csv"])   # mixed formats
result = rank("Senior AI Engineer: embeddings, retrieval, ranking. 5-9 years.", candidates, top_n=10)
for c in result.ranked:
    print(c.rank, c.title, round(c.score, 3), "—", c.reasoning)
```

## Architecture (JD-agnostic hybrid engine)

TalentSignal ranks **any** job description against **any** candidate dataset — the challenge's JD/dataset are proof-case #1, not the whole system.

- **JD ingestion** (`src/talentsignal/jd_ingest.py`) — parse any free-text or structured JD into a weighted requirement model (must-have / nice-to-have / disqualifier).
- **Hybrid semantic matching** (`src/talentsignal/semantic_match.py`) — match each requirement to candidate evidence by sentence-embedding cosine **plus** lexical overlap, so a candidate who "built the recommendation engine serving the homepage" matches "shipped a ranking system" with zero shared keywords.
- **Schema-driven signals** (`src/talentsignal/schema_profile.py`) — behavioral/availability/trust scoring adapts to whatever signal fields a dataset provides (not hardcoded to Redrob's 23).
- **General consistency auditor** (`src/talentsignal/consistency_audit.py`) — role-independent internal-contradiction checks that veto impossible honeypots (e.g. 8 years at a company that has tenure beyond the candidate's stated experience, expert skill with 0 months).
- **Unified scoring** (`src/talentsignal/scoring.py`) — one JD-requirement-weighted path; same code for an AI JD and a sales JD.
- **Evaluation suite** (`src/talentsignal/eval/`, `scripts/eval_harness.py`) — NDCG@10/@50, MAP, P@10 over labeled synthetic data across multiple JDs and dataset shapes. Every ranking change is measured, not guessed.

**Two engines.** `spine` is the zero-dependency structured ranker that always produces a valid CSV in budget. `hybrid` adds the precomputed semantic index (numpy-only at rank time) and measurably improves ranking: on labeled multi-JD eval, mean composite **0.95 vs 0.88**, zero-keyword paraphrase fits reach **10/10 in top-10 (vs 3/10)**, and honeypot rate in top-10 drops to **0%**.

### Run the evaluation suite

```bash
python3 scripts/eval_harness.py --engine spine   # writes outputs/eval/report.md
python3 scripts/eval_harness.py --engine hybrid   # needs the embedding model installed
```

### Rank with the hybrid engine

```bash
# 1) offline, once (~9 min): build the embedding index (may exceed the 5-min budget)
make precompute      # or: python3 precompute.py --candidates <jsonl> --job-spec <yaml> --index-dir outputs/index

# 2) the ranking step itself loads only numpy arrays, offline, within budget
make rank-hybrid     # or: python3 rank.py --engine hybrid --index-dir outputs/index --candidates <jsonl> --out <csv>
```

### Demo: rank any JD + candidates

```bash
python3 scripts/demo_rank.py --jd demo/data/sales_jd.md \
  --candidates demo/data/sales_candidates.jsonl --engine hybrid --top-n 10
```

## Repository

- GitHub: https://github.com/sreenathmmenon/talentsignal-ai
- Author: Sreenath
- Contact: sreenathmmmenon@gmail.com

## Status

The engine and all four surfaces are implemented, tested (115 tests), and validated end-to-end:

- **Engine**: JD ingestion, hybrid semantic matching, schema-driven signals, role-independent consistency auditor, unified scoring, grounded reasoning — with a labeled evaluation suite (composite 0.96, paraphrase 10/10, honeypots 0%, JD-agnostic ~0.06).
- **Universal ingest**: PDF/DOCX/TXT/CSV/JSON/LinkedIn/paste → rankable; pluggable adapters.
- **Surfaces**: clean `rank()` facade + SDK, MCP server (agentic), REST API + Python client, product UI.
- **Extensibility**: signal-plugin framework with roadmap stubs (background verification, GitHub-repo analysis).
- **Hackathon submission**: valid top-100 CSV (hybrid engine), 0 honeypots, reproduces offline in budget; the spine engine is a zero-dependency fallback.
- **Quality**: name/identity-blind (fairness audit, score delta 0.0), no reasoning hallucination (audited), Stage-3 reproduction verifier.

## Requirements

The ranking step uses only `numpy` (the spine engine uses only the Python standard library). Embeddings are precomputed offline by `precompute.py` (`requirements-precompute.txt`). The universal ingest layer optionally uses `pypdf` / `python-docx` for those formats.

Recommended:

```bash
python3 --version
```

Python 3.11 was used during development.

## Reproduce Final Submission

```bash
python3 rank.py \
  --candidates '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl' \
  --out outputs/final_submission.csv
```

This also writes:

- `outputs/factor_scores.csv`
- `outputs/evidence_packets.jsonl`
- `outputs/risk_report.csv`
- `outputs/risk_summary.json`

## Validate

Run tests:

```bash
python3 -m pytest tests/test_baseline_pipeline.py tests/test_app_rest.py -q
```

Run official challenge validator:

```bash
python3 '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py' \
  outputs/final_submission.csv
```

Run full internal validation:

```bash
python3 scripts/validate_all.py \
  --candidates '[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl' \
  --submission outputs/final_submission.csv
```

Run explanation audit:

```bash
python3 scripts/audit_explanations.py --evidence-packets outputs/evidence_packets.jsonl --strict
```

Run live UI browser validation:

```bash
python3 app.py --host 127.0.0.1 --port 8765
npx playwright test tests/ui-live.spec.js --reporter=line
```

The Playwright suite drives the browser UI against the local REST API and the real challenge candidate JSONL. It verifies ranking execution, ranked rows, candidate evidence details, filtering, sorting, CSV download, and desktop/mobile screenshots.

## Audit And Review

Generate top-25 audit:

```bash
python3 scripts/audit_top_candidates.py \
  --evidence-packets outputs/evidence_packets.jsonl \
  --out-csv outputs/top25_audit.csv \
  --out-md outputs/top25_audit.md
```

Compare two candidates:

```bash
python3 scripts/compare_candidates.py CAND_0079387 CAND_0018499 \
  --evidence-packets outputs/evidence_packets.jsonl
```

## Live Recruiter Cockpit

Start the local product UI:

```bash
python3 app.py --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/` in a browser.

The UI uses the Helix control-plane design system for a production-grade hiring intelligence cockpit. It generates a ranked shortlist from the selected candidate JSONL and JD scorecard, shows fit factors and grounded evidence, exposes risk flags, supports search/sort/risk filtering, and downloads generated CSV/evidence/risk artifacts.

The product direction is a universal JD-to-hiring-decision command center: role intelligence, evidence ranking, candidate comparison, boundary review, trust/trap review, interview probes, and exports. See `REDROB_BUSINESS_PLAN_PRODUCT_STRATEGY.md` for the Redrob business-plan signal and roadmap implication, and `TALENTSIGNAL_V2_PRODUCT_AND_ACTION_PLAN.md` for the V2 product plan.

## Docker Reproduction

The Dockerfile is intentionally minimal and uses the standard-library ranker.

```bash
docker build -t talentsignal-ai .
docker run --rm talentsignal-ai
```

The raw `candidates.jsonl` is ignored by git because it is large. For external reproduction, place the provided challenge data at the documented path or pass another mounted path to `rank.py`.

## Project Structure

Surfaces (all over one engine facade `talentsignal.api.rank`):
- `rank.py`: hackathon ranking CLI (spine + hybrid engines).
- `product_ui.py`: the product UI — upload any JD + resumes → ranked shortlist.
- `api_server.py`: REST API; `src/talentsignal/client.py`: Python SDK client.
- `mcp_server.py`: MCP server exposing the engine as agentic tools.
- `precompute.py`: offline embedding-index builder (hybrid engine).
- `app.py`: original recruiter cockpit (legacy demo).

Engine (`src/talentsignal/`):
- `api/`: public facade + typed results (the one contract every surface uses).
- `ingest/`: universal ingest — adapters for PDF/DOCX/TXT/CSV/JSON/LinkedIn + hybrid resume parser.
- `jd_ingest.py`, `jd_parser.py`: JD → weighted requirement model.
- `semantic_match.py`, `artifacts.py`: hybrid retrieval + numpy-only index loading.
- `scoring.py`, `consistency_audit.py`, `schema_profile.py`, `reasoning.py`: the brain.
- `eval/`: metrics, labeled datasets, role library, JD library.
- `signals/`: extensible signal-plugin framework (+ roadmap stubs).

Support:
- `job_specs/`: machine-readable JD scorecards. `demo/data/`: generated demo datasets.
- `scripts/`: eval harness, data factory, demo, audits. `docs/`: methodology, MCP, architecture/defense.
- `outputs/`: generated submission + `index/` (git-lfs embedding index). `tests/`: 104 tests.

## Important Docs

- `AIM.md`
- `HACKATHON_CHALLENGE_AND_WORK_PREPARED.md`
- `PROJECT_COMPLETION_RULE.md`
- `PROJECT_AUTHORSHIP_RULE.md`
- `PROJECT_TAGLINE_DECISION.md`
- `COUNCIL_REVIEW_JUNE_16_2026.md`
- `PROJECT_EXECUTION_STORIES_AND_TASKS.md`
- `TALENTSIGNAL_V2_PRODUCT_AND_ACTION_PLAN.md`
- `WORLD_CLASS_EXECUTION_PLAN.md`
- `FIRST_PRIZE_PREMORTEM.md`
- `AGENTIC_AI_TALENT_INTELLIGENCE_RESEARCH.md`
- `REDROB_BUSINESS_PLAN_PRODUCT_STRATEGY.md`
- `REDROB_RESEARCH_AND_BIG_BET_STRATEGY_JUNE_17_2026.md`
- `methodology.md`
- `docs/final_completion_evidence.md`
- `docs/v2_completion_evidence.md`

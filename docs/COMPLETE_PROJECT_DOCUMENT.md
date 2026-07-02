# TalentSignal — Complete Project Document

*What the challenge was, what it required, what we built, every feature, every file, and why.*

This document is compiled from the actual repository — every module's real purpose is
taken from its code, every number from the committed data. Nothing is assumed.

- **Repo:** https://github.com/sreenathmmenon/talentsignal-ai
- **Live Studio UI:** https://talentsignal-production.up.railway.app
- **Live REST API + Swagger:** https://talentsignal-api-production.up.railway.app/docs
- **Scale:** 47 engine modules · 40 test files (234 tests) · 19 scripts · 3 hosted-capable surfaces
- **Author:** Sreenath

---

## Part 1 — The Challenge

### 1.1 What it was
The **Redrob "Intelligent Candidate Discovery & Ranking Challenge"** (India Runs Data & AI
Challenge). Build an intelligent candidate-ranking system for a provided **Senior AI
Engineer (founding-team)** job description, run it against a **100,000-candidate pool**, and
submit only the **top 100**.

### 1.2 The data (organizer-provided)
- `candidates.jsonl` — 100,000 candidate profiles (never modified).
- `candidate_schema.json` — the profile shape: `candidate_id` (`CAND_XXXXXXX`), `profile`
  (headline, summary, location, years_of_experience, current_title/company/industry, …),
  `career_history`, `education`, `skills`, and **`redrob_signals`** (behavioral signals).
- `job_description.docx` — the target Senior AI Engineer JD.
- `redrob_signals_doc.docx` — the behavioral signal definitions.
- `validate_submission.py` — the official format validator.

### 1.3 The Redrob behavioral signals
Profile completeness, last-active date, open-to-work flag, recruiter response rate, average
response time, skill-assessment scores, notice period, preferred work mode, willingness to
relocate, GitHub activity, search appearances, saved-by-recruiters, interview completion
rate, offer acceptance rate, email/phone/LinkedIn verification. *These must modify
hireability — a strong-but-stale, unresponsive, unavailable candidate should not outrank a
comparable active one.*

### 1.4 Required output
CSV, exact columns `candidate_id,rank,score,reasoning`:
- exactly 100 data rows + header
- ranks 1–100, each once; unique IDs matching `CAND_XXXXXXX`
- scores are floats, **monotonically non-increasing** by rank
- reasoning: 1–2 grounded sentences

### 1.5 How it's scored (hidden composite)
`composite = 0.50·NDCG@10 + 0.30·NDCG@50 + 0.15·MAP + 0.05·P@10` — **top-10 precision
dominates.**

### 1.6 Evaluation stages
1. Format validation
2. Hidden ranking score (the composite above)
3. Code reproduction + honeypot check — **disqualifiers:** can't reproduce in budget,
   missing/fabricated code, or **honeypot rate > 10% in the top 100**
4. Manual review — reasoning quality, methodology-matches-code, git history, code quality
5. Defend-your-work interview

### 1.7 Final-ranking constraints (on the reproduce command)
≤ 5 min wall clock · ≤ 16 GB RAM · CPU-only · network OFF · no hosted LLM during ranking
· ≤ 5 GB disk.

### 1.8 The real JD interpretation
Not "most AI keywords." Evidence of **production ML/search/ranking/retrieval systems +
product-engineering judgment**. Must-haves: production ML, embeddings/retrieval/ranking/
search/recommender/vector-hybrid, strong Python, evaluation frameworks (NDCG/MRR/MAP).
Negative signals: research-only without deployment, shallow LangChain/OpenAI demos, no
recent production coding, service-only career path, CV/speech/robotics without NLP/IR
relevance, AI keyword-stuffing without evidence.

---

## Part 2 — What We Built (the big idea)

We did **not** build a one-JD hack. We built **TalentSignal — one JD-agnostic candidate-
intelligence engine** that ranks *any* candidate against *any* job description **by meaning,
not keywords**, rejects fabricated résumés, and explains every decision — with the hackathon
CSV as proof-case #1.

**One engine, three surfaces:**
- **Studio UI** — a recruiter web app (hosted).
- **REST API + Swagger** — the integrate/embed surface (hosted).
- **MCP server** — the agentic surface (9 tools + 4 workflow prompts) an AI agent calls.

**No LLM in the ranking path, no GPU, no per-token cost.** Deterministic, offline-capable,
CPU-only, ~450 MB.

### The scoring law (the heart of the engine)
From `scoring.py`, verbatim:
```
final = R^1.1 · (0.45 + 0.55·Q) · soft_multiplier · hard_veto
```
- **R** = relevance to *this JD's own parsed requirements* (dominant; the exponent 1.1 is
  super-linear so weak relevance is punished harder than rewarded).
- **Q** = generic quality blend of {seniority, logistics, behavioral, trust}, floored at
  0.45 so quality tunes but never dominates relevance.
- **soft_multiplier** = graded penalties (risk flags, availability, disqualifier overlap
  with counter-evidence).
- **hard_veto** = 0 only for an internally-impossible profile or a true disqualifier with no
  counter-evidence.

This one law, parameterized entirely by the *parsed JD*, is why the same code ranks an AI
JD, a sales JD, or a designer JD with no per-category branches.

---

## Part 3 — Every Feature, File by File (verified from code)

### 3.1 The ingest layer — `src/talentsignal/ingest/` (turn ANY input into candidate records)
| File | What it does |
|---|---|
| `__init__.py` | Universal ingest layer — turn ANY input into canonical candidate records. |
| `adapters.py` | Built-in adapters: **JSON/JSONL, CSV/TSV, text/paste, PDF, DOCX, LinkedIn** (heavy deps like pypdf/python-docx imported lazily). |
| `model.py` | Canonical candidate model — the normalized shape every adapter produces. |
| `registry.py` | Adapter registry + the public `ingest()` entry point (dispatch by format/extension). |
| `resume_parser.py` | Résumé text → structured Candidate (local default, optional LLM). |

*Why:* a general product must accept any résumé in any format, not just the organizer's
JSON — this is the "any resume, any format" front door.

### 3.2 JD understanding — `jd_ingest.py`, `jd_parser.py`, `category_taxonomy.py`
| File | What it does |
|---|---|
| `jd_ingest.py` | Free-text JD → structured, **weighted requirement model** (must_have / nice_to_have / disqualifier, seniority band, locations) via transparent regex + cue-lexicon (no LLM). |
| `jd_parser.py` | `JobSpec` + loaders: `load_job_spec` (YAML), `job_spec_from_jd_text` (free text), default locations per category. |
| `category_taxonomy.py` | `CategoryProfile` + `get_category_profile` + `validate_weights` — role-family vocabulary/weights. |

*Why:* the engine scores against the JD's *own* parsed requirements — this is the front door
that makes it JD-agnostic.

### 3.3 The matching + scoring core
| File | What it does |
|---|---|
| `features.py` | `build_evidence` → `CandidateEvidence`; whole-token matching (`contains_any`), tenure math (`months_since`). |
| `semantic_match.py` | Hybrid semantic matching between JD requirements and candidate evidence (dense embeddings + lexical). |
| `scoring.py` | The scoring law: `score_candidate` (spine) + `score_candidate_hybrid`; `ScoreBreakdown`; `reachability()`; the multiplicative relevance-gate. |
| `ranking.py` | `rank_records` / `score_pool_hybrid` / `rank_candidates`; the near-tie reachability tiebreak; monotonic score emission; CSV/factor/packet writers. |
| `reranker.py` | Cross-encoder reranking — the production-grade accuracy stage on the shortlist. |
| `reasoning.py` | Recruiter-grade, grounded, rank-aware reasoning — the reasoning column judges read (≥8 phrasing variants per tier, candidate-specific evidence, no hallucination). |

*Why:* meaning-based ranking is the whole thesis — a candidate who wrote "built the
recommendation engine" matches "shipped a ranking system" with zero shared keywords.

### 3.4 Trust, fairness & honeypot defense
| File | What it does |
|---|---|
| `consistency_audit.py` | Role-independent consistency/honeypot auditor — flags impossible profiles by **contradiction, not keywords** (expert skill 0 months, tenure > career length, etc.). |
| `risk_audit.py` | `risk_flags` / `risk_penalty` — AI-role-specific risk signals feeding the soft penalty. |
| `trap_detector.py` | `rejected_trap_examples` — surfaces which trap archetypes were rejected and why. |
| `candidate_report.py` | Candidate-facing transparency report — what matched (with proof), what wasn't evidenced, concerns; the humane answer to opaque rejection. |
| `explanation_audit.py` | `audit_packets` — fails the build if any reasoning claim isn't grounded in the profile. |
| `boundary_review.py` | `boundary_windows` — inspect candidates on the accept/reject line (internal QA). |
| `validation.py` | `validate_rows` — internal submission-shape validation. |

*Why:* Stage-3 disqualifies at >10% honeypots; and in an era of AI-hiring lawsuits, rejecting
fabrication + explaining every call is the trust differentiator.

### 3.5 Signals & schema adaptivity
| File | What it does |
|---|---|
| `schema_profile.py` | Schema-driven signal engine — behavioral/availability/trust adapt to *whatever* signal fields a dataset has (not hardcoded to Redrob's 23). |
| `signals/base.py` | Signal interface + registry (plugin framework). |
| `signals/builtin.py` | Built-in signals + future-facing extension stubs. |
| `github_analysis.py` | GitHub-repo analysis — surface real engineering evidence from a candidate's linked public profile (consented, offline-safe). |
| `talent_graph.py` | Talent-graph relationships (extension). |

*Why:* a real product ingests datasets with different signal vocabularies — the engine must
not break when the schema changes.

### 3.6 Comparative & interview intelligence
| File | What it does |
|---|---|
| `candidate_compare.py` | `compare_by_rank` / `compare_packets` — factor-by-factor "why #A over #B" scorecard. |
| `interview_kit.py` | `build_interview_kit` — evidence-grounded interview questions + hire/no-hire rubric. |

*Why:* these answer the recruiter's real next questions ("why them?" and "how do I
interview them?") — surfaced in the UI and as MCP tools.

### 3.7 The engine API (SDK + facade + batch)
| File | What it does |
|---|---|
| `api/facade.py` | The engine facade — one clean `rank()` entry point every surface calls. |
| `api/types.py` | Typed result objects (`RankResult`, `RankedCandidate`, `FactorBreakdown`) — the stable output contract. |
| `api/batch.py` | Batch + file ergonomics — rank many JDs / large pools (enterprise scale). |
| `client.py` | TalentSignal Python SDK — a thin client for the REST API. |
| `live_cache.py` | Live in-memory ranking cache for the product surfaces (rank once, serve instantly, re-rank on data change). |
| `artifacts.py` | Load/save the precomputed semantic index (numpy + json ONLY at rank time; LFS-pointer guard). |
| `io.py` | `iter_candidates` — stream candidates from `.jsonl`/`.jsonl.gz`. |
| `baseline_ranker.py` | A credible keyword-only baseline — the foil that proves our value (the "rescued by meaning" comparison). |

### 3.8 Evaluation framework — `src/talentsignal/eval/`
| File | What it does |
|---|---|
| `metrics.py` | NDCG@k, MAP, P@k + the challenge composite `0.50·NDCG@10 + 0.30·NDCG@50 + 0.15·MAP + 0.05·P@10`. |
| `datasets.py` | Labeled synthetic candidate generator (strong / paraphrase-ideal / adjacent / weak / irrelevant / honeypot archetypes, graded 0–5). |
| `roles.py` | RoleProfile library — role-specific vocabulary driving the synthetic generator. |
| `jd_library.py` | Free-text + structured JD library, one per role (cross-role generality tests). |
| `adversarial.py` | **Adversarial / honeypot resistance** — non-circular attack test (prompt injection, keyword stuffing, fabricated experience, impossible tenure). |
| `compliance.py` | Hiring-compliance analysis — **EEOC four-fifths** adverse-impact report (caller-supplied group labels). |
| `fairness.py` | Fairness / bias audit — name-invariance (identity-blind guarantee). |

*Why:* the JD's own must-have is "designing evaluation frameworks" — this suite is both our
quality instrument and a headline interview artifact.

---

## Part 4 — The Surfaces (entrypoints)

| File | Surface | What it is |
|---|---|---|
| `rank.py` | CLI | The hackathon ranking CLI (`--engine spine|hybrid`); the LFS/reproduce guard; writes the submission CSV + factor scores + evidence packets + risk report. |
| `studio.py` | **Studio UI** | The product GUI (hosted). Paste any JD + résumés → ranked, explained shortlist: verdict, Matched✓/Missing✗ skills panel, reachability, "found by meaning", compare, interview kits, live 100K tab. |
| `api_server.py` | **REST API** | 8 endpoints + full OpenAPI 3.0 + interactive **Swagger UI at `/docs`** (hosted). |
| `mcp_server.py` | **MCP server** | The agentic surface: 9 tools + 4 workflow prompts, schema validation, friendly errors, ping. |
| `precompute.py` | Offline | Builds the semantic embedding index (offline, allowed to exceed the 5-min budget). |
| `app.py` / `product_ui.py` | (legacy) | Earlier UIs; consolidated into Studio (kept for import stability). |

### REST endpoints (verified)
`/rank`, `/ingest/jd`, `/ingest/resume`, `/audit`, `/compliance`, `/candidate_report`,
`/health`, `/openapi.json` (+ `/docs` Swagger UI, `/` landing).

### MCP — 9 tools
`rank_candidates`, `compare_candidates`, `build_interview_kit`, `candidate_report`,
`compliance`, `audit_candidate`, `ingest_jd`, `screen_resume`, `explain_ranking`.

### MCP — 4 workflow prompts
`shortlist_for_role`, `fair_hiring_review`, `prep_interview`, `explain_to_candidate`.

---

## Part 5 — Scripts (19) — the tooling around the engine

| Script | What it does |
|---|---|
| `prove.py` | One command that reproduces the three core claims on the real 100K. |
| `rescue_ledger.py` | The brief's thesis proven — how many top-100 a keyword search misses. |
| `eval_harness.py` | Scores a ranker against labeled synthetic ground truth (all suites). |
| `real_jd_eval.py` | Validate the engine on REAL job descriptions. |
| `evaluate_multi_jd.py` | Cross-JD generality (low top-10 overlap across roles). |
| `adversarial_report.py` | Measure & report the non-circular attack-resistance metric. |
| `generate_datasets.py` | Synthetic data & JD factory. |
| `generate_case_studies.py` | Candidate case-study docs. |
| `gen_top10_report.py` | Regenerate TOP10_REPORT.md from the committed submission (can't drift). |
| `prebake_challenge.py` | Pre-bake the 100K "Proof at scale" snapshot for the hosted demo. |
| `verify_reproduction.py` | Verify the ranking reproduces in a clean, offline environment. |
| `ci_gate.py` | CI quality gate — run on every commit (rescue %, honeypot count, cross-JD overlap, name invariance, numpy-only rank imports). |
| `demo_rank.py` | Self-contained demo/sandbox entrypoint. |
| `compare_candidates.py`, `audit_explanations.py`, `audit_top_candidates.py`, `profile_dataset.py`, `sample_archetypes.py`, `validate_all.py` | Supporting audit/analysis utilities. |

---

## Part 6 — Tests (40 files, 234 tests)

Every subsystem is tested: ingest adapters, JD ingest, semantic match, hybrid scoring,
reasoning, consistency audit, compliance, fairness, eval metrics, eval datasets, reranker,
reproduction (offline, in-budget), rank-time-imports-numpy-only, the REST API + Swagger, the
MCP server (protocol + tools + prompts + friendly-error robustness), the SDK, live cache,
batch, GitHub analysis, signals, hardening/edge-cases, and the Studio payload (verdict +
skills). A CI workflow (`.github/workflows/ci.yml`) runs the full suite **numpy-only** (no
model) + the quality gate on every push.

---

## Part 7 — The Proof (real, measured numbers)

| Number | What it proves | Source |
|---|---|---|
| **32%** of the top-100 on the real 100K are people a keyword search would miss ("rescued by meaning") | Meaning-based ranking recovers strong people a keyword search structurally can't see | `outputs/rescue_summary.json` |
| **0** fabricated profiles in the submitted top-100 (audited on the real pool) | Honeypots don't reach the human's shortlist | consistency auditor |
| **100%** résumé-attack resistance on the semantic engine (vs **78%** on the keyword fallback) | Meaning is harder to game than keywords — the exact attacks that fool LLM screeners 30–95% | `outputs/eval/adversarial.md` |
| **0.9515 spine / 0.9728 hybrid** mean composite; **0.000** honeypot @top-10 | Ranking quality on our labeled multi-JD eval suite (our own graded labels) | `outputs/eval/METRICS.md` |
| **~30s spine / ~67s hybrid** for 100K, CPU-only, offline; byte-identical reproduction | Reproducibility + budget — replayable for any dispute | measured |
| **234 tests** green (incl. numpy-only CI + quality gate) | The behavior above is asserted, not claimed | `pytest` |

---

## Part 8 — Why We Built It This Way (design rationale)

1. **One engine, not a one-JD hack** — the JD the challenge is hiring for owns "candidate-JD
   matching at scale" and "evaluation frameworks." The winning move is to *be* that product.
2. **Meaning over keywords** — because 32% of the best people use different vocabulary and a
   keyword ATS deletes them. Measured on the organizer's own 100K.
3. **No LLM in the ranking path** — deterministic (reproducible for disputes + Stage-3),
   zero per-token cost, no GPU, offline. Also the reason it's cheap to host.
4. **Trust as a first-class feature** — reject fabrication by contradiction, explain every
   ranking, offer an adverse-impact check. Stage-3 disqualifies on honeypots; the market has
   AI-hiring lawsuits.
5. **Availability re-ranks, never filters** — an HR-council decision: `open_to_work=false`
   ≠ "won't join" (64% of the real pool is not-open, 22% still reachable). We surface strong
   passive candidates instead of hiding them.
6. **Three surfaces for the agentic era** — a recruiter logs into the Studio; a product
   embeds the REST API; an AI agent calls the MCP tools. Same engine, everywhere.
7. **Honest by design** — we retired inflated feature counts, state our boundaries (our eval
   labels are synthetic; the 100% resistance is scoped to four defined attack classes), and
   ship numbers anyone can re-run.

---

## Part 9 — Documentation Map (docs/)

- `challenge_brief.md` — the challenge, distilled.
- `methodology.md` — how the engine works + known limits.
- `STORY.md` — the agentic-era product narrative (+ `notes/STORY_ANGLES.md`).
- `mcp.md` — the MCP server (9 tools + 4 prompts + robustness).
- `api_examples.md` + `talentsignal.postman_collection.json` — REST usage.
- `deploy_railway.md` — how the hosted demo is deployed.
- `architecture_and_defense.md`, `interview_defense.md`, `competitive_analysis.md` — depth
  for the defend-your-work stage.
- `notes/FIRST_PRIZE_PREMORTEM.md`, `notes/BUG_HUNT_181.md` — the rigor trail.
- `outputs/eval/METRICS.md`, `outputs/eval/adversarial.md`, `outputs/rescue_summary.json` —
  the canonical measured numbers.

---

*Compiled from the repository at commit HEAD. Every module purpose is from its code; every
number from committed data. If a claim isn't here, it isn't claimed.*

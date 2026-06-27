# TalentSignal — Methodology

## Problem

Given any job description and any pool of candidates, surface the right people —
ranked best-fit first, explained, and resistant to gaming. The Redrob challenge
frames the hard version: ~100K candidates, one nuanced JD, deliberate traps
(keyword stuffers, plain-language strong fits, ~80 internally-impossible
honeypots), and the explicit instruction that the right answer requires reasoning
*beyond keywords* and accounting for who is actually hireable.

We treated this not as a one-JD tuning exercise but as the v1 of a universal
candidate-intelligence engine — because that generalization is exactly what makes
the ranking correct, and it is the system the role itself is about.

## Approach

### 1. JD → weighted requirement model
Any JD (free text or structured) is parsed into must-have / nice-to-have /
disqualifier requirements with importance weights, a seniority band, and
preferred locations — an explainable cue-lexicon + regex pipeline, no hosted LLM.
The same model is produced whether the JD is a hand-written scorecard or a pasted
paragraph, so the engine is genuinely JD-agnostic.

### 2. Hybrid semantic matching (the core)
Each requirement is matched against each candidate's *evidence text* (summary,
career descriptions, skills) by two channels:
- **dense** — sentence-embedding cosine (MiniLM), so meaning matches even with no
  shared words ("built the recommendation engine serving the homepage" ↔
  "shipped a ranking system");
- **lexical** — whole-token overlap, to catch exact tool/skill terms embeddings
  blur (FAISS, NDCG).

Combined per requirement (`alpha·dense + (1-alpha)·lexical`), weighted by
requirement importance. Sentence-embedding cosines bunch in a narrow band, so we
monotonically rescale the informative range to restore discrimination without
reordering. This replaces hardcoded keyword lists as the primary signal.

### 3. Schema-driven hireability
Behavioral/availability/trust are derived from whatever signal fields a dataset
provides (normalized to availability/engagement/trust), so a stale, unresponsive
"perfect-on-paper" candidate is correctly down-weighted — and the engine works on
a candidate schema it has never seen.

### 4. Role-independent consistency auditor (anti-honeypot)
Embeddings cannot tell a real strong candidate from a keyword-stuffed honeypot —
they score the same. So honeypots are caught by *internal contradiction*: career
tenure exceeding stated experience, expert proficiency with zero months, a skill
claiming more years than the whole career, broken dates. These checks are
structural and role-independent, and each flag carries the two contradicting
facts. They drive a top-rank veto.

### 5. Unified, data-driven scoring
One scoring path parameterized by the JD's own requirement weights — the same
code ranks an AI JD and a sales JD; only the parsed requirements differ. Final
score blends technical/career (from the hybrid match), seniority, logistics,
behavioral, and trust, minus penalties from the consistency auditor and semantic
disqualifier hits.

### 6. Grounded, rank-aware reasoning
Each candidate's reasoning is composed from the requirements that actually matched
and the keywords actually present in their profile — so no claim is ungrounded —
with tone scaled to rank and honest concerns surfaced for lower ranks.

## How we know it works (evaluation)

There is no leaderboard and no labels, so we built a first-class evaluation
framework — itself a direct demonstration of the JD's "designing evaluation
frameworks" must-have. Labeled synthetic pools (strong / paraphrase-ideal /
adjacent / weak / irrelevant / honeypot / behavioral-twin) across six roles and
multiple schema shapes are scored with NDCG@10/@50, MAP, P@10.

Headline results (labeled multi-JD eval; all numbers sourced in
[`../outputs/eval/METRICS.md`](../outputs/eval/METRICS.md)):

| metric | spine (default) | hybrid (+embeddings) |
|---|---|---|
| mean per-role composite | **0.95** | **0.97** |
| zero-keyword paraphrase fits in top-10 | 10/10 | **10/10** |
| honeypot rate in top-10 (trap-heavy pool) | 0% | **0%** |
| cross-JD top-10 overlap (lower = more JD-agnostic) | — | **~0.06** |

**The rescue result (real 100K):** a keyword filter ranks **28 of our top-100**
candidates outside its own top 100 — a recruiter on keyword search would never see
28% of who we recommend (`../outputs/rescue_summary.json`).

Additional guarantees:
- **Reproducible & offline:** the ranking step is CPU-only, no-network, and
  imports only numpy (embeddings are precomputed offline). Full 100K runs in ~51s
  / ~3.2 GB.
- **Fair:** the engine is name/identity-blind — 150 name-swap tests yield a max
  score delta of 0.0.
- **No hallucination:** every keyword cited in reasoning is present in the
  candidate's own text — audited to 0 ungrounded across the submission.
- **DQ-safe:** 0 honeypots in the submitted top-100.

## From engine to product

The same engine is exposed as a clean `rank(jd, candidates)` facade, behind:
a universal ingest layer (PDF/DOCX/TXT/CSV/JSON/LinkedIn/paste → rankable), an
MCP server (agentic tools), a REST API + Python SDK (integrate), and a product UI
(upload → explainable shortlist). A signal-plugin framework makes new intelligence
(background verification, GitHub-repo analysis) additive. The challenge submission
is one output of this engine; the product is the system the JD is hiring for.

## Privacy & fairness

- **Identity-blind ranking.** The engine scores from evidence (summary, career,
  skills) and structured signals — never the candidate's name. A name-swap audit
  (gendered/cultural name sets) yields a score delta of exactly 0.0, so ranking
  is provably invariant to identity.
- **PII handling.** Real resumes contain PII. The ranking step is local, offline,
  and deterministic — no candidate data leaves the machine. The optional LLM
  ingest mode is the only path that sends resume text to an external service and
  is strictly opt-in; the default parser is fully local. A production deployment
  should add PII minimization/retention controls at the ingest boundary.

## Honest limitations / next steps

- Local resume parsing is heuristic; an optional LLM ingest mode raises accuracy.
- Embedding model is small (MiniLM); a stronger/longer-context model and
  career-history-only embedding would sharpen the senior-vs-pretender call.
- Requirement weights and dense/lexical alpha are tuned on synthetic eval; a
  labeled real-resume corpus and learning-to-rank over the factors are the next
  quality lever.

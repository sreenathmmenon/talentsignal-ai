# TalentSignal — Architecture & Defense Notes

This document is the walkthrough for the defend-your-work stage: what the system
is, why each design choice was made, and how to reproduce and verify it.

## One-sentence summary

TalentSignal is a **JD-agnostic, semantic, explainable** candidate-ranking engine:
any job description (free text or structured) against any candidate dataset, with
a measured evaluation framework proving the quality. The Redrob JD/dataset is
proof-case #1, not the whole product.

## The pipeline

```
JD (free text or YAML)
  -> jd_ingest: weighted Requirement model (must / nice / disqualifier)
candidate record
  -> features.build_evidence  (source-separated evidence text + signals)
  -> semantic_match           (dense embedding cosine + lexical, per requirement)
  -> schema_profile           (availability/engagement/trust from any signal vocab)
  -> consistency_audit        (role-independent honeypot/contradiction veto)
  -> scoring.score_candidate_hybrid  (one JD-requirement-weighted path)
  -> reasoning                (grounded, rank-aware, non-templated)
  -> ranking                  (sort, write CSV + audit artifacts)
```

## Key design decisions (and why)

1. **Two engines, gated.** `spine` is a zero-dependency structured ranker that
   always produces a valid CSV in budget — the guaranteed floor. `hybrid` adds
   the semantic index and only ships if it measurably beats the spine on labeled
   eval. This bounds downside while capturing the upside. *Why:* a fancier ranker
   that scores worse is negative EV when NDCG@10 is 50% of the score.

2. **Hybrid retrieval, not keyword membership.** The primary signal is embedding
   cosine between each JD requirement and the candidate's evidence, combined with
   a lexical channel for exact tool terms. *Why:* the JD explicitly says the right
   answer requires reasoning beyond keywords; a candidate who built a recsys but
   never writes "RAG" must still surface. Measured: zero-keyword paraphrase fits
   go from 3/10 to 10/10 in the top-10.

3. **Cosine rescaling.** Raw sentence-embedding cosines bunch in a narrow band
   (~0.1–0.7 here), so we stretch the informative band to [0,1]. It's a monotonic
   transform — it never reorders two candidates against the same requirement, it
   only restores discrimination the final score can use.

4. **Consistency auditor as a veto, not a signal.** Embeddings can't tell a real
   strong candidate from a keyword-stuffed honeypot (they score the same dense
   similarity — we verified this). So honeypots are caught by internal
   contradiction (tenure vs experience, expert-with-zero-months, impossible
   skill duration), which is role-independent. Thresholds were tuned against the
   real 100K distribution, not guessed (skill duration legitimately runs to ~1.4x
   stated experience, so only the >2.5x tail flags). Result: honeypot rate in
   top-10 drops to 0%.

5. **Schema-driven behavioral scoring.** Availability/engagement/trust are derived
   from whatever signal fields exist, so the engine works on a dataset with a
   different signal vocabulary (verified on an alternate schema).

6. **Whole-token matching.** The original keyword matcher used substring `in`,
   so "ml" matched inside "html"/"xml" for ~54K of 100K candidates. Fixed to
   whole-token matching.

7. **Reasoning grounded in matches.** Each reasoning clause names the requirement
   that matched and the keywords actually present in the candidate's text — so
   there is no hallucination — with tone scaled to rank and honest concerns
   surfaced from the consistency auditor and behavioral signals.

## Compute & reproduction (Stage 3)

- **Spine:** `python3 rank.py --candidates <jsonl> --out <csv>` — pure stdlib,
  ~50s on 100K, no network, CPU-only.
- **Hybrid precompute (offline, ~9 min, allowed to exceed 5 min):**
  `make precompute` builds `outputs/index/` (committed via git-lfs).
- **Hybrid rank step:** `make rank-hybrid` — loads only numpy arrays
  (`np.load(mmap_mode='r')`), dense matmul + argpartition; the rank modules do
  NOT import sentence-transformers or torch (asserted). `HF_HUB_OFFLINE=1` set.
- **Docker:** `docker build` then `docker run --network none --memory 16g` from a
  fresh clone reproduces the CSV in budget.

## Evaluation (Stage 4 / methodology)

`scripts/eval_harness.py` scores any engine over labeled synthetic data across
six suites (per-role, honeypot, paraphrase, perturbation, cross-JD generality,
alternate schema). Headline numbers (hybrid vs spine): mean composite 0.95 vs
0.88; paraphrase top-10 10/10 vs 3/10; honeypot rate@10 0.00 vs 0.20; cross-JD
top-10 overlap ~0.06 (the engine surfaces different people for different JDs —
it is genuinely JD-agnostic). This eval framework is itself a direct
demonstration of the JD's "designing evaluation frameworks" must-have.

## What I would do next

- Tune the dense/lexical alpha and requirement weights against a larger labeled
  set; add learning-to-rank over the factor scores.
- Stronger/longer-context embedding model; embed career-history separately from
  summary to reduce self-promotion bias.
- Online feedback loop (recruiter accept/reject) to calibrate weights.

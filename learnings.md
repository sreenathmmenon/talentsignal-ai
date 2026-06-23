# TalentSignal — Issues Found & Fixes (Learnings)

A running log of real bugs and design issues we identified while building and
hardening the engine, and how each was fixed. Kept as a learning record and as
interview/defense material — most of these were caught by verification, premortem
analysis, or careful review rather than by tests alone.

---

## 1. Substring keyword matching corrupted scores for ~half the pool

**Issue.** The original term matcher used raw substring `in` checks, so `"ml"`
matched inside `"html"`/`"xml"` and `"ai"` inside `"maintain"`. Measured: `"ml"`
matched as a bare substring in **54,564 of 100,000** candidates — silently
inflating `ml_terms` for half the dataset.

**Fix.** `_term_coverage` (scoring.py) now tokenizes to whole tokens and matches
on the token set; a term is covered only if one of its ≥3-char words is a
standalone token. Verified: `"ml"` no longer matches inside `"html"`.

**Lesson.** Substring matching on short tokens is a silent score-corruption bug;
always match whole tokens for skill/keyword signals.

---

## 2. Templated reasoning + tone not matching rank (Stage-4 risk)

**Issue.** The original reasoning used one grammatical skeleton for 99/100 rows
(fails Stage-4 "substantively different / not templated") and read glowing even
at rank 95+ (fails "rank consistency").

**Fix.** Rewrote `reasoning.py` as a rank-aware, varied composer: 15+ skeletons
chosen deterministically per candidate, tone scaled by rank band, honest concerns
surfaced for low ranks, and every cited keyword drawn from the candidate's own
matched evidence (no hallucination by construction).

**Lesson.** "Each string is unique" is not the same as "not templated" — the
rubric tests *structure* and *tone*, not string equality.

---

## 3. Honeypot detection was AI-specific and shallow (~21 of ~80)

**Issue.** The original risk flags were tuned to the AI JD (keyword/title lists)
and caught only ~21 of the ~80 honeypots; they wouldn't generalize to other roles.

**Fix.** Added `consistency_audit.py` — role-independent internal-contradiction
checks (tenure vs stated years, expert-with-zero-months, skill duration vs
experience, date integrity). Each flag names the two contradicting facts.

**Lesson.** Honeypots are defined by *impossibility*, not by keywords — detect
them structurally so the check works for any role and any schema.

---

## 4. Consistency thresholds mis-tuned against real data (9% false-positive)

**Issue.** A first cut of `skill_exceeds_career` compared a skill's duration to
the *summed listed-job tenure*, which is a truncated subset of a real career —
so it flagged **9,304 / 100,000** candidates (~9%) as impossible. Way too broad.

**Fix.** Re-tuned against the real distribution: skill duration legitimately runs
to ~1.4x stated experience (p90), so only the >2.5x tail is genuinely impossible.
Flag rate dropped to a defensible ~0.6%.

**Lesson.** Tune thresholds against the *actual data distribution*, not against an
assumption of what "impossible" looks like.

---

## 5. AI-specific hardcoding leaked into the "general" hybrid path

**Issue.** The hybrid scorer still called the AI-tuned `risk_audit` (hardcoded
`RETRIEVAL_TERMS`/title lists for the Redrob JD), contradicting the JD-agnostic
claim. It was dormant (didn't fire on sales/design) but was a latent role-specific
dependency.

**Fix.** Removed the dependency; the hybrid penalty/eligibility now uses only the
role-independent consistency auditor + semantic disqualifier hits from each JD's
own disqualifiers. Removing it slightly *improved* quality (composite 0.954 →
0.962).

**Lesson.** "Generalizable" must be verified by grepping for hidden role-specific
dependencies, not assumed. The user's pointed question ("will there be any
hardcoding?") surfaced this.

---

## 6. Overstated honeypot recall ("~21 of ~80")

**Issue.** We described detection as "~21 of ~80", implying a known recall against
the true honeypots. But the ground-truth honeypot labels are hidden — 80 is the
spec's claim, 21 is one rule's count.

**Fix (framing).** Corrected to: 10/10 on *labeled synthetic* honeypots, and 0
honeypots in the submitted top-100 (verified). Real recall against the hidden 80
is unknown and not claimed.

**Lesson.** Don't present an estimate as a measured recall when the labels aren't
available; be precise about what's proven vs assumed.

---

## 7. Stage-3 reproduction risk: gitignored embeddings + offline model load

**Issue.** The initial plan gitignored the 154 MB embedding index and documented
"regenerate via `make precompute`." That fails reproduction under both readings of
the spec (no artifact in the checkout; or offline model download fails in the
sandbox).

**Fix.** Commit the index via **git-lfs**; the rank step imports **numpy only**
(asserted by a test — no torch/sentence-transformers at rank time); offline env
flags set; reproduction verified with an offline fresh-environment simulator.

**Lesson.** "OR a script that produces them" is satisfied by *committing the
artifact*; don't bet reproduction on an offline model download.

---

## 8. Facade crashed on malformed candidate records (KeyError)

**Issue.** `rank()` raised `KeyError: 'profile'` on a partial/malformed record —
unacceptable for a product ingesting real-world data.

**Fix.** `_safe_records` in the facade defensively normalizes incoming records
(missing blocks, no id, non-dict junk) so a bad candidate degrades instead of
crashing. Added a hardening test suite.

**Lesson.** A production ranking API must degrade, not throw, on hostile input.

---

## 9. Explanation auditor false-flagged grounded hybrid reasoning

**Issue.** The legacy explanation auditor whitelisted reasoning terms against the
*spine's* narrow evidence-term fields, which hybrid packets don't populate the
same way — so it flagged genuinely grounded terms (e.g. "recommendation" /
"retrieval" / "ranking", which *were* in the candidate's profile) as
"unsupported."

**Fix.** Hybrid reasoning only cites keywords whole-token matched against the
candidate's own text (grounding guaranteed by construction and separately tested),
so the auditor skips the spine-term whitelist for hybrid packets. Audit on the
submission: 0 warnings.

**Lesson.** When the engine changes, audit tooling tuned to the old engine can
produce false alarms — verify a flag against ground truth before trusting it.

---

## 10. Consistency check mis-tokenized multi-word skills → penalized a strong candidate

**Issue (user-caught).** The old Codex engine consistently ranked a Microsoft AI
Engineer from Trivandrum (`CAND_0079387`) at #1–2. Our hybrid engine dropped it
**out of the top 100**. Root cause: `skill_not_in_evidence` matched skill names by
exact token-set intersection, so "Sentence Transformers" (skill) didn't match
"sentence-transformers" (text) and "scikit-learn" tokenized inconsistently — it
falsely reported "7 of 8 expert skills never appear in career text" when **all 8
were present**, applying a 0.10 penalty that sank a legitimate candidate.

**Fix.** `_evidence_blob` normalizes separators (`/ - .` → space) and the skill
check matches on significant words (punctuation/spacing-insensitive); the flag now
fires only when *all* (≥5) expert skills are genuinely absent (true
keyword-stuffing), not a fuzzy 80%. After the fix the Microsoft candidate returns
to **#10**, honeypots still 10/10 caught, full-pool flag rate 0.69% → 0.58%,
submission still valid.

**Lesson.** False positives in a penalty/veto can be as damaging as missed
honeypots — they silently sink good candidates. The user's memory of the old
results ("always a Trivandrum candidate at #1") was the signal that caught this;
human cross-checks against prior behavior matter. Always normalize tokenization
consistently across the two things you're comparing.

---

## 11. Free-text resume parsing was weak — broke ranking on real input

**Issue (found via real-JD test).** Running a real GitLab Senior AI Engineer JD
against paste-style resumes, a keyword-stuffer ranked #2 above genuinely strong
candidates, and `career_fit` was 0 for everyone. Root cause: the local resume
parser only recognized clean "Title at Company DATE" lines. On a fixture suite of
6 realistic messy resumes (paragraph, split-date, ALL-CAPS/pipe, terse,
bullets-with-dates, keyword-stuffer), only **1 of 6 parsed correctly** — the rest
lost skills, career, title, or years, and that under-extraction flowed straight
into bad rankings (a profile with no parsed career can't be scored on career fit,
so the engine leans on the skills dump, which is exactly where stuffers win).

**Fix.** Rewrote `resume_parser.py`: a skills gazetteer fallback (recover known
tech skills mentioned anywhere, plus inline "Skills: a, b"), robust section
detection (ALL-CAPS, "WORK HISTORY", "SKILLS:"), multi-format career grouping
(title-at-company, pipe format, and the common title/company/date split layout),
title inference from free text, and a synthesized role for paragraph/terse
resumes. Result: **6/6 fixtures parse**. Re-running the real GitLab JD: the two
best fits are now #1/#2, the keyword-stuffer dropped to #5, and an
under-marketed terse resume correctly rose to #3. The optional LLM-assist mode is
wired (activates with ANTHROPIC_API_KEY) for messy real resumes, with graceful
local fallback.

**Lesson.** A ranking engine is only as good as the structure it can extract from
real input. Synthetic *structured* data hid this entirely — testing on realistic
*unstructured* input is what exposed it. "Works on the benchmark" ≠ "works on real
resumes." Build a fixture suite of messy real-world inputs and gate on it.

## Cross-cutting lessons

- **Verify claims against data, not memory.** Multiple "facts" we stated needed
  correcting once checked (substring extent, honeypot recall, the false-positive
  hallucination example, the skill-evidence flag).
- **Keep a guaranteed-valid floor.** The zero-dependency spine engine always
  produces a valid CSV, so aggressive changes to the hybrid engine never risk an
  unsubmittable state.
- **Premortem early.** The biggest risks (semantic mis-ranking honeypots up,
  Stage-3 reproduction, over-scoping) were all predicted by adversarial premortem
  before they could bite.

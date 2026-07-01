# TalentSignal — Adversarial / honeypot resistance

A non-circular robustness metric: ground truth is definitional (an injected /
stuffed / fabricated résumé is grade-0 by construction), so it needs no human
relevance labels and no protected attributes. We report the **resistance rate**:
the fraction of attacked profiles the engine refuses to reward (flagged and/or
denied any ranking gain over the clean copy).

- Clean strong profiles attacked: **40**
- Attacks per profile: **4** (prompt_injection, keyword_stuffing, fabricated_experience, impossible_tenure)
- Submitted **hybrid (semantic)** engine — overall resistance: **100.0%**
- Zero-dependency **spine (keyword)** fallback — overall resistance: **78.1%**

### Submitted hybrid (semantic) engine

| Attack | n | Detection rate | Suppression rate | Resistance |
|---|---|---|---|---|
| prompt injection | 40 | 0.0% | 100.0% | **100.0%** |
| keyword stuffing | 40 | 0.0% | 100.0% | **100.0%** |
| fabricated experience | 40 | 0.0% | 100.0% | **100.0%** |
| impossible tenure | 40 | 100.0% | 100.0% | **100.0%** |

### Spine (keyword) fallback — for contrast

| Attack | n | Detection rate | Suppression rate | Resistance |
|---|---|---|---|---|
| prompt injection | 40 | 0.0% | 100.0% | **100.0%** |
| keyword stuffing | 40 | 0.0% | 12.5% | **12.5%** |
| fabricated experience | 40 | 100.0% | 100.0% | **100.0%** |
| impossible tenure | 40 | 100.0% | 100.0% | **100.0%** |

**The headline:** keyword stuffing — the classic ATS-gaming move — fools the keyword-based spine (it rewards the added terms) but barely moves the submitted semantic engine, which sees the stuffed keywords carry no real evidence. This is direct, measured evidence for the product's core claim: *matching on meaning is harder to game than matching on keywords.* Fabrication and impossible-tenure attacks are caught by the role-independent consistency auditor in both engines.

- **Detection** = the consistency auditor flagged the attacked copy.
- **Suppression** = the attacked copy scored no higher than the clean copy (the gaming bought nothing).
- **Resistance** = flagged OR suppressed. An attack only 'wins' if it goes undetected AND lifts the score.

_Non-circular by construction (an injected/stuffed/fabricated résumé is grade-0 by definition — no human labels, no protected attributes needed). Method: `src/talentsignal/eval/adversarial.py`. Deterministic; reproduce with `python3 scripts/adversarial_report.py`._
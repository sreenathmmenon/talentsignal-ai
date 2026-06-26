"""Reasoning composer: grounded, varied, tone matches rank, concerns surfaced —
the six Stage-4 manual-review checks.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from talentsignal import artifacts
from talentsignal.jd_parser import load_job_spec
from talentsignal.ranking import rank_records_hybrid
from talentsignal.eval import datasets as D
from talentsignal.eval.roles import AI_SEARCH

JOB = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")


def _rank_pool(mix=None):
    pool = D.build_pool(AI_SEARCH, mix=mix)
    recs = D.records_of(pool)
    # deterministic synthetic embeddings keyed off archetype so dense channel is
    # meaningful without loading a model: strong/paraphrase near requirement vec.
    dim = 16
    base = np.zeros(dim, dtype="float32"); base[0] = 1.0
    off = np.zeros(dim, dtype="float32"); off[1] = 1.0
    arche = {c.candidate_id: c.archetype for c in pool}
    emb = []
    for c in recs:
        a = arche[c["candidate_id"]]
        v = base if a in (D.STRONG, D.PARAPHRASE_IDEAL, D.ADJACENT, D.HONEYPOT) else off
        emb.append(v)
    emb = np.stack(emb)
    id2row = {c["candidate_id"]: i for i, c in enumerate(recs)}
    reqemb = np.tile(base, (len(JOB.requirements), 1)).astype("float32")
    rows = rank_records_hybrid(recs, JOB, top_n=len(recs),
                               candidate_embeddings=(id2row, emb), req_embeddings=reqemb)
    return recs, rows


def test_reasonings_are_unique_and_varied() -> None:
    _, rows = _rank_pool()
    reasons = [r["reasoning"] for r in rows]
    # no two identical
    assert len(set(reasons)) == len(reasons)
    # not one grammatical skeleton: several distinct opening words across rows
    openers = {r.split()[0] for r in reasons}
    assert len(openers) >= 3


def test_tone_matches_rank() -> None:
    _, rows = _rank_pool()
    top = rows[0]["reasoning"].lower()
    bottom = rows[-1]["reasoning"].lower()
    assert any(w in top for w in ("strong", "clear", "top", "solid", "standout", "recommendation"))
    # the very bottom should read as borderline / caveated, not glowing
    assert any(w in bottom for w in ("borderline", "caveat", "cutoff", "bubble", "maybe",
                                     "flag", "thin", "partial", "human look", "near the cutoff"))


def test_concerns_surface_for_honeypots() -> None:
    recs, rows = _rank_pool()
    by_id = {c["candidate_id"]: c for c in recs}
    # any honeypot that appears should carry a flagged concern (contradiction named)
    labels = {c.candidate_id: c.archetype for c in D.build_pool(AI_SEARCH)}
    for r in rows:
        if labels.get(r["candidate_id"]) == D.HONEYPOT:
            low = r["reasoning"].lower()
            assert "flag" in low or "concern" in low


def test_reasoning_keywords_are_grounded() -> None:
    # every keyword the reasoning cites in parentheses must appear as a whole
    # token in the candidate's own evidence text (no hallucination).
    recs, rows = _rank_pool()
    by_id = {c["candidate_id"]: c for c in recs}
    import re
    for r in rows[:20]:
        cand = by_id[r["candidate_id"]]
        tokens = set(re.findall(r"[a-z0-9+#./\-]{3,}", artifacts.evidence_text_of(cand).lower()))
        for grp in re.findall(r"\(([^)]+)\)", r["reasoning"]):
            for kw in [k.strip() for k in grp.split(",")]:
                # skip percentages / numbers / multiword phrases
                if kw and kw.isalpha() and len(kw) >= 3 and " " not in kw:
                    assert kw in tokens, f"hallucinated keyword '{kw}' for {r['candidate_id']}"

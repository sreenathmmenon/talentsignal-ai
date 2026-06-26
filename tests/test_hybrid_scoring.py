"""Unified hybrid scoring: the same JD-requirement-weighted path scores any role,
fixes the substring bug, applies the consistency veto, and produces additive
ScoreBreakdown fields without breaking the spine.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from talentsignal.features import build_evidence
from talentsignal.jd_parser import load_job_spec
from talentsignal.ranking import rank_records_hybrid
from talentsignal.scoring import _term_coverage, score_candidate
from talentsignal.eval import datasets as D
from talentsignal.eval.roles import AI_SEARCH


def test_substring_bug_fixed_whole_token_only() -> None:
    # The core bug: multi-char skill words must match as whole tokens only.
    # 'ranking' must not match inside 'rerankings'/'cranking' substrings, and a
    # real standalone token must match.
    assert _term_coverage("i maintain the html and xml templates", ("ranking",)) == 0.0
    assert _term_coverage("i built a ranking system", ("ranking",)) == 1.0
    # Graded coverage: a single-word term present is full (1.0); a multi-word term
    # with only ONE of its words present gets PARTIAL credit (0.4), so coincidental
    # single-word overlaps can't fully "cover" a requirement (the off-role leak fix).
    assert _term_coverage("strong python and sql", ("python",)) == 1.0
    assert _term_coverage("strong python and sql", ("python skills",)) == 0.4
    assert _term_coverage("python skills are strong", ("python skills",)) == 1.0  # both words
    assert _term_coverage("i streamline reports", ("ml",)) == 0.0  # 'ml' inside streamline must not match


def test_score_breakdown_has_additive_fields_default() -> None:
    # spine path still works and defaults the new fields
    job = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")
    c = D.make_candidate(AI_SEARCH, D.STRONG, 0).record
    sb = score_candidate(build_evidence(c), job)
    assert sb.engine == "spine"
    assert sb.semantic_fit == 0.0  # default
    assert hasattr(sb, "requirement_coverage")


def test_hybrid_ranks_strong_above_irrelevant_lexical_only() -> None:
    # Without embeddings the hybrid path degrades to lexical-only but still ranks.
    job = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")
    pool = D.build_pool(AI_SEARCH, mix={D.STRONG: 5, D.IRRELEVANT: 5, D.HONEYPOT: 5})
    records = D.records_of(pool)
    rows = rank_records_hybrid(records, job, top_n=len(records))  # no index -> lexical-only
    order = [r["candidate_id"] for r in rows]
    labels = {c.candidate_id: c.archetype for c in pool}
    top5 = [labels[c] for c in order[:5]]
    # honeypots must not dominate the top
    assert top5.count(D.HONEYPOT) <= 1


def test_hybrid_consistency_veto_blocks_honeypot_top10() -> None:
    # Realistic pool: enough genuine fits to fill the top-10, plus many honeypots.
    # The veto must keep honeypots out of the top-10 entirely.
    job = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")
    pool = D.build_pool(AI_SEARCH, mix={D.STRONG: 14, D.ADJACENT: 8, D.HONEYPOT: 20})
    records = D.records_of(pool)
    rows = rank_records_hybrid(records, job, top_n=10)
    labels = {c.candidate_id: c.archetype for c in pool}
    top10 = [labels[r["candidate_id"]] for r in rows]
    assert top10.count(D.HONEYPOT) == 0  # consistency veto keeps honeypots out


def test_hybrid_dense_lifts_paraphrase_over_lexical() -> None:
    # With perfect synthetic embeddings, a paraphrase (zero keyword) candidate
    # should beat a lexical-only ranking. We fake embeddings: requirement vec and
    # the paraphrase candidate vec aligned; irrelevant orthogonal.
    job = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")
    para = D.make_candidate(AI_SEARCH, D.PARAPHRASE_IDEAL, 0).record
    irr = D.make_candidate(AI_SEARCH, D.IRRELEVANT, 0).record
    records = [para, irr]
    dim = 8
    aligned = np.ones(dim, dtype="float32")
    ortho = np.zeros(dim, dtype="float32"); ortho[0] = 1.0
    # must/nice requirements point to 'aligned' (para matches them); DISQUALIFIER
    # requirements point orthogonal so the paraphrase does NOT trip the (now hard)
    # disqualifier veto — we are testing semantic lift, not the veto.
    req_emb = np.stack([
        aligned if r.kind != "disqualifier" else ortho for r in job.requirements
    ]).astype("float32")
    id_to_row = {para["candidate_id"]: 0, irr["candidate_id"]: 1}
    emb = np.stack([aligned, ortho]).astype("float32")
    rows = rank_records_hybrid(records, job, top_n=2,
                               candidate_embeddings=(id_to_row, emb), req_embeddings=req_emb)
    assert rows[0]["candidate_id"] == para["candidate_id"]

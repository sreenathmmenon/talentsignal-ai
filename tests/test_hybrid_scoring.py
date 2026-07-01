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


# ---- Availability / reachability (HR council decision) ----

def _cand_with_signals(**signals):
    """A minimal but relevance-identical AI candidate; only signals vary."""
    base = D.make_candidate(AI_SEARCH, D.STRONG, 0).record
    base = dict(base)
    base["redrob_signals"] = {**base.get("redrob_signals", {}), **signals}
    return base


def test_open_to_work_never_vetoes() -> None:
    # A not-open candidate must still be scored and rank-eligible (no hard veto).
    job = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")
    c = _cand_with_signals(open_to_work_flag=False, last_active_date="2026-05-20",
                           recruiter_response_rate=0.8)
    sb = score_candidate(build_evidence(c), job)
    assert sb.final_score > 0.0  # availability alone never zeroes a qualified candidate


def test_missing_flag_is_neutral_between_true_and_false() -> None:
    # unknown != available and unknown != unavailable: a missing flag must score
    # strictly between an explicit True and an explicit False on identical profiles.
    from talentsignal.scoring import _open_to_work_term
    from talentsignal.features import build_evidence as be
    common = dict(last_active_date="2026-06-01", recruiter_response_rate=0.7)
    t = _open_to_work_term(be(_cand_with_signals(open_to_work_flag=True, **common)))
    f = _open_to_work_term(be(_cand_with_signals(open_to_work_flag=False, **common)))
    # build a candidate whose signal block has NO open_to_work_flag key
    miss_rec = _cand_with_signals(**common)
    miss_rec["redrob_signals"].pop("open_to_work_flag", None)
    m = _open_to_work_term(be(miss_rec))
    assert f < m < t, (f, m, t)


def test_passive_active_outranks_open_but_stale() -> None:
    # The brief's rule: a not-open-but-recently-active + responsive candidate should
    # not be beaten on availability by an open-but-stale, unresponsive one.
    from talentsignal.scoring import reachability
    from talentsignal.features import build_evidence as be
    passive_active = be(_cand_with_signals(
        open_to_work_flag=False, last_active_date="2026-05-25", recruiter_response_rate=0.85))
    open_stale = be(_cand_with_signals(
        open_to_work_flag=True, last_active_date="2024-09-01", recruiter_response_rate=0.05))
    lab_p, r_p = reachability(passive_active)
    lab_s, r_s = reachability(open_stale)
    assert r_p > r_s
    assert lab_p == "passive" and lab_s == "stale"


def test_stale_flag_decays_toward_neutral() -> None:
    # An OLD flag (either direction) should be trusted less: a stale not-open scores
    # closer to neutral than a fresh not-open.
    from talentsignal.scoring import _open_to_work_term
    from talentsignal.features import build_evidence as be
    fresh_no = _open_to_work_term(be(_cand_with_signals(
        open_to_work_flag=False, last_active_date="2026-06-01")))
    stale_no = _open_to_work_term(be(_cand_with_signals(
        open_to_work_flag=False, last_active_date="2024-01-01")))
    assert stale_no > fresh_no  # penalty relaxes as the flag ages


def test_disqualifier_veto_guarded_by_coverage():
    """A semantic disqualifier hit HARD-vetoes only when the candidate lacks
    must-have coverage. A strong candidate (high coverage) who merely overlaps a
    disqualifier term is soft-penalised, not zeroed — prevents false-veto loss of
    genuinely strong candidates (measured ~6/100k in the real pool)."""
    from talentsignal.scoring import score_candidate_hybrid
    from talentsignal.semantic_match import MatchResult
    from talentsignal.consistency_audit import audit_candidate
    from talentsignal.schema_profile import schema_signals
    job = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")
    rec = D.make_candidate(AI_SEARCH, D.STRONG, 0).record
    ev = build_evidence(rec)
    sig = schema_signals(rec)
    con = audit_candidate(rec)
    # weak coverage + disqualifier hit -> hard veto (score 0)
    weak = MatchResult(semantic_fit=0.6, lexical_fit=0.4, disqualifier_hit=0.7,
                       requirement_matches=[], coverage=0.2)
    sb_weak = score_candidate_hybrid(ev, job, match_result=weak, schema_sig=sig, consistency=con)
    assert sb_weak.final_score == 0.0
    # strong coverage + same disqualifier hit -> NOT vetoed (soft-penalised only)
    strong = MatchResult(semantic_fit=0.6, lexical_fit=0.4, disqualifier_hit=0.7,
                         requirement_matches=[], coverage=0.8)
    sb_strong = score_candidate_hybrid(ev, job, match_result=strong, schema_sig=sig, consistency=con)
    assert sb_strong.final_score > 0.0

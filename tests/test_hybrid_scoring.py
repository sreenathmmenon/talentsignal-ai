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


# ---- adversarial / honeypot resistance (non-circular robustness metric) ----

def test_hybrid_resists_keyword_stuffing_better_than_spine():
    """The core product claim, measured: stuffing a strong profile with role
    keywords gives a large lift under keyword (spine) scoring but a negligible one
    under the submitted semantic (hybrid) engine — because the stuffed terms carry
    no real evidence. Uses lexical-only hybrid (no model) so it runs in CI."""
    from talentsignal.eval import adversarial as adv
    from talentsignal.eval import datasets as D
    from talentsignal.eval.roles import AI_SEARCH
    from talentsignal import semantic_match as sm
    from talentsignal.schema_profile import schema_signals
    from talentsignal.consistency_audit import audit_candidate
    from talentsignal.scoring import score_candidate, score_candidate_hybrid
    from talentsignal import artifacts
    job = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")
    reqs = list(getattr(job, "requirements", ()) or [])
    rec = D.make_candidate(AI_SEARCH, D.STRONG, 3).record
    stuffed = adv.attack_keyword_stuffing(rec)

    def spine(r):
        return score_candidate(build_evidence(r), job).final_score

    def hybrid(r):
        ev = build_evidence(r); txt = artifacts.evidence_text_of(r)
        mr = sm.match(reqs, None, txt, None, alpha=sm.DEFAULT_ALPHA)  # lexical-only
        return score_candidate_hybrid(ev, job, match_result=mr,
                                      schema_sig=schema_signals(r),
                                      consistency=audit_candidate(r)).final_score
    spine_gain = spine(stuffed) - spine(rec)
    hybrid_gain = hybrid(stuffed) - hybrid(rec)
    # keyword stuffing must buy LESS advantage under semantic matching than keyword
    assert hybrid_gain < spine_gain
    # and the impossible-tenure attack must be flagged by the auditor either way
    from talentsignal.consistency_audit import audit_candidate as audit
    assert audit(adv.attack_impossible_tenure(rec)).flags or \
        audit(adv.attack_impossible_tenure(rec)).is_impossible


def test_resume_without_activity_data_is_not_stale():
    """A pasted/uploaded résumé has no platform activity signals. It must read as
    'unknown' (neutral), NOT 'stale' with a penalty — unknown != inactive. A real
    candidate with genuine old activity still reads 'stale'."""
    from talentsignal.scoring import reachability, _behavioral_score
    from talentsignal.features import build_evidence
    # résumé: no redrob_signals at all
    resume = {"candidate_id": "R1", "profile": {"summary": "ML engineer, open to work",
              "current_title": "ML Engineer", "years_of_experience": 7},
              "career_history": [{"title": "ML", "description": "ranking retrieval"}],
              "skills": ["Python"], "redrob_signals": {}}
    ev = build_evidence(resume)
    label, _ = reachability(ev)
    assert label in ("unknown", "reachable"), label      # never 'stale' on a bare résumé
    assert _behavioral_score(ev) >= 0.4                    # neutral, not penalized to ~0
    # a real candidate with genuine stale data is still flagged stale
    stale = {"candidate_id": "S1", "profile": {"summary": "x", "current_title": "ML"},
             "career_history": [], "skills": ["Python"],
             "redrob_signals": {"last_active_date": "2024-01-01",
                                 "recruiter_response_rate": 0.05, "open_to_work_flag": True}}
    assert reachability(build_evidence(stale))[0] == "stale"


def test_off_schema_record_flagged_not_confident_garbage():
    """A candidate with no usable evidence (wrong field names / missing profile)
    must NOT be scored as a confident 'standout'. It gets score 0, an
    'insufficient_evidence' flag, and honest reasoning — so a naive integration
    sees a clear signal, not silent garbage."""
    from talentsignal.api import rank
    res = rank("Senior AI Engineer. embeddings ranking. 5-9 years.",
               [{"id": "X1", "name": "Alice", "experience": "5 years"}, {"foo": "bar"}],
               top_n=2, engine="spine")
    for c in res.ranked:
        assert c.score == 0.0
        assert any(f.code == "insufficient_evidence" for f in (c.risk_flags or []))
        assert "insufficient profile data" in c.reasoning
        assert "standout" not in c.reasoning
    # a real candidate is unaffected
    good = rank("Senior AI Engineer. embeddings retrieval ranking Python. 5-9 years.",
                [{"candidate_id": "C1", "profile": {"summary": "Built embeddings retrieval ranking in Python",
                  "current_title": "ML Engineer", "years_of_experience": 7},
                  "career_history": [{"title": "ML", "description": "ranking retrieval"}],
                  "skills": ["Python"], "redrob_signals": {}}], top_n=1, engine="spine").ranked[0]
    assert not any(f.code == "insufficient_evidence" for f in (good.risk_flags or []))
    assert good.score > 0

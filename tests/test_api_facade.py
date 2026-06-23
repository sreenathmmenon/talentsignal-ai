"""The public engine facade: one clean rank(jd, candidates) -> typed RankResult,
accepting any JD form, with serialization for every surface.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.api import rank, TalentSignal, RankResult, RankedCandidate
from talentsignal.eval import datasets as D
from talentsignal.eval.roles import SALES


def _pool():
    return D.records_of(D.build_pool(SALES, mix={D.STRONG: 5, D.IRRELEVANT: 5, D.HONEYPOT: 3}))


def test_rank_from_free_text_jd_returns_typed_result() -> None:
    recs = _pool()
    res = rank("Enterprise Account Executive. Must have enterprise quota and pipeline generation. "
               "4-9 years. Mumbai.", recs, top_n=5, engine="spine", category="sales_gtm")
    assert isinstance(res, RankResult)
    assert res.candidate_count == len(recs)
    assert len(res.ranked) == 5
    assert all(isinstance(c, RankedCandidate) for c in res.ranked)
    # ranks are 1..5 unique, scores non-increasing
    assert [c.rank for c in res.ranked] == [1, 2, 3, 4, 5]
    assert all(res.ranked[i].score >= res.ranked[i + 1].score for i in range(4))


def test_rank_from_yaml_path() -> None:
    res = rank("job_specs/examples/enterprise_account_executive.yaml", _pool(), top_n=3, engine="spine")
    assert res.job_id == "enterprise_account_executive"
    assert len(res.ranked) == 3


def test_result_serialization_shapes() -> None:
    res = rank("Senior AI Engineer needs embeddings and ranking experience.", _pool(),
               top_n=3, engine="spine")
    d = res.to_dict()
    for k in ("job_title", "engine", "candidate_count", "ranked", "requirements", "api_version"):
        assert k in d
    # csv rows match the challenge submission shape
    rows = res.to_csv_rows()
    assert list(rows[0].keys()) == ["candidate_id", "rank", "score", "reasoning"]


def test_reusable_handle() -> None:
    ts = TalentSignal()
    a = ts.rank("Sales role, enterprise quota.", _pool(), top_n=2, engine="spine", category="sales_gtm")
    b = ts.rank("Sales role, enterprise quota.", _pool(), top_n=2, engine="spine", category="sales_gtm")
    assert [c.candidate_id for c in a.ranked] == [c.candidate_id for c in b.ranked]  # deterministic


def test_hybrid_without_index_degrades_gracefully() -> None:
    # no index, no embedder -> hybrid runs lexical-only, still returns a result + a note
    res = rank("Enterprise quota and pipeline.", _pool(), top_n=3, engine="hybrid", category="sales_gtm")
    assert len(res.ranked) == 3
    assert any("lexical-only" in n for n in res.notes)


def test_factor_breakdown_present() -> None:
    res = rank("Sales role.", _pool(), top_n=1, engine="spine", category="sales_gtm")
    c = res.ranked[0]
    assert c.factors is not None
    assert 0.0 <= c.factors.technical_evidence <= 1.0

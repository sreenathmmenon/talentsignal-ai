"""Batch / file ergonomics — the enterprise-scale SDK entry points: rank_file
(streamed), rank_many_jds (one pool, many roles, each with its own category), and
rank_to_csv.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.api import rank_file, rank_many_jds, rank_to_csv
from talentsignal.eval import datasets as D
from talentsignal.eval.roles import AI_SEARCH, SALES


def test_rank_many_jds_uses_per_jd_category():
    # mixed pool: AI engineers + sales people; each JD must surface its OWN role
    pool = (D.records_of(D.build_pool(AI_SEARCH, mix={D.STRONG: 5}))
            + D.records_of(D.build_pool(SALES, mix={D.STRONG: 5})))
    titles = {c["candidate_id"]: c["profile"]["current_title"].lower() for c in pool}
    jds = {"ai": "Senior AI Engineer. embeddings retrieval ranking evaluation. 5-9y.",
           "sales": "Enterprise Account Executive. enterprise quota pipeline CRM closing deals. 4-9y."}
    cats = {"ai": "ai_ml_search_ranking", "sales": "sales_gtm"}
    res = rank_many_jds(jds, pool, top_n=3, engine="spine", categories=cats)
    ai_top = [titles[c.candidate_id] for c in res["ai"].ranked]
    sales_top = [titles[c.candidate_id] for c in res["sales"].ranked]
    assert any("engineer" in t for t in ai_top)
    assert any("account" in t or "sales" in t for t in sales_top)
    # the two role rankings must NOT be identical (the bug we fixed)
    assert [c.candidate_id for c in res["ai"].ranked] != [c.candidate_id for c in res["sales"].ranked]


def test_rank_file_streams(tmp_path):
    import json
    pool = D.records_of(D.build_pool(AI_SEARCH, mix={D.STRONG: 4, D.IRRELEVANT: 4}))
    f = tmp_path / "cands.jsonl"
    f.write_text("\n".join(json.dumps(c) for c in pool))
    res = rank_file("Senior AI Engineer. embeddings ranking. 5-9y.", f, top_n=3, engine="spine")
    assert res.candidate_count == 8
    assert len(res.ranked) == 3


def test_rank_to_csv(tmp_path):
    pool = D.records_of(D.build_pool(AI_SEARCH, mix={D.STRONG: 3, D.WEAK: 3}))
    out = tmp_path / "out.csv"
    rank_to_csv("Senior AI Engineer. 5-9y.", pool, out, top_n=4, engine="spine")
    rows = list(csv.DictReader(open(out)))
    assert list(rows[0].keys()) == ["candidate_id", "rank", "score", "reasoning"]
    assert len(rows) == 4
    assert [int(r["rank"]) for r in rows] == [1, 2, 3, 4]

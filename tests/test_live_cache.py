"""Live ranking cache — the infra that lets the Studio serve the 100K instantly
AND guarantees a re-rank when the candidate pool changes (no stale results). These
tests use a small temp dataset so they're fast, and exercise the correctness
property that matters most: a data change MUST invalidate the cache."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

import talentsignal.live_cache as LC


def _records(n, ai=True):
    out = []
    for i in range(n):
        kind = ("embeddings retrieval ranking python ndcg" if ai
                else "marketing brand campaigns social media")
        out.append({
            "candidate_id": f"CAND_{i:07d}",
            "profile": {"anonymized_name": f"P{i}", "headline": "AI Engineer" if ai else "Marketer",
                        "summary": f"{kind} candidate {i}", "years_of_experience": 7,
                        "current_title": "AI Engineer" if ai else "Marketer"},
            "career_history": [{"title": "Engineer", "description": kind, "duration_months": 84}],
            "education": [], "skills": ["Python"], "certifications": [], "languages": ["English"],
            "redrob_signals": {"open_to_work_flag": True, "recruiter_response_rate": 0.7},
        })
    return out


@pytest.fixture
def temp_dataset(tmp_path, monkeypatch):
    """Point live_cache at a small temp jsonl and reset its module state."""
    ds = tmp_path / "candidates.jsonl"
    ds.write_text("\n".join(json.dumps(r) for r in _records(40)) + "\n", encoding="utf-8")
    monkeypatch.setattr(LC, "_DATASET", ds)
    LC._records = None
    LC._records_fp = None
    LC.invalidate()
    return ds


def test_ranks_and_returns_payload(temp_dataset):
    r = LC.rank_live("AI Engineer. Must have embeddings, retrieval, ranking, Python. 5-9 years.",
                     engine="spine", top_n=5)
    assert r["total"] == 40
    assert len(r["top"]) == 5
    assert r["from_cache"] is False
    assert r["engine"] == "spine"
    # every row carries the explainable fields
    c = r["top"][0]
    assert {"rank", "candidate_id", "score", "reasoning", "factors"} <= set(c)


def test_second_call_is_cached(temp_dataset):
    jd = "AI Engineer. Must have embeddings, retrieval, ranking, Python. 5-9 years."
    LC.rank_live(jd, engine="spine", top_n=5)
    again = LC.rank_live(jd, engine="spine", top_n=5)
    assert again["from_cache"] is True


def test_new_candidate_invalidates_cache(temp_dataset):
    """The property that matters: adding a candidate must force a live re-rank,
    so a newly-applied strong candidate is never hidden by a stale cache."""
    jd = "AI Engineer. Must have embeddings, retrieval, ranking, Python. 5-9 years."
    first = LC.rank_live(jd, engine="spine", top_n=10)
    fp1 = first["pool_fingerprint"]
    # append a new candidate and bump mtime so the file fingerprint changes
    with open(temp_dataset, "a") as f:
        f.write(json.dumps(_records(1)[0] | {"candidate_id": "CAND_NEWSTAR"}) + "\n")
    os.utime(temp_dataset, (time.time() + 5, time.time() + 5))
    after = LC.rank_live(jd, engine="spine", top_n=10)
    assert after["from_cache"] is False           # re-ranked, not stale
    assert after["total"] == 41
    assert after["pool_fingerprint"] != fp1       # content fingerprint changed


def test_removing_candidate_returns_to_identical_pool_cache(temp_dataset):
    """Removing the added candidate returns the EXACT original pool, so serving the
    original cached result is correct (same data == same answer), not stale."""
    jd = "AI Engineer. Must have embeddings, retrieval, ranking, Python. 5-9 years."
    first = LC.rank_live(jd, engine="spine", top_n=10)
    fp1 = first["pool_fingerprint"]
    with open(temp_dataset, "a") as f:
        f.write(json.dumps(_records(1)[0] | {"candidate_id": "CAND_NEWSTAR"}) + "\n")
    os.utime(temp_dataset, (time.time() + 5, time.time() + 5))
    LC.rank_live(jd, engine="spine", top_n=10)    # re-rank with 41
    # remove it -> back to the identical 40-record pool
    keep = [l for l in open(temp_dataset) if "CAND_NEWSTAR" not in l]
    open(temp_dataset, "w").writelines(keep)
    os.utime(temp_dataset, (time.time() + 9, time.time() + 9))
    back = LC.rank_live(jd, engine="spine", top_n=10)
    assert back["pool_fingerprint"] == fp1        # identical pool == original fingerprint


def test_warm_precomputes_standing_jd(temp_dataset):
    LC.invalidate()
    res = LC.warm(engine="spine", top_n=10)
    assert not res.get("error")
    # the warmed result is now cached for the challenge route's key
    cached = LC.rank_live(LC.CHALLENGE_JD, engine="spine", top_n=10)
    assert cached["from_cache"] is True


def test_missing_dataset_returns_error(tmp_path, monkeypatch):
    monkeypatch.setattr(LC, "_DATASET", tmp_path / "nope.jsonl")
    LC._records = None
    LC.invalidate()
    r = LC.rank_live("AI Engineer. Must have python. 5-9 years.", engine="spine")
    assert "error" in r

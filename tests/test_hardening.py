"""Hardening: the engine and ingest layer degrade gracefully on malformed,
partial, or hostile input instead of crashing — a production requirement.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.api import rank
from talentsignal.ingest import ingest


def test_rank_handles_partial_records() -> None:
    for recs in (
        [{"candidate_id": "CAND_0000001"}],            # missing profile/career/...
        [{"profile": {"current_title": "X"}}],          # missing candidate_id
        [{}],                                            # empty dict
        ["not a dict", {"candidate_id": "CAND_0000002"}],  # mixed junk
    ):
        res = rank("AI Engineer: ranking, embeddings.", recs, top_n=2)
        assert len(res.ranked) >= 1
        assert res.ranked[0].reasoning is not None


def test_rank_handles_explicitly_null_and_mistyped_fields() -> None:
    # real-world exports have keys present with null values, or wrong types —
    # these must degrade, not crash (regression test for a found bug).
    cases = [
        [{"candidate_id": "CAND_0000001", "profile": {"summary": None, "years_of_experience": None},
          "career_history": None, "skills": None, "redrob_signals": None}],
        [{"candidate_id": None, "profile": None}],
        [{"candidate_id": "CAND_0000001", "profile": "oops"}],   # profile wrong type
        [{"candidate_id": "CAND_0000001", "skills": {"a": 1}}],   # skills wrong type
    ]
    for recs in cases:
        res = rank("AI Engineer", recs, top_n=3, engine="spine")
        assert len(res.ranked) >= 1


def test_rank_empty_pool() -> None:
    res = rank("AI Engineer", [], top_n=10)
    assert res.ranked == []
    assert res.candidate_count == 0


def test_ingest_empty_and_garbage() -> None:
    assert ingest("", fmt="text") == []
    assert ingest("   \n  ", fmt="text") == []
    assert ingest("[]", fmt="json") == []
    # garbage text still produces a (low-confidence) record rather than crashing
    assert len(ingest("!!!@#$%^&*()", fmt="text")) == 1


def test_ingest_huge_input_bounded() -> None:
    big = "Skills\n" + ", ".join(f"skill{i}" for i in range(1000))
    recs = ingest(big, fmt="text")
    assert len(recs) == 1
    assert len(recs[0]["skills"]) <= 30  # skills are capped, not unbounded


def test_malformed_json_falls_back_to_text() -> None:
    # a string that isn't valid JSON shouldn't raise; text adapter handles it
    recs = ingest("{not valid json", fmt="text")
    assert len(recs) == 1

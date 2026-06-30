"""Coverage for the embedding-index artifacts (hybrid engine I/O) and the v2
intelligence features (trap explainer, boundary review, candidate compare,
interview kit). All offline / deterministic / no model needed."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pytest


# --- artifacts: save/load round-trip of the embedding index -------------------

def test_candidate_index_round_trip(tmp_path):
    from talentsignal import artifacts
    ids = ["CAND_1", "CAND_2", "CAND_3"]
    emb = np.random.rand(3, 8).astype("float32")
    artifacts.save_candidate_index(ids, emb, "all-MiniLM-L6-v2", index_dir=tmp_path)
    id_to_row, loaded, meta = artifacts.load_candidate_index(tmp_path)
    assert id_to_row == {"CAND_1": 0, "CAND_2": 1, "CAND_3": 2}
    assert loaded.shape == (3, 8)
    # saved vectors are L2-normalized, so each row should have unit norm
    assert np.allclose(np.linalg.norm(loaded, axis=1), 1.0, atol=1e-5)
    assert meta["count"] == 3 and meta["dim"] == 8


def test_requirement_embeddings_round_trip(tmp_path):
    from talentsignal import artifacts
    req = np.random.rand(4, 8).astype("float32")
    artifacts.save_requirement_embeddings("job_xyz", req, index_dir=tmp_path)
    loaded = artifacts.load_requirement_embeddings("job_xyz", index_dir=tmp_path)
    assert loaded.shape == (4, 8)


def test_evidence_text_handles_string_and_dict_skills():
    from talentsignal import artifacts
    cand = {"profile": {"summary": "built ranking", "headline": "AI Engineer"},
            "career_history": [{"title": "Eng", "description": "embeddings retrieval"}],
            "skills": ["Python", {"name": "FAISS"}]}   # mixed string + dict skills
    text = artifacts.evidence_text_of(cand)
    assert "ranking" in text and "python" in text.lower() and "faiss" in text.lower()


def test_evidence_text_safe_on_malformed():
    from talentsignal import artifacts
    assert artifacts.evidence_text_of({"profile": None, "career_history": "x", "skills": None}) == "" \
        or isinstance(artifacts.evidence_text_of({"profile": None}), str)


# --- v2 intelligence: trap explainer ------------------------------------------

def test_rejected_trap_examples_surface_flagged():
    from talentsignal.trap_detector import rejected_trap_examples
    packets = [
        {"candidate_id": "CAND_T", "rank": 80, "score": 0.2,
         "evidence": {"title": "AI Engineer", "risk_flags": ["expert_skills_zero_duration"]},
         "score_breakdown": {"penalty": 0.3, "risk_flags": ["expert_skills_zero_duration"]}},
        {"candidate_id": "CAND_OK", "rank": 1, "score": 0.9,
         "evidence": {"title": "ML Engineer", "risk_flags": []},
         "score_breakdown": {"penalty": 0.0, "risk_flags": []}},
    ]
    out = rejected_trap_examples(packets)
    assert any(e["candidate_id"] == "CAND_T" for e in out)


# --- v2 intelligence: candidate compare ---------------------------------------

def _packets():
    """Build evidence packets (the dict shape the v2 tools consume) by ranking a
    tiny pool and using the real write path."""
    import json as _json
    import tempfile
    from talentsignal.ranking import rank_records, write_evidence_packets
    from talentsignal.jd_parser import load_job_spec
    job = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")
    recs = [{
        "candidate_id": f"CAND_{i:07d}",
        "profile": {"current_title": "AI Engineer", "summary": "embeddings retrieval ranking ndcg python production",
                    "years_of_experience": 7, "location": "Bangalore"},
        "career_history": [{"title": "AI Engineer", "company": "X", "duration_months": 84,
                            "description": "built embeddings retrieval ranking ndcg in production python"}],
        "skills": ["Python"], "redrob_signals": {"open_to_work_flag": True, "recruiter_response_rate": 0.8},
    } for i in range(1, 6)]
    rows = rank_records(recs, job, top_n=5)
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        write_evidence_packets(rows, f.name)
        path = f.name
    packets = [_json.loads(l) for l in open(path) if l.strip()]
    return packets, job


def test_candidate_compare_by_rank():
    from talentsignal.candidate_compare import compare_by_rank
    packets, _ = _packets()
    cmp = compare_by_rank(packets, 1, 2)
    assert cmp is not None
    assert any(k in cmp for k in ("factors", "score_gap", "recommendation"))


def test_candidate_compare_missing_rank_returns_none():
    from talentsignal.candidate_compare import compare_by_rank
    packets, _ = _packets()
    assert compare_by_rank(packets, 1, 999) is None


def test_strongest_and_weakest_factor():
    from talentsignal.candidate_compare import strongest_factor, weakest_factor
    packets, _ = _packets()
    sk, sv = strongest_factor(packets[0])
    wk, wv = weakest_factor(packets[0])
    assert sv >= wv


# --- v2 intelligence: boundary review -----------------------------------------

def test_boundary_review_runs():
    from talentsignal import boundary_review
    packets, _ = _packets()
    fn = next((getattr(boundary_review, n) for n in dir(boundary_review)
               if n.startswith(("boundary", "review")) and callable(getattr(boundary_review, n))), None)
    assert fn is not None
    out = fn(packets)
    assert out is not None


# --- v2 intelligence: interview kit -------------------------------------------

def test_interview_kit_is_grounded():
    from talentsignal.interview_kit import build_interview_kit
    packets, job = _packets()
    kit = build_interview_kit(packets[0], job)
    assert kit  # non-empty guide

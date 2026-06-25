"""Candidate-facing transparency report — what an applicant (or FCRA-style
adverse-action notice, or auditor) can see: what data was used, what matched with
proof, what wasn't, concerns, and the full factor breakdown. No black box.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.ingest import ingest
from talentsignal.candidate_report import candidate_report

CAND = ingest("Maya Rao. Bangalore. Senior AI Engineer 7 years. Built embeddings retrieval "
              "and ranking models. Owned NDCG evaluation. Skills: Python, Embeddings, Ranking, NDCG",
              fmt="text")[0]
JD = "Senior AI Engineer. Must have embeddings retrieval, ranking models, evaluation NDCG. 5-9 years."


def test_report_has_all_transparency_sections():
    r = candidate_report(CAND, JD, engine="spine")
    for key in ("disclosure", "data_used", "result", "matched_with_proof",
                "not_evidenced", "concerns_flagged", "your_rights"):
        assert key in r


def test_report_states_no_scraping_and_identity_blind():
    r = candidate_report(CAND, JD, engine="spine")
    assert "only the information you provided" in r["disclosure"].lower() \
        or "no scraped" in r["disclosure"].lower()
    assert "never reads your name" in r["data_used"]["identity_used"].lower()


def test_report_proof_is_from_candidate_text():
    r = candidate_report(CAND, JD, engine="spine")
    text = "embeddings retrieval ranking ndcg python"
    for m in r["matched_with_proof"]:
        ev = m["your_evidence"].lower()
        # evidence is the candidate's own text or the explicit "overall meaning" note
        assert "matched on overall meaning" in ev or any(w in ev for w in text.split())


def test_report_lists_unmet_requirements_for_dispute():
    # a JD with a requirement the candidate clearly lacks
    jd = "AI Engineer. Must have Kubernetes production deployment and Go microservices. 5-9 years."
    r = candidate_report(CAND, jd, engine="spine")
    note = r["not_evidenced"]["note"].lower()
    # the candidate gets a chance to correct the record before a human reviews it
    assert "correct the record" in note or "dispute" in note
    assert "human" in note


def test_human_in_the_loop_not_auto_reject():
    r = candidate_report(CAND, JD, engine="spine")
    assert "human" in r["disclosure"].lower()
    assert "not auto-rejected" in r["disclosure"].lower() or "human reviewer" in r["disclosure"].lower()

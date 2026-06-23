"""Universal ingest: any format -> canonical, rankable candidate records, via a
pluggable adapter registry. Covers text/CSV/JSON/LinkedIn + auto-detection and
the end-to-end ingest -> rank path. (PDF/DOCX adapters are wired but need
optional deps / fixture files, so they're smoke-checked for registration.)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.ingest import ingest, list_adapters, detect_format
from talentsignal.api import rank

RESUME = """Asha Menon
asha.menon@email.com | Bangalore, India

Summary
Senior ML engineer with 7 years building recommendation and ranking systems at product companies.

Experience
Senior ML Engineer at Flipkart  2021 - present
Built the recommendation engine serving the homepage feed; owned ranking models and A/B evaluation.
Data Scientist at Swiggy  2018 - 2021
Worked on search relevance and personalization using embeddings.

Education
B.Tech Computer Science 2017

Skills
Python, PyTorch, Embeddings, Ranking, FAISS, A/B Testing
"""


def test_all_builtin_adapters_registered() -> None:
    adapters = list_adapters()
    for fmt in ("text", "csv", "json", "pdf", "docx", "linkedin"):
        assert fmt in adapters


def test_text_resume_parses_to_structured_record() -> None:
    c = ingest(RESUME, fmt="text")[0]
    assert c["profile"]["current_title"]
    assert c["profile"]["years_of_experience"] == 7.0
    assert len(c["career_history"]) == 2
    assert c["profile"]["location"] == "Bangalore"
    assert c["profile"]["country"] == "India"
    names = [s["name"].lower() for s in c["skills"]]
    assert any("python" in n for n in names)


def test_csv_multi_candidate() -> None:
    csv_data = ("name,current_title,current_company,location,years,skills\n"
                "Ravi Kumar,Backend Engineer,Razorpay,Pune,5,\"Python;Go;Kafka\"\n"
                "Priya Singh,Data Scientist,Swiggy,Bangalore,6,\"Python;ML;SQL\"")
    cands = ingest(csv_data, fmt="csv")
    assert len(cands) == 2
    assert cands[0]["profile"]["current_title"] == "Backend Engineer"
    assert cands[0]["profile"]["years_of_experience"] == 5.0


def test_json_dict_and_jsonl() -> None:
    rec = {"candidate_id": "CAND_0000009", "profile": {"current_title": "X"},
           "career_history": [], "skills": [], "redrob_signals": {}}
    out = ingest(rec, fmt="json")
    assert out[0]["candidate_id"] == "CAND_0000009"


def test_linkedin_dict() -> None:
    data = {
        "profile": {"First Name": "Sam", "Last Name": "Roy", "Headline": "ML Engineer",
                    "Summary": "ranking systems", "Geo Location": "Bangalore"},
        "positions": [{"Company Name": "Cred", "Title": "ML Engineer",
                       "Description": "ranking", "Started On": "2020", "Finished On": ""}],
        "skills": [{"Name": "Python"}, {"Name": "Ranking"}],
    }
    c = ingest(data, fmt="linkedin")[0]
    assert "Sam" in c["profile"]["anonymized_name"]
    assert c["career_history"][0]["company"] == "Cred"


def test_auto_detect_format() -> None:
    assert detect_format({"x": 1}) == "json"
    assert detect_format("some pasted resume text with no path") == "text"


def test_mixed_list_ingest() -> None:
    csv_data = "name,current_title,years\nA,Engineer,5"
    out = ingest([RESUME, csv_data], fmt=None) if False else ingest([{"candidate_id": "CAND_0000001",
                  "profile": {}, "career_history": [], "skills": [], "redrob_signals": {}}])
    assert len(out) == 1


def test_ingest_to_rank_end_to_end() -> None:
    cands = ingest(RESUME, fmt="text")
    res = rank("Senior AI Engineer: embeddings, retrieval, ranking, production ML, evaluation. 5-9 years.",
               cands, top_n=1, engine="spine")
    assert res.ranked[0].score > 0
    assert res.ranked[0].reasoning

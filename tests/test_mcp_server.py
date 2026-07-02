"""MCP server: protocol handshake, tool listing, and each tool over JSON-RPC,
wrapping the same engine facade as every other surface.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import mcp_server as M


def _call(name, args):
    r = M.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                  "params": {"name": name, "arguments": args}})
    assert "result" in r, r
    return json.loads(r["result"]["content"][0]["text"])


def test_initialize_and_list():
    init = M.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert init["result"]["serverInfo"]["name"] == "talentsignal"
    # declares both tools and prompts capabilities
    assert "prompts" in init["result"]["capabilities"]
    tools = M.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
    names = {t["name"] for t in tools}
    assert {"rank_candidates", "ingest_jd", "screen_resume", "audit_candidate",
            "explain_ranking", "candidate_report", "compliance",
            "compare_candidates", "build_interview_kit"} <= names
    assert all("inputSchema" in t for t in tools)


def test_prompts_list_and_get():
    prompts = M.handle({"jsonrpc": "2.0", "id": 3, "method": "prompts/list"})["result"]["prompts"]
    names = {p["name"] for p in prompts}
    assert {"shortlist_for_role", "fair_hiring_review", "prep_interview",
            "explain_to_candidate"} <= names
    got = M.handle({"jsonrpc": "2.0", "id": 4, "method": "prompts/get",
                    "params": {"name": "prep_interview",
                               "arguments": {"jd": "AI Engineer", "resumes": "Asha ML 7y"}}})
    text = got["result"]["messages"][0]["content"]["text"]
    assert "build_interview_kit" in text and "AI Engineer" in text
    # unknown prompt errors cleanly
    err = M.handle({"jsonrpc": "2.0", "id": 5, "method": "prompts/get", "params": {"name": "nope"}})
    assert err["error"]["code"] == -32602


def test_compare_and_interview_kit_tools():
    jd = "Senior AI Engineer. Must have embeddings, retrieval, ranking, Python. 5-9 years."
    cands = [
        {"candidate_id": "C1", "profile": {"current_title": "ML Engineer",
         "summary": "ranking retrieval embeddings python", "years_of_experience": 7},
         "career_history": [{"title": "ML Eng", "description": "ranking retrieval"}],
         "skills": ["Python"], "redrob_signals": {}},
        {"candidate_id": "C2", "profile": {"current_title": "Backend",
         "summary": "java services", "years_of_experience": 6},
         "career_history": [{"title": "Backend", "description": "java"}],
         "skills": ["Java"], "redrob_signals": {}},
    ]
    cmp = _call("compare_candidates", {"jd": jd, "candidates": cands, "left_rank": 1, "right_rank": 2})
    assert "recommendation" in cmp and cmp.get("left_rank") == 1
    kit = _call("build_interview_kit", {"jd": jd, "candidates": cands, "rank": 1})
    assert len(kit.get("questions", [])) >= 3 and kit.get("decision_rubric")


def test_ingest_jd_tool():
    out = _call("ingest_jd", {"jd": "Senior AI Engineer. Must have embeddings and ranking. 5-9 years. Pune."})
    assert out["min_years"] == 5.0 and out["max_years"] == 9.0
    assert len(out["requirements"]) >= 1


def test_screen_resume_tool():
    resume = "Asha\nBangalore, India\nML Engineer with 7 years.\nExperience\nML Engineer at Flipkart 2021 - present\nBuilt ranking.\nSkills\nPython, Ranking"
    out = _call("screen_resume", {"resume": resume})
    assert out["profile"]["years_of_experience"] == 7.0


def test_rank_candidates_tool_accepts_resume_text():
    resume = "Asha\nML Engineer with 7 years building ranking and embeddings systems.\nSkills\nPython, Ranking, Embeddings"
    out = _call("rank_candidates", {"jd": "AI Engineer: embeddings, ranking, production ML. 5-9 years.",
                                    "candidates": [resume], "top_n": 1})
    assert out["ranked"][0]["score"] >= 0
    assert out["ranked"][0]["reasoning"]


def test_audit_candidate_tool_flags_honeypot():
    sys.path.insert(0, str(ROOT / "src"))
    from talentsignal.eval import datasets as D
    from talentsignal.eval.roles import AI_SEARCH
    hp = D.make_candidate(AI_SEARCH, D.HONEYPOT, 0).record
    out = _call("audit_candidate", {"candidate": hp})
    assert out["is_impossible"] is True
    assert out["flags"]


def test_unknown_tool_errors():
    r = M.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                  "params": {"name": "does_not_exist", "arguments": {}}})
    assert "error" in r

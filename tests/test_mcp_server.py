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
    tools = M.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
    names = {t["name"] for t in tools}
    assert {"rank_candidates", "ingest_jd", "screen_resume", "audit_candidate", "explain_ranking"} <= names


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

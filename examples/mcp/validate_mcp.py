#!/usr/bin/env python3
"""End-to-end MCP validation over the REAL stdio JSON-RPC protocol.

Launches mcp_server.py exactly as an MCP client (Claude Desktop) would, exercises the
handshake, all 9 tools, all 4 prompts, and the error handling — and (with --save) writes
real request/response captures into this directory.

  python3 examples/mcp/validate_mcp.py            # validate + print a summary
  python3 examples/mcp/validate_mcp.py --save     # also save captures to examples/mcp/
"""
from __future__ import annotations

import json
import select
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SAVE = "--save" in sys.argv


class MCP:
    def __init__(self):
        self.p = subprocess.Popen(
            [sys.executable, str(ROOT / "mcp_server.py")],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def call(self, obj, timeout=30):
        self.p.stdin.write(json.dumps(obj) + "\n")
        self.p.stdin.flush()
        r, _, _ = select.select([self.p.stdout], [], [], timeout)
        if not r:
            return {"error": "TIMEOUT"}
        return json.loads(self.p.stdout.readline())

    def tool(self, name, args):
        r = self.call({"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                       "params": {"name": name, "arguments": args}})
        res = r["result"]
        body = json.loads(res["content"][0]["text"])
        return res.get("isError", False), body

    def close(self):
        self.p.terminate()


JD = "Senior AI Engineer. Must have embeddings, retrieval, ranking, Python. 5-9 years."
CANDS = [
    {"candidate_id": "CAND_A", "profile": {"current_title": "ML Engineer",
     "summary": "Built the system ordering the homepage feed by relevance; shipped to millions. Python.",
     "years_of_experience": 7},
     "career_history": [{"title": "ML Engineer", "company": "Acme", "description": "owned ranking and retrieval; A/B tested"}],
     "skills": ["Python", "Recommendation"], "redrob_signals": {}},
    {"candidate_id": "CAND_B", "profile": {"current_title": "AI Expert",
     "summary": "embeddings retrieval ranking python expert", "years_of_experience": 9},
     "career_history": [{"title": "AI Lead", "duration_months": 180, "description": "embeddings"}],
     "skills": [{"name": "Embeddings", "proficiency": "expert", "months_used": 0}], "redrob_signals": {}},
    {"candidate_id": "CAND_C", "profile": {"current_title": "Backend Engineer",
     "summary": "Java microservices", "years_of_experience": 6},
     "career_history": [{"title": "Backend", "description": "java"}], "skills": ["Java"], "redrob_signals": {}},
]

captures: dict = {}
passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  ✓ {name}  {detail}")
    else:
        failed += 1
        print(f"  ✗ {name}  {detail}")


def main() -> int:
    m = MCP()
    try:
        # --- handshake ---
        r = m.call({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        caps = r["result"]["capabilities"]
        check("initialize", r["result"]["serverInfo"]["name"] == "talentsignal",
              f"protocol {r['result']['protocolVersion']}, caps {list(caps)}")
        captures["initialize"] = r

        tools = m.call({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        check("tools/list", len(tools) == 9, f"{len(tools)} tools")
        captures["tools_list"] = {"tools": [t["name"] for t in tools]}

        prompts = m.call({"jsonrpc": "2.0", "id": 3, "method": "prompts/list"})["result"]["prompts"]
        check("prompts/list", len(prompts) == 4, f"{len(prompts)} prompts")
        captures["prompts_list"] = {"prompts": [p["name"] for p in prompts]}

        # --- the 9 tools ---
        err, d = m.tool("rank_candidates", {"jd": JD, "candidates": CANDS, "top_n": 3})
        top = d["ranked"][0]["candidate_id"]
        check("rank_candidates", not err and top == "CAND_A", f"#1 = {top}")
        captures["rank_candidates"] = d

        err, d = m.tool("ingest_jd", {"jd": JD})
        check("ingest_jd", not err and d["min_years"] == 5.0, f"years {d['min_years']}-{d['max_years']}")
        captures["ingest_jd"] = d

        err, d = m.tool("screen_resume", {"resume": "Asha - ML Engineer, 7 yrs. Ranking, retrieval. Python."})
        check("screen_resume", not err and "profile" in d, "parsed profile")
        captures["screen_resume"] = d

        err, d = m.tool("audit_candidate", {"candidate": CANDS[1]})
        check("audit_candidate", not err and d["is_impossible"], f"honeypot caught: {d['is_impossible']}")
        captures["audit_candidate"] = d

        err, d = m.tool("candidate_report", {"candidate": CANDS[0], "jd": JD})
        check("candidate_report", not err and "disclosure" in d, "transparency report")
        captures["candidate_report"] = d

        err, d = m.tool("compliance", {"ranked_ids": ["a", "b", "c", "d"],
                        "group_attributes": {"a": "F", "b": "M", "c": "F", "d": "M"}, "top_k": 2})
        check("compliance (flat input)", not err, "no crash on flat labels")
        captures["compliance"] = d

        err, d = m.tool("explain_ranking", {"jd": JD, "candidates": CANDS, "top_n": 2})
        check("explain_ranking", not err and d.get("explanations"), f"{len(d.get('explanations', []))} explanations")
        captures["explain_ranking"] = d

        err, d = m.tool("compare_candidates", {"jd": JD, "candidates": CANDS, "left_rank": 1, "right_rank": 3})
        check("compare_candidates", not err and "recommendation" in d, "scorecard")
        captures["compare_candidates"] = d

        err, d = m.tool("build_interview_kit", {"jd": JD, "candidates": CANDS, "rank": 1})
        check("build_interview_kit", not err and len(d.get("questions", [])) >= 3, f"{len(d.get('questions', []))} questions")
        captures["build_interview_kit"] = d

        # --- the 4 prompts ---
        for name in ("shortlist_for_role", "fair_hiring_review", "prep_interview", "explain_to_candidate"):
            r = m.call({"jsonrpc": "2.0", "id": 4, "method": "prompts/get",
                        "params": {"name": name, "arguments": {"jd": JD, "resumes": "Asha ML 7y", "resume": "Asha ML 7y", "group_attributes": "{}"}}})
            ok = "messages" in r.get("result", {})
            check(f"prompt: {name}", ok, "renders")

        # --- robustness ---
        err, d = m.tool("rank_candidates", {"jd": JD})  # missing candidates
        check("friendly error (missing arg)", err and "required" in d.get("error", ""), "isError, readable")
        r = m.call({"jsonrpc": "2.0", "id": 6, "method": "ping"})
        check("ping", r["result"] == {}, "keepalive")

        print(f"\n  ==== {passed} passed, {failed} failed ====")
        if SAVE:
            out = HERE / "captures.json"
            out.write_text(json.dumps(captures, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  saved real captures -> {out}")
        return 0 if failed == 0 else 1
    finally:
        m.close()


if __name__ == "__main__":
    raise SystemExit(main())

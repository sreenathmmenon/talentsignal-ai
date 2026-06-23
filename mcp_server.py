#!/usr/bin/env python3
"""TalentSignal MCP server — expose the candidate-intelligence engine as tools
any agentic system (Claude Desktop, agents) can call.

Implements the Model Context Protocol over stdio JSON-RPC with no third-party
dependency (hand-rolled, so it runs anywhere the engine runs). It wraps the same
public facade (talentsignal.api.rank) and ingest layer the CLI/REST/UI use, so
there is one engine behind every surface.

Tools exposed:
  rank_candidates   — rank candidates (any format) against a JD (any format)
  ingest_jd         — parse a JD into a structured weighted requirement model
  screen_resume     — parse one resume (text/file) into a structured profile
  audit_candidate   — run the consistency/honeypot auditor on a candidate
  explain_ranking   — rank then return the grounded reasoning for the top picks

Run:
  python mcp_server.py                # stdio server (for Claude Desktop / agents)

Register in an MCP client (e.g. Claude Desktop config):
  { "mcpServers": { "talentsignal": { "command": "python",
    "args": ["/abs/path/mcp_server.py"] } } }
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "talentsignal", "version": "1.0.0"}

# --- tool schemas --------------------------------------------------------------

TOOLS = [
    {
        "name": "rank_candidates",
        "description": "Rank candidates against a job description. Accepts a JD as "
                       "free text and candidates as a list of records (or text resumes). "
                       "Returns a ranked, explainable shortlist.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jd": {"type": "string", "description": "Job description (free text or YAML)."},
                "candidates": {"type": "array", "description": "Candidate records (objects) or resume texts (strings).",
                                "items": {"type": ["object", "string"]}},
                "top_n": {"type": "integer", "default": 10},
                "category": {"type": "string", "default": "ai_ml_search_ranking"},
            },
            "required": ["jd", "candidates"],
        },
    },
    {
        "name": "ingest_jd",
        "description": "Parse a job description into a structured, weighted requirement "
                       "model (must-have / nice-to-have / disqualifier, seniority, locations).",
        "inputSchema": {
            "type": "object",
            "properties": {"jd": {"type": "string"}},
            "required": ["jd"],
        },
    },
    {
        "name": "screen_resume",
        "description": "Parse one resume (plain text) into a structured candidate profile.",
        "inputSchema": {
            "type": "object",
            "properties": {"resume": {"type": "string"}, "use_llm": {"type": "boolean", "default": False}},
            "required": ["resume"],
        },
    },
    {
        "name": "audit_candidate",
        "description": "Run the role-independent consistency / honeypot auditor on a "
                       "candidate record and return any internal contradictions found.",
        "inputSchema": {
            "type": "object",
            "properties": {"candidate": {"type": "object"}},
            "required": ["candidate"],
        },
    },
    {
        "name": "explain_ranking",
        "description": "Rank candidates against a JD and return the grounded reasoning "
                       "for each of the top picks (why they ranked where they did).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jd": {"type": "string"},
                "candidates": {"type": "array", "items": {"type": ["object", "string"]}},
                "top_n": {"type": "integer", "default": 5},
            },
            "required": ["jd", "candidates"],
        },
    },
]


# --- tool implementations ------------------------------------------------------

def _coerce_candidates(items: list) -> list[dict]:
    """Allow candidates as records OR resume text strings (ingest the strings)."""
    from talentsignal.ingest import ingest
    out: list[dict] = []
    for it in items:
        if isinstance(it, str):
            out.extend(ingest(it, fmt="text"))
        elif isinstance(it, dict):
            out.append(it)
    return out


def tool_rank_candidates(args: dict) -> dict:
    from talentsignal.api import rank
    cands = _coerce_candidates(args["candidates"])
    res = rank(args["jd"], cands, top_n=int(args.get("top_n", 10)),
               engine="spine", category=args.get("category", "ai_ml_search_ranking"))
    return res.to_dict()


def tool_ingest_jd(args: dict) -> dict:
    from talentsignal.jd_ingest import ingest_text
    model = ingest_text(args["jd"])
    return {
        "title": model.title,
        "min_years": model.min_years, "max_years": model.max_years,
        "preferred_locations": list(model.preferred_locations),
        "requirements": [{"text": r.text, "kind": r.kind, "weight": r.weight,
                          "keywords": list(r.keywords)} for r in model.requirements],
    }


def tool_screen_resume(args: dict) -> dict:
    from talentsignal.ingest import ingest
    recs = ingest(args["resume"], fmt="text", use_llm=bool(args.get("use_llm", False)))
    return recs[0] if recs else {}


def tool_audit_candidate(args: dict) -> dict:
    from talentsignal.consistency_audit import audit_candidate
    rep = audit_candidate(args["candidate"])
    return {
        "is_impossible": rep.is_impossible,
        "penalty": rep.penalty,
        "flags": [{"code": f.code, "detail": f.detail} for f in rep.flags],
    }


def tool_explain_ranking(args: dict) -> dict:
    from talentsignal.api import rank
    cands = _coerce_candidates(args["candidates"])
    res = rank(args["jd"], cands, top_n=int(args.get("top_n", 5)), engine="spine")
    return {"explanations": [{"rank": c.rank, "candidate_id": c.candidate_id,
                              "score": c.score, "reasoning": c.reasoning} for c in res.ranked]}


TOOL_FUNCS = {
    "rank_candidates": tool_rank_candidates,
    "ingest_jd": tool_ingest_jd,
    "screen_resume": tool_screen_resume,
    "audit_candidate": tool_audit_candidate,
    "explain_ranking": tool_explain_ranking,
}


# --- JSON-RPC / MCP plumbing ---------------------------------------------------

def handle(request: dict) -> dict | None:
    """Handle one JSON-RPC request; return a response dict (or None for notifications)."""
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return _result(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return _result(req_id, {"tools": TOOLS})
    if method == "tools/call":
        params = request.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})
        fn = TOOL_FUNCS.get(name)
        if fn is None:
            return _error(req_id, -32601, f"unknown tool: {name}")
        try:
            result = fn(args)
            return _result(req_id, {"content": [{"type": "text",
                                                  "text": json.dumps(result, ensure_ascii=False)}]})
        except Exception as exc:  # noqa: BLE001
            return _error(req_id, -32000, f"{type(exc).__name__}: {exc}")
    if req_id is not None:
        return _error(req_id, -32601, f"unknown method: {method}")
    return None


def _result(req_id, result) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id, code, message) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def serve_stdio() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    serve_stdio()

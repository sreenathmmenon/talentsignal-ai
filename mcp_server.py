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
        "name": "candidate_report",
        "description": "Transparency report for ONE candidate against a JD: what the "
                       "engine used (only their own data; identity-blind), what matched "
                       "with proof from their own words, what wasn't evidenced (so they "
                       "can correct the record), concerns, and the factor breakdown. "
                       "Human-in-the-loop, no black box.",
        "inputSchema": {
            "type": "object",
            "properties": {"candidate": {"type": ["object", "string"]}, "jd": {"type": "string"}},
            "required": ["candidate", "jd"],
        },
    },
    {
        "name": "compliance",
        "description": "EEOC four-fifths (80%) adverse-impact report on a ranking, given "
                       "customer-supplied protected-group labels. The engine never infers "
                       "protected attributes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ranked_ids": {"type": "array", "items": {"type": "string"}},
                "group_attributes": {"type": "object"},
                "top_k": {"type": "integer", "default": 10},
            },
            "required": ["ranked_ids", "group_attributes"],
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
    {
        "name": "compare_candidates",
        "description": "Explain why one candidate ranks ahead of another with a "
                       "factor-by-factor scorecard (skills, experience, seniority, "
                       "availability, credibility). Use after rank_candidates when the "
                       "user asks 'why them and not the other one?'. Ranks are 1-based "
                       "positions in the shortlist produced from the same JD + candidates.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jd": {"type": "string"},
                "candidates": {"type": "array", "items": {"type": ["object", "string"]}},
                "left_rank": {"type": "integer", "description": "1-based rank of the first candidate"},
                "right_rank": {"type": "integer", "description": "1-based rank of the second"},
            },
            "required": ["jd", "candidates", "left_rank", "right_rank"],
        },
    },
    {
        "name": "build_interview_kit",
        "description": "Generate an evidence-grounded interview kit for one ranked "
                       "candidate: sharp questions drawn from their own work, a weak-area "
                       "probe, a risk-validation question, and a hire/no-hire rubric. Use "
                       "after rank_candidates to prepare the recruiter for a specific "
                       "candidate. Every question is anchored in the résumé (no invention).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jd": {"type": "string"},
                "candidates": {"type": "array", "items": {"type": ["object", "string"]}},
                "rank": {"type": "integer", "default": 1, "description": "1-based rank of the candidate to prep for"},
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


_EMBEDDER = {"model": None, "tried": False}


def _embedder():
    """Cached embedder for hybrid ranking on small samples; None -> spine fallback."""
    if _EMBEDDER["tried"]:
        return _EMBEDDER["model"]
    _EMBEDDER["tried"] = True
    try:
        import os
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        _EMBEDDER["model"] = lambda t: m.encode(t, convert_to_numpy=True, normalize_embeddings=True)
    except Exception:  # noqa: BLE001
        _EMBEDDER["model"] = None
    return _EMBEDDER["model"]


def tool_rank_candidates(args: dict) -> dict:
    from talentsignal.api import rank
    cands = _coerce_candidates(args["candidates"])
    emb = _embedder() if len(cands) <= 200 else None
    res = rank(args["jd"], cands, top_n=int(args.get("top_n", 10)),
               engine="hybrid" if emb else "spine", embedder=emb,
               category=args.get("category", "ai_ml_search_ranking"))
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


def tool_candidate_report(args: dict) -> dict:
    """Transparency report for ONE candidate: what the engine used/concluded, with
    proof, unmet requirements, and concerns — the human-in-the-loop, no-black-box
    answer an agent can give a candidate or an auditor."""
    from talentsignal.candidate_report import candidate_report
    cand = args["candidate"]
    if isinstance(cand, str):
        from talentsignal.ingest import ingest
        recs = ingest(cand, fmt="text")
        cand = recs[0] if recs else {}
    return candidate_report(cand, args["jd"], category=args.get("category", "ai_ml_search_ranking"))


def tool_compliance(args: dict) -> dict:
    """Adverse-impact (EEOC four-fifths) report on a ranking given customer-supplied
    protected-group labels. The engine never infers protected attributes."""
    from talentsignal.eval.compliance import compliance_summary
    return compliance_summary(args["ranked_ids"], args["group_attributes"],
                              top_k=int(args.get("top_k", 10)))


def tool_explain_ranking(args: dict) -> dict:
    from talentsignal.api import rank
    cands = _coerce_candidates(args["candidates"])
    res = rank(args["jd"], cands, top_n=int(args.get("top_n", 5)), engine="spine")
    return {"explanations": [{"rank": c.rank, "candidate_id": c.candidate_id,
                              "score": c.score, "reasoning": c.reasoning} for c in res.ranked]}


def _packets(jd, candidates):
    """Rank in-memory candidates and return the full evidence packets that the
    compare + interview-kit engines consume, plus the parsed job."""
    from dataclasses import asdict
    from talentsignal.api.facade import _resolve_job
    from talentsignal.ranking import rank_records, rank_records_hybrid
    cands = _coerce_candidates(candidates)
    job = _resolve_job(jd, category="ai_ml_search_ranking", title="")
    emb = _embedder() if len(cands) <= 200 else None
    rows = (rank_records_hybrid(cands, job, top_n=min(50, len(cands)), live_embedder=emb)
            if emb else rank_records(cands, job, top_n=min(50, len(cands))))
    out = []
    for row in rows:
        ev, score = row["_evidence"], row["_score"]
        out.append({"candidate_id": row["candidate_id"], "rank": row["rank"],
                    "score": row["score"], "reasoning": row["reasoning"],
                    "score_breakdown": asdict(score),
                    "evidence": {"title": ev.title, "years": ev.years, "location": ev.location,
                                 "career_retrieval_terms": ev.career_retrieval_terms,
                                 "career_production_terms": ev.career_production_terms,
                                 "vector_terms": ev.vector_terms, "production_terms": ev.production_terms,
                                 "risk_flags": score.risk_flags, "confidence": score.confidence}})
    return out, job


def tool_compare_candidates(args: dict) -> dict:
    """Explain WHY one ranked candidate sits ahead of another — a factor-by-factor
    scorecard. The recruiter question 'why #2 over #5?', answered for an agent."""
    from talentsignal.candidate_compare import compare_by_rank
    packets, _ = _packets(args["jd"], args["candidates"])
    cmp = compare_by_rank(packets, int(args["left_rank"]), int(args["right_rank"]))
    if cmp is None:
        return {"error": f"ranks {args['left_rank']}/{args['right_rank']} not in the shortlist of {len(packets)}"}
    return cmp


def tool_build_interview_kit(args: dict) -> dict:
    """Generate an evidence-grounded interview kit for ONE ranked candidate: depth
    questions tied to their strongest evidence, a weak-area probe, a risk question,
    and a hire/no-hire rubric. No hallucination — anchored in their own profile."""
    from talentsignal.interview_kit import build_interview_kit
    packets, job = _packets(args["jd"], args["candidates"])
    target = int(args.get("rank", 1))
    packet = next((p for p in packets if p["rank"] == target), None)
    if packet is None:
        return {"error": f"rank {target} not in the shortlist of {len(packets)}"}
    return build_interview_kit(packet, job)


TOOL_FUNCS = {
    "rank_candidates": tool_rank_candidates,
    "ingest_jd": tool_ingest_jd,
    "screen_resume": tool_screen_resume,
    "audit_candidate": tool_audit_candidate,
    "explain_ranking": tool_explain_ranking,
    "candidate_report": tool_candidate_report,
    "compliance": tool_compliance,
    "compare_candidates": tool_compare_candidates,
    "build_interview_kit": tool_build_interview_kit,
}


# --- MCP prompts: one-click hiring workflows an agent/user can invoke ----------
# Prompts are reusable, parameterized instructions that guide the model to use the
# tools above in a proven sequence — the feature that turns "9 tools" into "hire
# faster, fairly, with proof" for a non-expert user.

PROMPTS = [
    {
        "name": "shortlist_for_role",
        "description": "Screen a batch of résumés against a role and return a ranked, "
                       "explained shortlist — surfacing strong candidates a keyword filter misses.",
        "arguments": [
            {"name": "jd", "description": "The job description", "required": True},
            {"name": "resumes", "description": "Résumé texts (paste or list)", "required": True},
        ],
    },
    {
        "name": "fair_hiring_review",
        "description": "Produce a shortlist AND an adverse-impact (four-fifths) compliance "
                       "check for it — the review legal/HR needs before automated screening.",
        "arguments": [
            {"name": "jd", "description": "The job description", "required": True},
            {"name": "resumes", "description": "Résumé texts", "required": True},
            {"name": "group_attributes", "description": "Your own protected-group labels per candidate", "required": False},
        ],
    },
    {
        "name": "prep_interview",
        "description": "Rank the candidates, then build an evidence-grounded interview kit "
                       "for the top pick (questions from their own work + a hire/no-hire rubric).",
        "arguments": [
            {"name": "jd", "description": "The job description", "required": True},
            {"name": "resumes", "description": "Résumé texts", "required": True},
        ],
    },
    {
        "name": "explain_to_candidate",
        "description": "Generate a transparent, candidate-facing report: what the engine "
                       "used, what matched with proof, and what to improve — the humane "
                       "answer to 'why was I not shortlisted?'.",
        "arguments": [
            {"name": "jd", "description": "The job description", "required": True},
            {"name": "resume", "description": "The candidate's résumé", "required": True},
        ],
    },
]

_PROMPT_TEXT = {
    "shortlist_for_role": (
        "Use rank_candidates with this JD and these résumés, then present the ranked "
        "shortlist. For each candidate give the score, the one-line reasoning, and flag "
        "anyone marked 'rescued by meaning' (strong fit a keyword search would miss).\n\n"
        "JD:\n{jd}\n\nRésumés:\n{resumes}"),
    "fair_hiring_review": (
        "First call rank_candidates on this JD and these résumés. Then call compliance "
        "with the resulting ranked ids and the supplied group_attributes to run the "
        "four-fifths adverse-impact check. Present the shortlist AND the compliance verdict; "
        "if the impact ratio is below 0.8, call it out clearly.\n\n"
        "JD:\n{jd}\n\nRésumés:\n{resumes}\n\nGroup attributes (optional):\n{group_attributes}"),
    "prep_interview": (
        "Call rank_candidates on this JD and these résumés, then call build_interview_kit "
        "for rank 1. Present the top candidate, then their interview questions and the "
        "hire/no-hire rubric.\n\nJD:\n{jd}\n\nRésumés:\n{resumes}"),
    "explain_to_candidate": (
        "Call candidate_report with this candidate and JD. Present, in a warm and honest "
        "tone: what the engine used (only their own data), what matched with proof from "
        "their words, what wasn't evidenced (so they can improve), and any concerns.\n\n"
        "JD:\n{jd}\n\nRésumé:\n{resume}"),
}


def _get_prompt(name: str, arguments: dict) -> dict:
    tmpl = _PROMPT_TEXT.get(name)
    if tmpl is None:
        raise KeyError(name)
    args = {a["name"]: "" for p in PROMPTS if p["name"] == name for a in p["arguments"]}
    args.update({k: str(v) for k, v in (arguments or {}).items()})
    return {
        "description": next(p["description"] for p in PROMPTS if p["name"] == name),
        "messages": [{"role": "user", "content": {"type": "text", "text": tmpl.format(**args)}}],
    }


# --- JSON-RPC / MCP plumbing ---------------------------------------------------

def handle(request: dict) -> dict | None:
    """Handle one JSON-RPC request; return a response dict (or None for notifications)."""
    # A JSON line that parses to a non-dict (array, scalar, null) must not crash the
    # whole server — return a proper JSON-RPC Invalid Request error instead.
    if not isinstance(request, dict):
        return _error(None, -32600, "Invalid Request: expected a JSON object")
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return _result(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "prompts": {}},
            "serverInfo": SERVER_INFO,
        })
    if method == "ping":
        # standard MCP keepalive — respond with an empty result
        return _result(req_id, {})
    if method and method.startswith("notifications/"):
        # notifications (initialized, cancelled, progress, …) get no response
        return None
    if method == "tools/list":
        return _result(req_id, {"tools": TOOLS})
    if method == "prompts/list":
        return _result(req_id, {"prompts": PROMPTS})
    if method == "prompts/get":
        params = request.get("params", {})
        try:
            return _result(req_id, _get_prompt(params.get("name", ""), params.get("arguments", {})))
        except KeyError:
            return _error(req_id, -32602, f"unknown prompt: {params.get('name')}")
    if method == "tools/call":
        params = request.get("params", {})
        name = params.get("name")
        args = params.get("arguments") or {}
        fn = TOOL_FUNCS.get(name)
        if fn is None:
            return _error(req_id, -32601, f"unknown tool: {name}")
        # Validate inputs and return a FRIENDLY, agent-readable error (isError result)
        # instead of a raw Python exception — so an agent can read it and self-correct.
        problem = _validate_args(name, args)
        if problem:
            return _tool_error(req_id, problem)
        try:
            result = fn(args)
            return _result(req_id, {"content": [{"type": "text",
                                                  "text": json.dumps(result, ensure_ascii=False)}]})
        except (KeyError, ValueError, TypeError) as exc:
            # user-input-shaped failures -> readable tool error, not a protocol crash
            return _tool_error(req_id, f"invalid input to {name}: {exc}")
        except Exception as exc:  # noqa: BLE001 - unexpected: still don't crash the server
            return _tool_error(req_id, f"{name} failed: {type(exc).__name__}: {exc}")
    if req_id is not None:
        return _error(req_id, -32601, f"unknown method: {method}")
    return None


_SCHEMA_BY_TOOL = {t["name"]: t["inputSchema"] for t in TOOLS}

# JSON-schema type -> python types, for coercion-friendly validation.
_PYTYPE = {"string": str, "integer": int, "number": (int, float), "boolean": bool,
           "array": list, "object": dict}


def _validate_args(name: str, args: dict) -> str | None:
    """Schema-driven input validation (reads each tool's own inputSchema — no
    per-tool hardcoding). Returns a friendly problem string, or None if OK."""
    if not isinstance(args, dict):
        return "arguments must be a JSON object"
    schema = _SCHEMA_BY_TOOL.get(name, {})
    props = schema.get("properties", {})
    for req in schema.get("required", []):
        if req not in args or args[req] is None:
            return (f"'{req}' is required. This tool needs: "
                    f"{', '.join(schema.get('required', [])) or '(none)'}.")
    for key, val in args.items():
        spec = props.get(key)
        if not spec or val is None:
            continue
        allowed = spec.get("type")
        types = allowed if isinstance(allowed, list) else [allowed]
        py = tuple(t for jt in types for t in ((_PYTYPE.get(jt),) if not isinstance(_PYTYPE.get(jt), tuple) else _PYTYPE[jt]) if t)
        # accept numeric strings for integer fields (agents often send "5")
        if py and int in py and isinstance(val, str) and val.strip().lstrip("-").isdigit():
            continue
        if py and not isinstance(val, py):
            return (f"'{key}' should be {' or '.join(types)}, got "
                    f"{type(val).__name__}.")
    # a couple of high-value semantic checks agents trip on
    if "candidates" in props and isinstance(args.get("candidates"), list) and not args["candidates"]:
        return "'candidates' is empty — provide at least one candidate record or résumé text."
    return None


def _tool_error(req_id, message: str) -> dict:
    """A tool-level error the AGENT can read and act on (isError result), rather
    than a JSON-RPC protocol error that surfaces as an opaque failure."""
    return _result(req_id, {
        "isError": True,
        "content": [{"type": "text", "text": json.dumps({"error": message})}],
    })


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
            sys.stdout.write(json.dumps(_error(None, -32700, "Parse error")) + "\n")
            sys.stdout.flush()
            continue
        try:
            response = handle(request)
        except Exception as exc:  # noqa: BLE001 - one bad request must not kill the server
            response = _error(request.get("id") if isinstance(request, dict) else None,
                              -32603, f"Internal error: {type(exc).__name__}")
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    serve_stdio()

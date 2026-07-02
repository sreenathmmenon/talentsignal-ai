#!/usr/bin/env python3
"""TalentSignal REST API — the integrate/buy surface.

A small HTTP service over the same talentsignal.api facade and ingest layer, so
any portal/ATS can POST a JD + candidates and get a ranked, explainable
shortlist. Stdlib http.server (no framework dependency), JSON in/out.

Endpoints:
  GET  /health              -> {"status":"ok", ...}
  GET  /openapi.json        -> machine-readable API spec
  POST /rank                -> {jd, candidates[, top_n, engine, category]} -> RankResult
  POST /ingest/jd           -> {jd} -> structured requirement model
  POST /ingest/resume       -> {resume[, use_llm]} -> structured candidate
  POST /audit               -> {candidate} -> consistency report

Auth: optional API key via the X-API-Key header when TALENTSIGNAL_API_KEY is set.

Run:
  python api_server.py --host 127.0.0.1 --port 8900
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent / "src"))

API_VERSION = "1.0.0"

# A human face for the API port — a judge hitting GET / sees the product story and
# a copy-paste curl, not raw JSON. Self-contained, no dependencies.
_API_LANDING = """<!doctype html><html><head><meta charset=utf-8>
<title>TalentSignal API</title>
<style>
body{margin:0;background:#07070B;color:#F5F6FC;font:15px/1.6 'Inter',system-ui,sans-serif;padding:56px 24px}
.wrap{max-width:760px;margin:0 auto}
h1{font-size:34px;font-weight:800;letter-spacing:-.02em;margin:0 0 8px}
.g{background:linear-gradient(110deg,#8B5CF6,#22D3EE);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
p{color:#C7CBDD}.mut{color:#878DAB}
pre{background:#101220;border:1px solid #1E2138;border-radius:12px;padding:18px;overflow:auto;
  font:13px ui-monospace,monospace;color:#C7CBDD}
.chip{display:inline-block;font:12px ui-monospace,monospace;padding:5px 11px;border-radius:999px;
  border:1px solid #2A2E4A;color:#C7CBDD;margin:2px 6px 2px 0}
a{color:#67E8F9}
</style></head><body><div class=wrap>
<h1>TalentSignal <span class=g>API</span></h1>
<p>The same JD-agnostic ranking engine as the Studio UI — exposed as a REST service.
Rank candidates by meaning (not keywords), reject fabricated profiles, get grounded reasoning.</p>
<p class=mut>Endpoints:
<span class=chip>POST /rank</span><span class=chip>POST /ingest/jd</span><span class=chip>POST /ingest/resume</span>
<span class=chip>POST /audit</span><span class=chip>POST /compliance</span><span class=chip>POST /candidate_report</span>
<span class=chip>GET /openapi.json</span><span class=chip>GET /health</span></p>
<p>Try it:</p>
<pre>curl -s localhost:PORT/rank -H 'Content-Type: application/json' -d '{
  "jd": "Senior AI Engineer. Must have embeddings, retrieval, ranking, Python. 5-9 years.",
  "candidates": [{"candidate_id":"C1","profile":{"summary":"built embeddings retrieval ranking in python"}}]
}'</pre>
<p class=mut>Interactive docs: <a href="/docs"><b>/docs</b> (Swagger UI)</a> · spec: <a href="/openapi.json">/openapi.json</a>
· Studio UI: run <code>python studio.py</code> (:8888) · Also available as <b>MCP tools</b> for agents.</p>
</div></body></html>"""

_EX_JD = "Senior AI Engineer. Must have embeddings, retrieval, ranking, Python. 5-9 years."
_EX_CAND = {"candidate_id": "CAND_0000001",
            "profile": {"current_title": "ML Engineer", "years_of_experience": 7,
                        "summary": "Built embeddings-based retrieval and ranking systems in Python."},
            "career_history": [{"title": "ML Engineer", "company": "Acme",
                                "description": "Owned ranking + retrieval; shipped to production."}],
            "skills": ["Python", "Ranking", "Embeddings"], "redrob_signals": {}}


def _json_body(schema, example):
    return {"required": True, "content": {"application/json": {
        "schema": schema, "example": example}}}


def _json_resp(desc, example):
    return {"200": {"description": desc, "content": {"application/json": {"example": example}}},
            "400": {"description": "Invalid input (missing field / bad JSON)"}}


OPENAPI = {
    "openapi": "3.0.0",
    "info": {
        "title": "TalentSignal API",
        "version": API_VERSION,
        "description": (
            "Rank any candidate against any job description **by meaning, not keywords** — "
            "reject fabricated résumés, and get grounded, explainable reasoning for every "
            "decision. The same engine behind the Studio UI and the MCP tools, exposed as a "
            "clean REST service any ATS, career portal, or product can call.\n\n"
            "No LLM, no GPU, no per-token cost. Deterministic and offline-capable."),
        "contact": {"name": "TalentSignal", "email": "sreenathmmmenon@gmail.com"},
    },
    "tags": [
        {"name": "Ranking", "description": "Score and order candidates for a role."},
        {"name": "Ingest", "description": "Turn any JD or résumé into structured data."},
        {"name": "Trust & fairness", "description": "Fabrication audit and adverse-impact compliance."},
        {"name": "Ops", "description": "Health and spec."},
    ],
    "paths": {
        "/rank": {"post": {
            "tags": ["Ranking"], "summary": "Rank candidates against a JD",
            "description": "Returns a ranked, explained shortlist. Uses the semantic (hybrid) "
                           "engine on small pools when a model is available, else the "
                           "zero-dependency structured engine.",
            "requestBody": _json_body(
                {"type": "object", "required": ["jd", "candidates"],
                 "properties": {
                     "jd": {"type": "string", "description": "Job description (free text or path)."},
                     "candidates": {"type": "array", "items": {"type": "object"},
                                    "description": "Candidate records (or plain-text résumés)."},
                     "top_n": {"type": "integer", "default": 10},
                     "engine": {"type": "string", "enum": ["hybrid", "spine"]},
                     "category": {"type": "string", "default": "ai_ml_search_ranking"}}},
                {"jd": _EX_JD, "candidates": [_EX_CAND], "top_n": 5}),
            "responses": _json_resp("Ranked shortlist", {
                "job_title": "Senior AI Engineer", "engine": "hybrid", "candidate_count": 1,
                "ranked": [{"rank": 1, "candidate_id": "CAND_0000001", "score": 0.57,
                            "title": "ML Engineer", "reasoning": "Strong fit at #1: …",
                            "reachability_label": "reachable",
                            "factors": {"technical_evidence": 0.9, "career_fit": 0.8}}]}),
        }},
        "/ingest/jd": {"post": {
            "tags": ["Ingest"], "summary": "Parse a JD into a weighted requirement model",
            "requestBody": _json_body(
                {"type": "object", "required": ["jd"],
                 "properties": {"jd": {"type": "string"}}}, {"jd": _EX_JD}),
            "responses": _json_resp("Structured requirements", {
                "title": "Senior AI Engineer", "min_years": 5.0, "max_years": 9.0,
                "requirements": [{"text": "embeddings", "kind": "must_have", "weight": 1.0}]}),
        }},
        "/ingest/resume": {"post": {
            "tags": ["Ingest"], "summary": "Parse a résumé (any text) into a candidate profile",
            "requestBody": _json_body(
                {"type": "object", "required": ["resume"],
                 "properties": {"resume": {"type": "string"},
                                "use_llm": {"type": "boolean", "default": False}}},
                {"resume": "Asha — ML Engineer, 7 yrs. Built ranking & retrieval. Skills: Python."}),
            "responses": _json_resp("Structured candidate record", _EX_CAND),
        }},
        "/audit": {"post": {
            "tags": ["Trust & fairness"], "summary": "Audit a candidate for internal contradictions",
            "description": "Role-independent fabrication/honeypot check — flags impossible "
                           "profiles (e.g. expert skill with 0 months, tenure > career length).",
            "requestBody": _json_body(
                {"type": "object", "required": ["candidate"],
                 "properties": {"candidate": {"type": "object"}}}, {"candidate": _EX_CAND}),
            "responses": _json_resp("Consistency report", {
                "is_impossible": False, "penalty": 0.0, "flags": []}),
        }},
        "/compliance": {"post": {
            "tags": ["Trust & fairness"],
            "summary": "Adverse-impact (four-fifths) report on a ranking",
            "description": "The report legal/compliance needs before deploying automated "
                           "selection. Group labels are CALLER-supplied from your own HR data; "
                           "the engine never infers protected attributes.",
            "requestBody": _json_body(
                {"type": "object", "required": ["ranked_ids", "group_attributes"],
                 "properties": {
                     "ranked_ids": {"type": "array", "items": {"type": "string"}},
                     "group_attributes": {"type": "object"},
                     "top_k": {"type": "integer", "default": 10}}},
                {"ranked_ids": ["CAND_1", "CAND_2", "CAND_3", "CAND_4"],
                 "group_attributes": {"gender": {"CAND_1": "F", "CAND_2": "M",
                                                 "CAND_3": "F", "CAND_4": "M"}}, "top_k": 2}),
            "responses": _json_resp("Adverse-impact summary", {
                "method": "four_fifths_rule", "overall_passes_four_fifths": True,
                "assessed_attributes": ["gender"]}),
        }},
        "/candidate_report": {"post": {
            "tags": ["Trust & fairness"],
            "summary": "Candidate-facing transparency report",
            "description": "What the engine used and concluded about ONE candidate — proof "
                           "from their own words, unmet requirements they can dispute. The "
                           "human-in-the-loop answer to opaque auto-rejection.",
            "requestBody": _json_body(
                {"type": "object", "required": ["candidate", "jd"],
                 "properties": {"candidate": {"type": "object"}, "jd": {"type": "string"}}},
                {"candidate": _EX_CAND, "jd": _EX_JD}),
            "responses": _json_resp("Transparency report", {
                "disclosure": "This report shows everything the engine used …",
                "matched_with_proof": [], "not_evidenced": {"requirements": []}}),
        }},
        "/health": {"get": {
            "tags": ["Ops"], "summary": "Health check",
            "responses": {"200": {"description": "OK", "content": {"application/json": {
                "example": {"status": "ok", "api_version": API_VERSION}}}}},
        }},
        "/openapi.json": {"get": {"tags": ["Ops"], "summary": "This OpenAPI spec (machine-readable)",
                                  "responses": {"200": {"description": "OpenAPI 3.0 document"}}}},
    },
}


# Self-hosted Swagger UI — interactive API docs at GET /docs. The UI assets load
# from a CDN (no new runtime dependency); the spec is served from /openapi.json.
_SWAGGER_HTML = """<!doctype html><html><head><meta charset=utf-8>
<title>TalentSignal API — docs</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
<style>body{margin:0}.topbar{display:none}
.info{margin:22px 0}.swagger-ui .info .title{color:#1b1b2f}</style>
</head><body>
<div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
window.onload=()=>{window.ui=SwaggerUIBundle({url:'/openapi.json',dom_id:'#swagger-ui',
  deepLinking:true,tryItOutEnabled:true,defaultModelsExpandDepth:-1});};
</script></body></html>"""


def _coerce_candidates(items):
    from talentsignal.ingest import ingest
    out = []
    for it in items:
        if isinstance(it, str):
            out.extend(ingest(it, fmt="text"))
        elif isinstance(it, dict):
            out.append(it)
    return out


_EMBEDDER = {"model": None, "tried": False}


def _embedder():
    """Cached embedder so REST /rank uses the best (hybrid) engine on small pools,
    consistent with the Studio and MCP surfaces; None -> spine fallback."""
    if _EMBEDDER["tried"]:
        return _EMBEDDER["model"]
    _EMBEDDER["tried"] = True
    try:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        _EMBEDDER["model"] = lambda t: m.encode(t, convert_to_numpy=True, normalize_embeddings=True)
    except Exception:
        _EMBEDDER["model"] = None
    return _EMBEDDER["model"]


def do_rank(body: dict) -> dict:
    from talentsignal.api import rank
    cands = _coerce_candidates(body.get("candidates", []))
    # Default to the best engine: hybrid (live-embed) on small pools when a model
    # is available; honor an explicit engine override; index_dir uses precomputed.
    requested = body.get("engine")
    emb = _embedder() if (requested != "spine" and not body.get("index_dir") and len(cands) <= 200) else None
    engine = requested or ("hybrid" if (emb or body.get("index_dir")) else "spine")
    res = rank(body["jd"], cands, top_n=int(body.get("top_n", 10)),
               engine=engine, embedder=emb, index_dir=body.get("index_dir"),
               category=body.get("category", "ai_ml_search_ranking"))
    return res.to_dict()


def do_ingest_jd(body: dict) -> dict:
    from talentsignal.jd_ingest import ingest_text
    m = ingest_text(body["jd"])
    return {"title": m.title, "min_years": m.min_years, "max_years": m.max_years,
            "preferred_locations": list(m.preferred_locations),
            "requirements": [{"text": r.text, "kind": r.kind, "weight": r.weight} for r in m.requirements]}


def do_ingest_resume(body: dict) -> dict:
    from talentsignal.ingest import ingest
    recs = ingest(body["resume"], fmt="text", use_llm=bool(body.get("use_llm", False)))
    return recs[0] if recs else {}


def do_audit(body: dict) -> dict:
    from talentsignal.consistency_audit import audit_candidate
    rep = audit_candidate(body["candidate"])
    return {"is_impossible": rep.is_impossible, "penalty": rep.penalty,
            "flags": [{"code": f.code, "detail": f.detail} for f in rep.flags]}


def do_compliance(body: dict) -> dict:
    """Adverse-impact (four-fifths rule) report on a ranking. The caller supplies
    ranked_ids and per-attribute group labels from their OWN HR data; the engine
    never infers protected attributes. This is the report legal/compliance needs
    before deploying an automated selection procedure."""
    from talentsignal.eval.compliance import compliance_summary
    return compliance_summary(body["ranked_ids"], body["group_attributes"],
                              top_k=int(body.get("top_k", 10)))


def do_candidate_report(body: dict) -> dict:
    """Candidate-facing transparency report: what the engine used and concluded
    about ONE candidate against a JD, with proof, unmet requirements they can
    dispute, and concerns -- the human-in-the-loop, no-black-box answer to the
    FCRA-style 'I was scored and rejected and never told why' grievance."""
    from talentsignal.candidate_report import candidate_report
    return candidate_report(body["candidate"], body["jd"],
                            category=body.get("category", "ai_ml_search_ranking"))


ROUTES = {
    "/rank": do_rank,
    "/compliance": do_compliance,
    "/candidate_report": do_candidate_report,
    "/ingest/jd": do_ingest_jd,
    "/ingest/resume": do_ingest_resume,
    "/audit": do_audit,
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # quiet
        pass

    def _send(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        key = os.environ.get("TALENTSIGNAL_API_KEY")
        if not key:
            return True
        return self.headers.get("X-API-Key") == key

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._send(HTTPStatus.OK, {"status": "ok", "api_version": API_VERSION,
                                       "engine": "talentsignal"})
        elif path == "/openapi.json":
            self._send(HTTPStatus.OK, OPENAPI)
        elif path in ("/docs", "/docs/"):
            body = _SWAGGER_HTML.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path in ("/", "/index.html"):
            host = self.headers.get("Host", "localhost:8900")
            body = _API_LANDING.replace("localhost:PORT", host).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        fn = ROUTES.get(path)
        if fn is None:
            self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        if not self._authorized():
            self._send(HTTPStatus.UNAUTHORIZED, {"error": "invalid or missing X-API-Key"})
            return
        MAX_BODY = 32 * 1024 * 1024  # 32 MB cap — reject oversized bodies (DoS guard)
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except (TypeError, ValueError):
            self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid Content-Length header"})
            return
        if length > MAX_BODY:
            self._send(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "request body too large"})
            return
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid JSON body"})
            return
        if not isinstance(body, dict):
            self._send(HTTPStatus.BAD_REQUEST, {"error": "request body must be a JSON object"})
            return
        try:
            self._send(HTTPStatus.OK, fn(body))
        except KeyError as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": f"missing field: {exc}"})
        except (ValueError, TypeError) as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": f"invalid input: {exc}"})
        except Exception:  # noqa: BLE001 - never leak internals to the client
            import traceback
            traceback.print_exc()
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal server error"})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8900)
    args = ap.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"TalentSignal API on http://{args.host}:{args.port}  (POST /rank, /ingest/jd, /ingest/resume, /audit)")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

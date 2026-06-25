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

OPENAPI = {
    "openapi": "3.0.0",
    "info": {"title": "TalentSignal API", "version": API_VERSION,
             "description": "Universal candidate-intelligence ranking engine."},
    "paths": {
        "/rank": {"post": {"summary": "Rank candidates against a JD"}},
        "/ingest/jd": {"post": {"summary": "Parse a JD into requirements"}},
        "/ingest/resume": {"post": {"summary": "Parse a resume into a profile"}},
        "/audit": {"post": {"summary": "Audit a candidate for contradictions"}},
        "/compliance": {"post": {"summary": "Adverse-impact (four-fifths) report on a ranking"}},
        "/health": {"get": {"summary": "Health check"}},
    },
}


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
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            self._send(HTTPStatus.OK, fn(body))
        except KeyError as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": f"missing field: {exc}"})
        except Exception as exc:  # noqa: BLE001
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"{type(exc).__name__}: {exc}"})


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

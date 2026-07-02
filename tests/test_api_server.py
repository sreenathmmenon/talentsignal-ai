"""REST API + Python SDK: a live server over the engine facade, exercised through
the SDK client. Uses an ephemeral port and a background server thread.
"""
from __future__ import annotations

import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import api_server
from talentsignal.client import TalentSignalClient


def _start_server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), api_server.Handler)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    return srv, port


def test_rest_api_end_to_end():
    srv, port = _start_server()
    try:
        c = TalentSignalClient(f"http://127.0.0.1:{port}")
        # health
        assert c.health()["status"] == "ok"
        # ingest jd
        jd = c.ingest_jd("Senior AI Engineer. Must have embeddings and ranking. 5-9 years. Pune.")
        assert jd["min_years"] == 5.0 and len(jd["requirements"]) >= 1
        # screen resume
        r = c.screen_resume("Asha\nBangalore, India\nML Engineer with 7 years.\n"
                            "Experience\nML Engineer at Flipkart 2021 - present\nBuilt ranking.\n"
                            "Skills\nPython, Ranking")
        assert r["profile"]["years_of_experience"] == 7.0
        # rank (resume text accepted)
        res = c.rank("AI Engineer: embeddings, ranking, production ML. 5-9 years.",
                     ["Asha\nML Engineer 7 years ranking embeddings\nSkills\nPython, Ranking"], top_n=1)
        assert res["ranked"][0]["candidate_id"]
        assert "reasoning" in res["ranked"][0]
    finally:
        srv.shutdown()


def test_openapi_and_404():
    srv, port = _start_server()
    try:
        c = TalentSignalClient(f"http://127.0.0.1:{port}")
        spec = c._get("/openapi.json")
        assert spec["info"]["title"] == "TalentSignal API"
        # the spec is now rich: every endpoint documented, POSTs carry examples
        paths = spec["paths"]
        for ep in ("/rank", "/ingest/jd", "/ingest/resume", "/audit", "/compliance",
                   "/candidate_report", "/health"):
            assert ep in paths, ep
        assert "requestBody" in paths["/rank"]["post"]
        assert paths["/rank"]["post"]["requestBody"]["content"]["application/json"]["example"]
    finally:
        srv.shutdown()


def test_swagger_docs_page_serves():
    import urllib.request
    srv, port = _start_server()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/docs", timeout=10) as r:
            html = r.read().decode()
        assert r.status == 200 and "swagger-ui" in html
    finally:
        srv.shutdown()

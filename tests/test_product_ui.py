"""Product UI server: serves the SPA and ingests-then-ranks uploaded/pasted
candidates of any format through the same engine facade.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib import request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import product_ui


def _start():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), product_ui.Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.1)
    return srv, port


def test_page_serves():
    srv, port = _start()
    try:
        with request.urlopen(f"http://127.0.0.1:{port}/") as r:
            html = r.read().decode()
        assert "TalentSignal" in html and "Rank candidates" in html
    finally:
        srv.shutdown()


def test_ingest_inputs_text_and_json():
    # the core helper: pasted text + a json candidate both become records
    recs = product_ui._ingest_inputs(
        files=[{"name": "a.txt", "ext": "txt",
                "text": "Asha\nML Engineer 7 years ranking embeddings\nSkills\nPython, Ranking"}],
        paste='[{"candidate_id":"CAND_0000005","profile":{"current_title":"X"},'
              '"career_history":[],"skills":[],"redrob_signals":{}}]',
    )
    assert len(recs) == 2


def test_rank_endpoint_with_pasted_resumes():
    srv, port = _start()
    try:
        body = {
            "jd": "Senior AI Engineer: embeddings, retrieval, ranking, production ML. 5-9 years.",
            "category": "ai_ml_search_ranking", "top_n": 2,
            "files": [], "paste": (
                "Asha\nBangalore, India\nML Engineer 7 years ranking embeddings.\n"
                "Experience\nML Engineer at Flipkart 2021 - present\nBuilt ranking.\nSkills\nPython, Ranking\n\n"
                "Rahul\nPune\nBackend Engineer 6 years java services.\nSkills\nJava, SQL"
            ),
        }
        req = request.Request(f"http://127.0.0.1:{port}/api/rank",
                              data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with request.urlopen(req) as r:
            data = json.loads(r.read())
        assert "error" not in data, data
        assert data["candidate_count"] == 2
        assert len(data["ranked"]) == 2
        assert all("reasoning" in c for c in data["ranked"])
    finally:
        srv.shutdown()

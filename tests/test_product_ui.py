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
    # product_ui's "/" now points visitors to the canonical Studio product
    # (the GUIs were consolidated); it still serves a valid TalentSignal page.
    srv, port = _start()
    try:
        with request.urlopen(f"http://127.0.0.1:{port}/") as r:
            html = r.read().decode()
        assert "TalentSignal" in html and "studio.py" in html
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


def test_studio_rank_has_verdict_and_skills_match():
    """The canonical Studio rank payload carries the UI-polish fields: a one-line
    verdict + a Matched/Missing skills view, grounded in the engine's own data."""
    import importlib.util
    ROOT = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("studio", ROOT / "studio.py")
    studio = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(studio)
    out = studio.do_rank({
        "jd": "Senior AI Engineer. Must have embeddings, retrieval, ranking, Python. 5-9 years.",
        "paste": ("Asha\nML Engineer 7y. Built embeddings retrieval ranking in Python.\nSkills\nPython, Ranking, Embeddings\n\n"
                  "Rahul\nBackend Engineer 6y java services.\nSkills\nJava, SQL"),
        "files": [],
    })
    assert "error" not in out, out
    for c in out["ranked"]:
        assert c["verdict"]["label"] and c["verdict"]["tone"]
        assert "matched" in c["skills_match"] and "missing" in c["skills_match"]
    # the strong AI candidate should read as a match; the backend one should not
    top = out["ranked"][0]
    assert top["verdict"]["tone"] in ("strong", "good")
    assert top["skills_match"]["matched"]


def test_studio_transparency_endpoint():
    import importlib.util
    ROOT = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("studio", ROOT / "studio.py")
    studio = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(studio)
    out = studio.do_transparency({
        "jd": "Senior AI Engineer. Must have embeddings retrieval ranking evaluation. 5-9y.",
        "paste": "Maya. Senior AI Engineer 7y. Built embeddings retrieval and ranking. Skills: Python, Ranking",
        "files": [],
    })
    assert "disclosure" in out and "matched_with_proof" in out
    assert "never reads your name" in out["data_used"]["identity_used"].lower()

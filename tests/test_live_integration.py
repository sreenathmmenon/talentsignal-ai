"""Live integration tests — start the REAL REST server on a socket and the REAL
MCP server over stdio, and exercise them end-to-end. The handler logic is unit-
tested elsewhere; this proves the servers actually bind, route, and respond over a
real connection (the thing a customer/agent hits)."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "HF_HUB_OFFLINE": "1", "TOKENIZERS_PARALLELISM": "false",
       "PYTHONPATH": str(ROOT / "src")}


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


# --- REST server over a real socket -------------------------------------------

@pytest.fixture(scope="module")
def rest_server():
    port = _free_port()
    proc = subprocess.Popen([sys.executable, "api_server.py", "--port", str(port)],
                            cwd=str(ROOT), env=ENV,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    # wait for it to come up
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/health", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    yield base
    proc.terminate()
    proc.wait(timeout=5)


def _post(base, path, body):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, json.loads(r.read().decode())


def test_rest_health(rest_server):
    with urllib.request.urlopen(rest_server + "/health", timeout=5) as r:
        assert r.status == 200
        body = json.loads(r.read().decode())
        assert body.get("status") in ("ok", "healthy") or "status" in body


def test_rest_rank_end_to_end(rest_server):
    cands = [{"candidate_id": "CAND_0000001",
              "profile": {"summary": "embeddings retrieval ranking python ndcg",
                          "current_title": "AI Engineer", "years_of_experience": 7},
              "career_history": [{"title": "AI Engineer", "description": "ranking retrieval", "duration_months": 84}],
              "skills": ["Python"], "redrob_signals": {"open_to_work_flag": True}}]
    status, body = _post(rest_server, "/rank",
                         {"jd": "AI Engineer. Must have embeddings, retrieval, ranking, python. 5-9 years.",
                          "candidates": cands})
    assert status == 200
    assert body.get("ranked") and body["ranked"][0]["candidate_id"] == "CAND_0000001"


def test_rest_ingest_jd_end_to_end(rest_server):
    status, body = _post(rest_server, "/ingest/jd",
                         {"jd": "Nurse. Must have patient care, EMR, BLS. 3-7 years."})
    assert status == 200
    # parsed into a structured model with requirements
    assert any(k in body for k in ("requirements", "must_have", "title"))


def test_rest_bad_json_is_400_not_500(rest_server):
    req = urllib.request.Request(rest_server + "/rank", data=b"{not json",
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
        assert False, "expected an HTTP error"
    except urllib.error.HTTPError as e:
        assert e.code == 400  # invalid JSON -> 400, never a 500 leak


# --- MCP server over real stdio -----------------------------------------------

def _mcp_call(requests):
    """Pipe JSON-RPC lines into the real MCP server process; return parsed lines."""
    inp = "\n".join(json.dumps(r) for r in requests) + "\n"
    proc = subprocess.run([sys.executable, "mcp_server.py"], cwd=str(ROOT), env=ENV,
                          input=inp.encode(), capture_output=True, timeout=60)
    return [json.loads(l) for l in proc.stdout.decode().splitlines() if l.strip()]


def test_mcp_tools_list_over_stdio():
    out = _mcp_call([{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}])
    assert out and "result" in out[0]
    names = [t["name"] for t in out[0]["result"]["tools"]]
    assert "rank_candidates" in names and len(names) >= 5


def test_mcp_survives_bad_line_then_serves_valid():
    # a non-dict line must NOT kill the server; the following valid request still works
    out = _mcp_call([123, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}])
    # the valid tools/list response must be present
    assert any(o.get("id") == 2 and "result" in o for o in out)

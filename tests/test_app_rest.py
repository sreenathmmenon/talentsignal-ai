from __future__ import annotations

import json
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import AppHandler
from http.server import ThreadingHTTPServer


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def start_server() -> tuple[ThreadingHTTPServer, str]:
    port = free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), AppHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{port}"


def request_json(url: str, payload: dict | None = None, timeout: int = 60) -> dict:
    if payload is None:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def test_status_and_rank_api_with_real_sample_file() -> None:
    server, base = start_server()
    try:
        status = request_json(base + "/api/status")
        assert status["status"] == "ok"
        result = request_json(
            base + "/api/rank",
            {
                "candidates_path": "[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl",
                "job_spec": "job_specs/redrob_senior_ai_engineer.yaml",
                "top_n": 5,
            },
            timeout=240,
        )
        assert len(result["rows"]) == 5
        assert result["summary"]["top10_eligible_count"] == 5
        assert Path(result["files"]["submission"]).exists()
        assert result["rows"][0]["candidate_id"].startswith("CAND_")
        assert result["job"]["category_label"]
        assert result["v2"]["analysis_rows"] >= 5
        assert result["v2"]["top_compare"]["left_rank"] == 1
        assert result["v2"]["boundary_review"]["windows"]
        assert result["v2"]["interview_kits"][0]["questions"]
    finally:
        server.shutdown()
        server.server_close()

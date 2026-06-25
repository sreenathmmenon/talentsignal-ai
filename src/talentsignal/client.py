"""TalentSignal Python SDK — a thin client for the REST API.

For integrators who want to call a hosted TalentSignal service rather than embed
the engine. Stdlib-only (urllib), so it has no dependencies.

    from talentsignal.client import TalentSignalClient

    client = TalentSignalClient("http://localhost:8900", api_key="...")
    result = client.rank(jd="Senior AI Engineer ...", candidates=[...], top_n=10)
    for c in result["ranked"]:
        print(c["rank"], c["candidate_id"], c["score"])
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any


class TalentSignalClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8900", api_key: str | None = None,
                 timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.base_url + path, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("X-API-Key", self.api_key)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _get(self, path: str) -> dict[str, Any]:
        req = urllib.request.Request(self.base_url + path, method="GET")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # --- API ---

    def health(self) -> dict[str, Any]:
        return self._get("/health")

    def rank(self, jd: str, candidates: list, *, top_n: int = 10, engine: str | None = None,
             category: str = "ai_ml_search_ranking", index_dir: str | None = None) -> dict[str, Any]:
        # engine=None lets the server pick the best available engine (hybrid when a
        # model is present, spine otherwise). Pass engine="spine"/"hybrid" to force.
        payload = {"jd": jd, "candidates": candidates, "top_n": top_n,
                   "category": category, "index_dir": index_dir}
        if engine is not None:
            payload["engine"] = engine
        return self._post("/rank", payload)

    def ingest_jd(self, jd: str) -> dict[str, Any]:
        return self._post("/ingest/jd", {"jd": jd})

    def screen_resume(self, resume: str, *, use_llm: bool = False) -> dict[str, Any]:
        return self._post("/ingest/resume", {"resume": resume, "use_llm": use_llm})

    def audit(self, candidate: dict) -> dict[str, Any]:
        return self._post("/audit", {"candidate": candidate})

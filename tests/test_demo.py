"""Demo / sandbox: any JD (free-text or YAML) + any candidate file produces a
valid ranked, explainable shortlist. Uses the lexical-only hybrid fallback so
the test needs no embedding model (CI-safe).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.io import iter_candidates
from talentsignal.ranking import score_pool_hybrid, _rows_from_scored

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "scripts" / "demo_rank.py"
spec = importlib.util.spec_from_file_location("demo_rank", DEMO)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


def test_build_job_from_free_text_md() -> None:
    job = demo.build_job(str(ROOT / "demo/data/sales_jd.md"), "sales_gtm")
    assert job.requirements and job.must_have


def test_build_job_from_yaml() -> None:
    job = demo.build_job(str(ROOT / "job_specs/redrob_senior_ai_engineer.yaml"), "ai_ml_search_ranking")
    assert job.id == "redrob_senior_ai_engineer"


def test_demo_ranks_any_jd_lexical_only() -> None:
    # free-text JD + candidate file -> valid shortlist (lexical-only path)
    job = demo.build_job(str(ROOT / "demo/data/sales_jd.md"), "sales_gtm")
    records = list(iter_candidates(str(ROOT / "demo/data/sales_candidates.jsonl")))
    scored = score_pool_hybrid(records, job)  # no embeddings -> lexical-only
    rows = _rows_from_scored(scored, job, 10)
    assert len(rows) == 10
    assert all(r["reasoning"] for r in rows)
    # ranks are unique 1..10
    assert sorted(r["rank"] for r in rows) == list(range(1, 11))

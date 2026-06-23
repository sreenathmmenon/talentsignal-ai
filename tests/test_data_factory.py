"""The data factory writes schema-valid datasets + JDs that rank correctly
through the real pipeline, for every role and for the alternate signal schema.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.eval.jd_library import JDS
from talentsignal.eval.roles import ROLES
from talentsignal.jd_parser import load_job_spec
from talentsignal.ranking import rank_records
from talentsignal.eval import metrics

ROOT = Path(__file__).resolve().parents[1]
FACTORY = ROOT / "scripts" / "generate_datasets.py"
spec = importlib.util.spec_from_file_location("generate_datasets", FACTORY)
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)


def test_jd_library_covers_all_roles() -> None:
    assert set(JDS) == set(ROLES)
    for role_id, jd in JDS.items():
        assert jd.text.strip()
        assert Path(ROOT / jd.spec_path).exists(), jd.spec_path


def test_factory_writes_role_and_it_ranks(tmp_path: Path) -> None:
    out = tmp_path / "data"
    out.mkdir()
    info = factory.write_role("sales", out, "redrob", factory.DEMO_MIX)
    # files exist
    for key in ("candidates", "labels", "jd_text"):
        assert Path(info[key]).exists()
    # candidates rank sensibly with the role's own JD
    records = [json.loads(l) for l in Path(info["candidates"]).read_text().splitlines() if l.strip()]
    labels = {k: v["grade"] for k, v in json.loads(Path(info["labels"]).read_text()).items()}
    job = load_job_spec(JDS["sales"].spec_path)
    rows = rank_records(records, job, top_n=len(records))
    rels = metrics.relevances_from_ranking([r["candidate_id"] for r in rows], labels)
    assert metrics.ndcg_at_k(rels, 10) >= 0.6


def test_factory_alt_schema(tmp_path: Path) -> None:
    out = tmp_path / "alt"
    out.mkdir()
    info = factory.write_role("ai_search", out, "alt", factory.DEMO_MIX)
    records = [json.loads(l) for l in Path(info["candidates"]).read_text().splitlines() if l.strip()]
    # alt schema uses different signal field names
    sig = records[0]["redrob_signals"]
    assert "reply_rate" in sig and "recruiter_response_rate" not in sig

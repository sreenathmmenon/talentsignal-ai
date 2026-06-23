"""Regression gates on the eval harness. These pin the qualities we must not
lose: the spine ranks each role well, keeps honeypots out of the very top on
balanced pools, stays JD-agnostic (low cross-JD overlap), and never crashes on a
non-Redrob signal schema. The paraphrase weakness is recorded (not gated up)
because closing it is Story 4's job — we assert it stays measurable.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import importlib.util

HARNESS = Path(__file__).resolve().parents[1] / "scripts" / "eval_harness.py"
spec = importlib.util.spec_from_file_location("eval_harness", HARNESS)
eh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eh)


def test_per_role_quality_threshold() -> None:
    out = eh.suite_per_role(eh.spine_ranker)
    # The spine should rank each role's own pool well; mean composite is the gate.
    assert out["mean_composite"] >= 0.80, out["mean_composite"]
    # Every role should be at least reasonable (no role collapses).
    for role, m in out["per_role"].items():
        assert m["ndcg@10"] >= 0.60, (role, m["ndcg@10"])


def test_generality_low_overlap() -> None:
    out = eh.suite_generality(eh.spine_ranker)
    # Different JDs must not surface the same people.
    assert out["mean_top10_jaccard_overlap"] <= 0.20, out


def test_perturbation_contradiction_drops() -> None:
    out = eh.suite_perturbation(eh.spine_ranker)
    assert out["contradicted_below_strong"] is True, out


def test_schema_agnostic_runs() -> None:
    out = eh.suite_schema(eh.spine_ranker)
    assert out["ran_without_error"] is True, out


def test_paraphrase_is_measured() -> None:
    # Story 4 (semantic) should lift this; for now we only require it's measurable
    # and the harness reports a numeric mean rank.
    out = eh.suite_paraphrase(eh.spine_ranker)
    assert out["paraphrase_ideal_mean_rank"] is not None
    assert out["total_paraphrase_ideals"] == 10

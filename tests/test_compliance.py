"""Hiring-compliance (adverse-impact / four-fifths rule) analysis. The math is
pinned to hand-computed values; group labels are customer-supplied, never inferred.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.eval.compliance import adverse_impact, compliance_summary


def test_four_fifths_fail():
    # Group A: 8/10 selected (0.80), Group B: 3/10 (0.30) -> ratio 0.375 < 0.80
    ranked = [f"A{i}" for i in range(8)] + [f"B{i}" for i in range(3)] + ["x"] * 40
    group = {**{f"A{i}": "A" for i in range(10)}, **{f"B{i}": "B" for i in range(10)}}
    r = adverse_impact(ranked, group, top_k=11)
    assert abs(r.min_impact_ratio - 0.375) < 0.01
    assert r.passes_four_fifths is False


def test_four_fifths_pass():
    ranked = [f"A{i}" for i in range(5)] + [f"B{i}" for i in range(5)]
    group = {**{f"A{i}": "A" for i in range(10)}, **{f"B{i}": "B" for i in range(10)}}
    r = adverse_impact(ranked, group, top_k=10)
    assert r.min_impact_ratio == 1.0
    assert r.passes_four_fifths is True


def test_small_groups_excluded():
    ranked = ["A0", "A1", "B0"]
    group = {"A0": "A", "A1": "A", "A2": "A", "A3": "A", "A4": "A", "A5": "A", "B0": "tiny"}
    r = adverse_impact(ranked, group, top_k=3, min_group_size=5)
    # 'tiny' has 1 member -> excluded with a note
    assert any("too small" in n for n in r.notes)


def test_summary_multi_attribute_serializes():
    ranked = [f"c{i}" for i in range(10)]
    attrs = {
        "gender": {f"c{i}": ("x" if i % 2 else "y") for i in range(20)},
        "age_band": {f"c{i}": ("under35" if i < 10 else "over35") for i in range(20)},
    }
    s = compliance_summary(ranked, attrs, top_k=5)
    assert "overall_passes_four_fifths" in s
    assert set(s["attributes"]) == {"gender", "age_band"}
    assert "four-fifths" in s["method"]


def test_identity_blind_note_present():
    s = compliance_summary(["a"], {"g": {"a": "x"}}, top_k=1)
    assert "identity-blind" in s["engine_property"]


def test_discloses_incomplete_label_coverage():
    # candidate 'c' is ranked but unlabeled -> the report must say so (an unlabeled
    # ranked candidate silently dropped could mask adverse impact)
    r = adverse_impact(["a", "b", "c"], {"a": "x", "b": "y"}, top_k=2)
    assert any("coverage" in n.lower() and "unlabeled" in n.lower() for n in r.notes)


def test_no_coverage_warning_when_complete():
    r = adverse_impact(["a", "b"], {"a": "x", "b": "y"}, top_k=2)
    assert not any("coverage:" in n.lower() for n in r.notes)

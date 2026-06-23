"""Schema-driven signals normalize availability/engagement/trust from ANY signal
vocabulary, so active candidates beat stale ones on Redrob AND alternate schemas.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.schema_profile import schema_signals, overall_hireability
from talentsignal.eval import datasets as D
from talentsignal.eval.roles import AI_SEARCH


def test_dimensions_present_and_bounded() -> None:
    c = D.make_candidate(AI_SEARCH, D.STRONG, 0).record
    s = schema_signals(c)
    assert set(s) == {"availability", "engagement", "trust"}
    assert all(0.0 <= v <= 1.0 for v in s.values())


def test_active_beats_stale_redrob_schema() -> None:
    active = D.make_candidate(AI_SEARCH, D.STRONG, 5, schema_variant="redrob").record
    stale = D.make_candidate(AI_SEARCH, D.BEHAVIORAL_TWIN, 5, schema_variant="redrob").record
    assert overall_hireability(active) > overall_hireability(stale) + 0.2


def test_active_beats_stale_alt_schema() -> None:
    # Different field names entirely; the engine must still discriminate.
    active = D.make_candidate(AI_SEARCH, D.STRONG, 5, schema_variant="alt").record
    stale = D.make_candidate(AI_SEARCH, D.BEHAVIORAL_TWIN, 5, schema_variant="alt").record
    assert "recruiter_response_rate" not in active["redrob_signals"]
    assert overall_hireability(active) > overall_hireability(stale) + 0.2


def test_unknown_schema_defaults_neutral() -> None:
    c = {"redrob_signals": {"some_unknown_field": 42, "another": "x"}}
    s = schema_signals(c)
    # nothing recognized -> all neutral 0.5, no crash
    assert s == {"availability": 0.5, "engagement": 0.5, "trust": 0.5}


def test_empty_signals_safe() -> None:
    assert schema_signals({}) == {"availability": 0.5, "engagement": 0.5, "trust": 0.5}

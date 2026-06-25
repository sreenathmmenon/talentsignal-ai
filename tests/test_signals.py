"""Signal plugin framework: built-in signals wrap existing intelligence, roadmap
stubs are wired, and new signals register without touching the core.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.signals import compute_signals, list_signals, register_signal, Signal, SignalResult
from talentsignal.signals.base import blended_signal_score
from talentsignal.eval import datasets as D
from talentsignal.eval.roles import AI_SEARCH


def test_builtin_signals_registered() -> None:
    for name in ("hireability", "consistency", "github_activity",
                 "background_verification", "github_repo_analysis"):
        assert name in list_signals()


def test_consistency_signal_separates_honeypot() -> None:
    strong = D.make_candidate(AI_SEARCH, D.STRONG, 1).record
    honey = D.make_candidate(AI_SEARCH, D.HONEYPOT, 1).record
    s = compute_signals(strong)["consistency"].score
    h = compute_signals(honey)["consistency"].score
    assert s > h  # clean candidate scores higher than the contradictory honeypot
    assert s == 1.0


def test_hireability_signal_present_and_bounded() -> None:
    rec = D.make_candidate(AI_SEARCH, D.STRONG, 2).record
    r = compute_signals(rec)["hireability"]
    assert 0.0 <= r.score <= 1.0 and r.evidence


def test_roadmap_stubs_have_zero_weight() -> None:
    # background_verification is still a wired stub (weight 0 until connected)
    rec = D.make_candidate(AI_SEARCH, D.STRONG, 3).record
    res = compute_signals(rec)
    assert res["background_verification"].weight == 0.0


def test_github_signal_is_real_and_zero_weight_when_applicable(monkeypatch) -> None:
    # github_repo_analysis is now a REAL signal; it only applies when the candidate
    # links a GitHub profile, and stays weight 0 (surfaced evidence, opt-in to blend).
    # Force offline so the test never hits the network (deterministic/CI-safe).
    import talentsignal.github_analysis as g
    monkeypatch.setattr(g, "_get", lambda url, timeout: (_ for _ in ()).throw(OSError("offline")))
    rec = D.make_candidate(AI_SEARCH, D.STRONG, 3).record
    rec["profile"]["summary"] = rec["profile"].get("summary", "") + " github.com/dev"
    res = compute_signals(rec, only=["github_repo_analysis"])
    assert "github_repo_analysis" in res
    assert res["github_repo_analysis"].weight == 0.0


def test_custom_signal_registers_and_runs() -> None:
    @register_signal
    class _AvgTenure(Signal):
        name = "test_avg_tenure"

        def score(self, candidate, jd=None):
            jobs = candidate.get("career_history", [])
            avg = sum(j.get("duration_months", 0) for j in jobs) / max(1, len(jobs))
            return SignalResult(self.name, min(1.0, avg / 36), f"avg {avg:.0f}mo")

    assert "test_avg_tenure" in list_signals()
    rec = D.make_candidate(AI_SEARCH, D.STRONG, 4).record
    out = compute_signals(rec, only=["test_avg_tenure"])
    assert "test_avg_tenure" in out and out["test_avg_tenure"].evidence


def test_blended_score() -> None:
    rec = D.make_candidate(AI_SEARCH, D.STRONG, 5).record
    blended = blended_signal_score(compute_signals(rec))
    assert 0.0 <= blended <= 1.0


def test_bad_signal_does_not_break() -> None:
    @register_signal
    class _Broken(Signal):
        name = "test_broken"

        def score(self, candidate, jd=None):
            raise RuntimeError("boom")

    rec = D.make_candidate(AI_SEARCH, D.STRONG, 6).record
    out = compute_signals(rec, only=["test_broken"])
    assert out["test_broken"].score == 0.0  # error contained

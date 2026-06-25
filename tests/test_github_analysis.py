"""GitHub-repo analysis — surfaces real engineering evidence from a candidate's
OWN linked public profile. Tested OFFLINE (no network in CI): username extraction,
graceful no-fetch behavior, scoring math on injected data, and signal wiring.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.github_analysis import find_github_username, analyze_github, GithubProfile


def test_extracts_username_from_resume_text():
    c = {"profile": {"summary": "my work: github.com/octocat and more"}, "career_history": []}
    assert find_github_username(c) == "octocat"


def test_ignores_non_user_github_paths():
    c = {"profile": {"summary": "see github.com/features for details"}, "career_history": []}
    assert find_github_username(c) == ""


def test_no_github_is_graceful():
    c = {"profile": {"summary": "I write Python"}, "career_history": []}
    p = analyze_github(c)
    assert p.fetched is False
    assert "no GitHub profile" in p.evidence


def test_offline_fetch_failure_is_graceful(monkeypatch):
    # force the network call to fail -> must return a clear not-fetched result, not raise
    import talentsignal.github_analysis as g

    def boom(url, timeout):
        raise OSError("offline")
    monkeypatch.setattr(g, "_get", boom)
    p = analyze_github({"profile": {"summary": "github.com/someone"}, "career_history": []})
    assert p.fetched is False
    assert "not fetched" in p.evidence.lower()


def test_scoring_is_bounded_and_explainable(monkeypatch):
    import talentsignal.github_analysis as g

    def fake_get(url, timeout):
        if "/repos" in url:
            return [{"fork": False, "stargazers_count": 1200, "language": "Python"},
                    {"fork": False, "stargazers_count": 300, "language": "Go"},
                    {"fork": True, "stargazers_count": 9999, "language": "C"}]  # fork ignored
        return {"public_repos": 25, "followers": 150}
    monkeypatch.setattr(g, "_get", fake_get)
    p = analyze_github({"profile": {"summary": "github.com/dev"}, "career_history": []})
    assert p.fetched is True
    assert 0.0 <= p.score <= 1.0
    assert p.total_stars == 1500          # fork excluded
    assert "Python" in p.top_languages
    assert "stars" in p.evidence


def test_signal_registered_and_applies():
    from talentsignal.signals import compute_signals, list_signals
    assert "github_repo_analysis" in list_signals()
    # applies only when a github profile is present
    with_gh = compute_signals({"profile": {"summary": "github.com/dev"}, "career_history": [],
                               "skills": [], "redrob_signals": {}}, only=["github_repo_analysis"])
    without = compute_signals({"profile": {"summary": "no link"}, "career_history": [],
                              "skills": [], "redrob_signals": {}}, only=["github_repo_analysis"])
    # with a link the signal runs (may or may not fetch); without, applies_to() skips it
    assert "github_repo_analysis" not in without

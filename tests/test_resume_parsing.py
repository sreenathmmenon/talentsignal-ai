"""Resume parser robustness on messy real-world layouts. The local parser must
recover title, years, career, and skills from paragraph-style, split-date,
ALL-CAPS/pipe, and terse resumes -- not just clean 'Title at Company DATE' lines.
This is the production-quality gap we found by testing on realistic input.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from talentsignal.ingest import ingest
from fixtures.messy_resumes import ALL, EXPECTED


def _parse(name):
    return ingest(ALL[name], fmt="text")[0]


def test_all_messy_formats_parse():
    """Every messy fixture must recover title + years + skills (career where expected)."""
    failures = []
    for name, exp in EXPECTED.items():
        p = _parse(name)["profile"]
        c = _parse(name)
        yrs = p["years_of_experience"]
        ok = (bool(p["current_title"].strip())
              and exp["min_years"] <= yrs <= exp["max_years"]
              and len(c["career_history"]) >= exp["min_career"]
              and len(c["skills"]) >= exp["min_skills"])
        if not ok:
            failures.append((name, p["current_title"], yrs, len(c["career_history"]), len(c["skills"])))
    assert not failures, f"messy resumes failed to parse: {failures}"


def test_paragraph_resume_recovers_skills_via_gazetteer():
    # PARAGRAPH has no SKILLS section; gazetteer fallback must still find skills.
    c = _parse("PARAGRAPH")
    names = {s["name"].lower() for s in c["skills"]}
    assert "python" in names
    assert len(c["skills"]) >= 3


def test_split_date_layout_groups_jobs():
    # title / company / date on separate lines must group into jobs with tenure
    c = _parse("SPLIT_DATES")
    assert len(c["career_history"]) >= 2
    assert c["profile"]["years_of_experience"] > 0


def test_terse_resume_still_yields_a_role():
    # a 6-word resume must still produce a title + one synthesized role
    c = _parse("TERSE")
    assert c["profile"]["current_title"]
    assert len(c["career_history"]) >= 1


def test_keyword_stuffer_parses_but_career_is_marketing():
    # the stuffer parses fine; the SIGNAL is that career says marketing, not AI
    c = _parse("STUFFER")
    assert "marketing" in c["career_history"][0]["description"].lower() \
        or "marketing" in c["profile"]["current_title"].lower()

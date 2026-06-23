"""Free-text JD ingestion parses into a correct, weighted requirement model and
builds a working JobSpec for ANY role — the general-product front door.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal import jd_ingest as ji
from talentsignal.jd_parser import job_spec_from_jd_text, load_job_spec
from talentsignal.eval.jd_library import JDS


def test_ingest_classifies_sections() -> None:
    m = ji.ingest_text(JDS["ai_search"].text, "Senior AI Engineer")
    assert m.min_years == 5.0 and m.max_years == 9.0
    assert "Pune" in m.preferred_locations and "Noida" in m.preferred_locations
    assert len(m.by_kind(ji.MUST_HAVE)) >= 3
    assert len(m.by_kind(ji.DISQUALIFIER)) >= 3
    # disqualifiers capture the JD's actual traps
    dq = " ".join(r.text.lower() for r in m.by_kind(ji.DISQUALIFIER))
    assert "research" in dq and "services companies" in dq


def test_emphasis_boosts_must_have_weight() -> None:
    m = ji.ingest_text("You must have carried an enterprise quota and generated pipeline.")
    must = m.by_kind(ji.MUST_HAVE)
    assert must and any(r.weight > ji.KIND_WEIGHT[ji.MUST_HAVE] for r in must)


def test_no_years_or_location_leaks_into_requirements() -> None:
    for jd in JDS.values():
        m = ji.ingest_text(jd.text, jd.title)
        for r in m.requirements:
            # a bare "4-9 years ..." logistics line must not be a requirement
            assert not (r.text.strip()[:1].isdigit() and "years" in r.text.lower()
                        and len(r.text.split()) <= 12), r.text


def test_all_roles_ingest_with_requirements() -> None:
    for role_id, jd in JDS.items():
        m = ji.ingest_text(jd.text, jd.title)
        assert m.requirements, role_id
        assert m.min_years is not None, role_id


def test_job_spec_from_jd_text_builds_valid_spec() -> None:
    jd = JDS["sales"]
    spec = job_spec_from_jd_text(jd.text, job_id="sales_ingested", category="sales_gtm", title=jd.title)
    assert spec.must_have and spec.disqualifiers
    assert spec.preferred_min_years == 4.0 and spec.preferred_max_years == 9.0
    assert spec.strongest_min_years >= spec.preferred_min_years
    assert spec.strongest_max_years <= spec.preferred_max_years
    assert len(spec.requirements) >= 3
    # weights still validate (sum ~1.0)
    assert abs(sum(spec.weights.values()) - 1.0) < 0.05


def test_yaml_spec_now_carries_requirements() -> None:
    spec = load_job_spec("job_specs/redrob_senior_ai_engineer.yaml")
    assert len(spec.requirements) >= 5
    kinds = {r.kind for r in spec.requirements}
    assert ji.MUST_HAVE in kinds and ji.DISQUALIFIER in kinds


def test_title_line_not_a_requirement():
    # the JD title/intro line must NOT become a scored requirement (it gave weak
    # candidates spurious credit for sharing the role word)
    m = ji.ingest_text("Senior AI Engineer at GitLab. Remote, US.\n"
                       "Required: confident coding in Python; deep experience with modern AI.")
    texts = [r.text.lower() for r in m.requirements]
    assert not any("gitlab" in t for t in texts), texts
    assert any("python" in t or "modern ai" in t for t in texts)

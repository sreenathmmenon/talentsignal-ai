from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .category_taxonomy import get_category_profile, validate_weights


@dataclass(frozen=True)
class JobSpec:
    id: str
    title: str
    category: str
    preferred_min_years: float
    preferred_max_years: float
    strongest_min_years: float
    strongest_max_years: float
    preferred_locations: tuple[str, ...]
    country_preferred: str
    must_have: tuple[str, ...]
    nice_to_have: tuple[str, ...]
    disqualifiers: tuple[str, ...]
    weights: dict[str, float]
    category_label: str
    category_core_signals: tuple[str, ...]
    category_evidence_priorities: tuple[str, ...]
    category_common_risks: tuple[str, ...]
    # Structured requirement model (from free-text ingestion or derived from the
    # YAML must/nice/disqualifier lists). Additive; defaults to empty so existing
    # construction paths and consumers are unaffected.
    requirements: tuple = ()


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_simple_yaml(path: str | Path) -> dict[str, Any]:
    """Parse the small YAML subset used by job_specs without external deps."""
    return _parse_yaml_with_lists(Path(path).read_text(encoding="utf-8").splitlines())


def _parse_yaml_with_lists(lines: list[str]) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any, str | None]] = [(-1, root, None)]
    for i, raw in enumerate(lines):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        text = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if text.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"Unexpected list item: {raw}")
            parent.append(_parse_scalar(text[2:]))
            continue
        key, _, value = text.partition(":")
        key = key.strip()
        value = value.strip()
        if value:
            parent[key] = _parse_scalar(value)
            continue
        next_is_list = False
        for nxt in lines[i + 1 :]:
            if not nxt.strip() or nxt.lstrip().startswith("#"):
                continue
            next_indent = len(nxt) - len(nxt.lstrip(" "))
            next_is_list = next_indent > indent and nxt.strip().startswith("- ")
            break
        container: Any = [] if next_is_list else {}
        parent[key] = container
        stack.append((indent, container, key))
    return root


def load_job_spec(path: str | Path) -> JobSpec:
    data = load_simple_yaml(path)
    exp = data["experience"]
    loc = data["locations"]
    category = str(data["category"])
    category_profile = get_category_profile(category)
    weights = {k: float(v) for k, v in data.get("weights", category_profile.default_weights).items()}
    validate_weights(weights)
    return JobSpec(
        id=str(data["id"]),
        title=str(data["title"]),
        category=category,
        preferred_min_years=float(exp["preferred_min_years"]),
        preferred_max_years=float(exp["preferred_max_years"]),
        strongest_min_years=float(exp["strongest_min_years"]),
        strongest_max_years=float(exp["strongest_max_years"]),
        preferred_locations=tuple(loc["preferred"]),
        country_preferred=str(loc["country_preferred"]),
        must_have=tuple(data["must_have"]),
        nice_to_have=tuple(data["nice_to_have"]),
        disqualifiers=tuple(data["disqualifiers"]),
        weights=weights,
        category_label=category_profile.label,
        category_core_signals=category_profile.core_signals,
        category_evidence_priorities=category_profile.evidence_priorities,
        category_common_risks=category_profile.common_risks,
        requirements=_requirements_from_lists(
            tuple(data["must_have"]), tuple(data["nice_to_have"]), tuple(data["disqualifiers"])
        ),
    )


def _requirements_from_lists(must, nice, disq) -> tuple:
    """Build a structured requirement model from the YAML scorecard lists so a
    hand-written spec and an ingested free-text JD expose the SAME requirements."""
    from .jd_ingest import Requirement, _keywords, MUST_HAVE, NICE_TO_HAVE, DISQUALIFIER, KIND_WEIGHT

    reqs = []
    for kind, items in ((MUST_HAVE, must), (NICE_TO_HAVE, nice), (DISQUALIFIER, disq)):
        for text in items:
            reqs.append(Requirement(text=str(text), kind=kind, weight=KIND_WEIGHT[kind],
                                    keywords=_keywords(str(text))))
    return tuple(reqs)


def job_spec_from_jd_text(
    text: str,
    *,
    job_id: str = "ingested_jd",
    category: str = "ai_ml_search_ranking",
    country_preferred: str = "India",
    title: str = "",
) -> JobSpec:
    """Build a JobSpec directly from a free-text job description.

    This is the general-product front door: any JD becomes a scorable spec with
    no YAML authoring. Uses jd_ingest for the requirement model, falls back to
    the category taxonomy for weights/seniority defaults where the text is silent.
    """
    from .jd_ingest import ingest_text, must_have_phrases, disqualifier_phrases, NICE_TO_HAVE

    model = ingest_text(text, title=title)
    category_profile = get_category_profile(category)
    weights = dict(category_profile.default_weights)

    pmin = model.min_years if model.min_years is not None else 5.0
    pmax = model.max_years if model.max_years is not None else 9.0
    # "strongest" band = the inner ~60% of the preferred band.
    span = max(0.0, pmax - pmin)
    smin = round(pmin + span * 0.2, 1)
    smax = round(pmax - span * 0.2, 1)

    nice = tuple(r.text for r in model.requirements if r.kind == NICE_TO_HAVE)
    return JobSpec(
        id=job_id,
        title=model.title or title or "Ingested Role",
        category=category,
        preferred_min_years=float(pmin),
        preferred_max_years=float(pmax),
        strongest_min_years=float(smin),
        strongest_max_years=float(smax),
        preferred_locations=model.preferred_locations or category_profile_locations(category),
        country_preferred=country_preferred,
        must_have=must_have_phrases(model),
        nice_to_have=nice,
        disqualifiers=disqualifier_phrases(model),
        weights=weights,
        category_label=category_profile.label,
        category_core_signals=category_profile.core_signals,
        category_evidence_priorities=category_profile.evidence_priorities,
        category_common_risks=category_profile.common_risks,
        requirements=tuple(model.requirements),
    )


def category_profile_locations(category: str) -> tuple[str, ...]:
    """Sensible default preferred locations when a JD names none."""
    return ("Bangalore", "Pune", "Hyderabad", "Mumbai", "Delhi", "Noida", "Gurgaon")

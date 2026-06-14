#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.features import build_evidence
from talentsignal.io import iter_candidates
from talentsignal.risk_audit import risk_flags


def classify(ev) -> list[str]:
    labels: list[str] = []
    if ev.ai_title and ev.career_retrieval_terms and ev.career_production_terms:
        labels.append("strong_ai_search_ranking_engineer")
    if ev.adjacent_title and ev.career_retrieval_terms:
        labels.append("adjacent_backend_data_engineer")
    if ev.ai_title and ev.career_production_terms and not ev.career_retrieval_terms:
        labels.append("product_ml_generalist")
    if "research" in ev.title_norm and not ev.career_production_terms:
        labels.append("pure_research_candidate")
    if "non_tech_ai_keyword_stuffing" in risk_flags(ev) or "ai_terms_without_career_evidence" in risk_flags(ev):
        labels.append("ai_keyword_stuffer")
    if ev.last_active_months >= 6 and ev.response_rate < 0.2:
        labels.append("stale_strong_or_stale_profile")
    if ev.service_only:
        labels.append("service_only_candidate")
    return labels


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", default="outputs/archetype_samples.json")
    parser.add_argument("--limit-per-archetype", type=int, default=8)
    args = parser.parse_args()

    samples: dict[str, list[dict]] = defaultdict(list)
    for candidate in iter_candidates(args.candidates):
        ev = build_evidence(candidate)
        for label in classify(ev):
            if len(samples[label]) < args.limit_per_archetype:
                samples[label].append(
                    {
                        "candidate_id": ev.candidate_id,
                        "title": ev.title,
                        "years": ev.years,
                        "location": ev.location,
                        "career_retrieval_terms": ev.career_retrieval_terms,
                        "career_production_terms": ev.career_production_terms,
                        "risk_flags": risk_flags(ev),
                    }
                )
        if samples and all(len(v) >= args.limit_per_archetype for v in samples.values()) and len(samples) >= 7:
            break
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(samples, indent=2), encoding="utf-8")
    print(f"Wrote {sum(len(v) for v in samples.values())} samples across {len(samples)} archetypes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


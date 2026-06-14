#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.io import iter_candidates


def pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    return values[min(len(values) - 1, int(len(values) * p))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out-json", default="outputs/dataset_profile.json")
    parser.add_argument("--out-md", default="outputs/dataset_profile.md")
    args = parser.parse_args()

    titles: Counter[str] = Counter()
    countries: Counter[str] = Counter()
    locations: Counter[str] = Counter()
    industries: Counter[str] = Counter()
    companies: Counter[str] = Counter()
    skills: Counter[str] = Counter()
    signals: dict[str, list[float]] = defaultdict(list)
    count = 0
    for candidate in iter_candidates(args.candidates):
        count += 1
        profile = candidate["profile"]
        titles[profile["current_title"]] += 1
        countries[profile["country"]] += 1
        locations[profile["location"]] += 1
        industries[profile["current_industry"]] += 1
        for job in candidate.get("career_history", []):
            companies[job.get("company", "")] += 1
        for skill in candidate.get("skills", []):
            skills[skill.get("name", "")] += 1
        redrob = candidate["redrob_signals"]
        for key in [
            "profile_completeness_score",
            "recruiter_response_rate",
            "avg_response_time_hours",
            "notice_period_days",
            "github_activity_score",
            "search_appearance_30d",
            "saved_by_recruiters_30d",
            "interview_completion_rate",
            "offer_acceptance_rate",
        ]:
            signals[key].append(float(redrob.get(key) or 0.0))

    profile = {
        "count": count,
        "top_titles": titles.most_common(30),
        "top_countries": countries.most_common(20),
        "top_locations": locations.most_common(30),
        "top_industries": industries.most_common(30),
        "top_companies": companies.most_common(30),
        "top_skills": skills.most_common(50),
        "signals": {
            key: {"p10": pct(vals, 0.10), "p50": pct(vals, 0.50), "p90": pct(vals, 0.90), "min": min(vals), "max": max(vals)}
            for key, vals in signals.items()
        },
    }
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(profile, indent=2), encoding="utf-8")
    lines = ["# Dataset Profile", "", f"Total candidates: {count}", ""]
    for name, values in [
        ("Top Titles", profile["top_titles"]),
        ("Top Countries", profile["top_countries"]),
        ("Top Locations", profile["top_locations"]),
        ("Top Industries", profile["top_industries"]),
        ("Top Companies", profile["top_companies"]),
        ("Top Skills", profile["top_skills"][:25]),
    ]:
        lines.append(f"## {name}")
        lines.extend(f"- {k}: {v}" for k, v in values)
        lines.append("")
    lines.append("## Signal Percentiles")
    for key, stats in profile["signals"].items():
        lines.append(f"- {key}: p10={stats['p10']}, p50={stats['p50']}, p90={stats['p90']}, min={stats['min']}, max={stats['max']}")
    Path(args.out_md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Profiled {count} candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


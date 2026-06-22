#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.jd_parser import load_job_spec
from talentsignal.ranking import rank_candidates


def _packet(row: dict[str, Any]) -> dict[str, Any]:
    ev = row["_evidence"]
    score = row["_score"]
    return {
        "candidate_id": row["candidate_id"],
        "rank": row["rank"],
        "score": row["score"],
        "title": ev.title,
        "years": ev.years,
        "location": ev.location,
        "country": ev.country,
        "confidence": score.confidence,
        "top10_eligible": score.top10_eligible,
        "risk_flags": score.risk_flags,
        "reasoning": row["reasoning"],
    }


def evaluate_job(candidates: str, spec_path: Path, top_n: int) -> dict[str, Any]:
    start = time.perf_counter()
    job = load_job_spec(spec_path)
    rows = rank_candidates(candidates, job, top_n=top_n)
    elapsed = time.perf_counter() - start
    top = [_packet(row) for row in rows]
    title_counts = Counter(packet["title"] for packet in top)
    country_counts = Counter(packet["country"] for packet in top)
    flagged = sum(1 for packet in top if packet["risk_flags"])
    eligible_top10 = sum(1 for packet in top[:10] if packet["top10_eligible"])
    return {
        "job_spec": str(spec_path),
        "job_id": job.id,
        "title": job.title,
        "category": job.category,
        "category_label": job.category_label,
        "elapsed_seconds": round(elapsed, 3),
        "top_n": top_n,
        "eligible_top10": eligible_top10,
        "risk_flagged_top_n": flagged,
        "top_titles": title_counts.most_common(8),
        "top_countries": country_counts.most_common(8),
        "top_candidates": top[:10],
    }


def write_markdown(report: dict[str, Any], out_path: Path) -> None:
    lines = [
        "# Multi-JD Candidate Review",
        "",
        f"Candidates: `{report['candidates']}`",
        f"Job specs evaluated: {len(report['jobs'])}",
        f"Top N per job: {report['top_n']}",
        "",
        "## Cross-Job Overlap",
        "",
    ]
    for item in report["overlap"]:
        lines.append(f"- `{item['left']}` vs `{item['right']}`: {item['overlap_count']} overlapping top candidates")
    lines.append("")
    for job in report["jobs"]:
        top_titles = ", ".join(f"{title} ({count})" for title, count in job["top_titles"])
        top_countries = ", ".join(f"{country or 'Unknown'} ({count})" for country, count in job["top_countries"])
        lines.extend(
            [
                f"## {job['title']}",
                "",
                f"- Job ID: `{job['job_id']}`",
                f"- Category: {job['category_label']} (`{job['category']}`)",
                f"- Runtime: {job['elapsed_seconds']}s",
                f"- Top-10 eligible: {job['eligible_top10']}/10",
                f"- Risk-flagged in top {job['top_n']}: {job['risk_flagged_top_n']}",
                f"- Top titles: {top_titles}",
                f"- Top countries: {top_countries}",
                "",
                "| Rank | Candidate | Score | Title | Location | Confidence | Risk | Reasoning |",
                "|---:|---|---:|---|---|---:|---|---|",
            ]
        )
        for cand in job["top_candidates"]:
            risk = ", ".join(cand["risk_flags"]) if cand["risk_flags"] else "clear"
            lines.append(
                f"| {cand['rank']} | `{cand['candidate_id']}` | {cand['score']} | "
                f"{cand['title']} | {cand['location']} | {cand['confidence']:.3f} | {risk} | {cand['reasoning']} |"
            )
        lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def build_overlap(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    overlap: list[dict[str, Any]] = []
    top_sets = {
        job["job_id"]: {candidate["candidate_id"] for candidate in job["top_candidates"]}
        for job in jobs
    }
    ids = list(top_sets)
    for i, left in enumerate(ids):
        for right in ids[i + 1 :]:
            overlap.append(
                {
                    "left": left,
                    "right": right,
                    "overlap_count": len(top_sets[left].intersection(top_sets[right])),
                }
            )
    return overlap


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate multiple job scorecards against the same candidate pool.")
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--job-spec", action="append", dest="job_specs", default=[])
    parser.add_argument("--job-spec-dir", action="append", dest="job_spec_dirs", default=[])
    parser.add_argument("--top-n", type=int, default=25)
    parser.add_argument("--out-json", default="outputs/multi_jd_candidate_review.json")
    parser.add_argument("--out-md", default="outputs/multi_jd_candidate_review.md")
    args = parser.parse_args()

    spec_paths = [Path(path) for path in args.job_specs]
    for directory in args.job_spec_dirs:
        spec_paths.extend(sorted(Path(directory).glob("*.yaml")))
    if not spec_paths:
        raise SystemExit("No job specs provided")

    jobs = [evaluate_job(args.candidates, path, args.top_n) for path in spec_paths]
    report = {
        "candidates": args.candidates,
        "top_n": args.top_n,
        "jobs": jobs,
        "overlap": build_overlap(jobs),
    }
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, Path(args.out_md))
    print(f"Wrote {args.out_json} and {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

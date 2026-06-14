#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_packets(path: str) -> list[dict]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def section(packet: dict) -> str:
    evidence = packet["evidence"]
    score = packet["score_breakdown"]
    return f"""## Rank {packet['rank']}: {packet['candidate_id']}

- Title: {evidence['title']}
- Experience: {evidence['years']} years
- Location: {evidence['location']}
- Score: {packet['score']}
- Confidence: {score['confidence']}
- Top-10 eligible: {score['top10_eligible']}
- Career retrieval/ranking evidence: {', '.join(evidence.get('career_retrieval_terms', [])) or 'None'}
- Career production evidence: {', '.join(evidence.get('career_production_terms', [])) or 'None'}
- Vector/search evidence: {', '.join(evidence.get('vector_terms', [])) or 'None'}
- Evaluation evidence: {', '.join(evidence.get('eval_terms', [])) or 'None'}
- Risk flags: {', '.join(score.get('risk_flags', [])) or 'None'}

Reasoning:

> {packet['reasoning']}

Defense:

This candidate is placed here because the scorecard found direct career evidence matching the Redrob JD, with factor scores that support the rank. The evidence terms above are the facts to use in an interview defense.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-packets", default="outputs/evidence_packets.jsonl")
    parser.add_argument("--out", default="docs/candidate_case_studies.md")
    args = parser.parse_args()
    packets = load_packets(args.evidence_packets)
    by_rank = {packet["rank"]: packet for packet in packets}
    selected_ranks = [1, 5, 10, 50, 100]
    selected = [by_rank[rank] for rank in selected_ranks if rank in by_rank]
    # Add the highest ranked candidate with a risk flag if one exists.
    risky = next((packet for packet in packets if packet["score_breakdown"].get("risk_flags")), None)
    lines = [
        "# Candidate Case Studies",
        "",
        "These examples are generated from the current evidence packets and should be used for interview defense.",
        "",
    ]
    for packet in selected:
        lines.append(section(packet))
    if risky:
        lines.append("# Down-Ranked Risk Example")
        lines.append(section(risky))
    else:
        lines.append("# Down-Ranked Risk Example")
        lines.append("")
        lines.append("No risk-flagged candidate appears in the current top 100. Use `outputs/archetype_samples.json` for examples of keyword-stuffer and stale-profile patterns found in the broader dataset.")
        lines.append("")
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


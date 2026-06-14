#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_packets(path: str) -> dict[str, dict]:
    packets = {}
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                packet = json.loads(line)
                packets[packet["candidate_id"]] = packet
    return packets


def summarize(packet: dict) -> str:
    score = packet["score_breakdown"]
    evidence = packet["evidence"]
    lines = [
        f"{packet['candidate_id']} rank={packet['rank']} score={packet['score']}",
        f"title={evidence['title']} years={evidence['years']} location={evidence['location']}",
        f"technical={score['technical_evidence']} career={score['career_fit']} behavioral={score['behavioral']} trust={score['trust']}",
        f"confidence={score['confidence']} top10_eligible={score['top10_eligible']} penalty={score['penalty']}",
        f"career_retrieval={', '.join(evidence['career_retrieval_terms']) or 'none'}",
        f"career_production={', '.join(evidence['career_production_terms']) or 'none'}",
        f"vector={', '.join(evidence['vector_terms']) or 'none'}",
        f"eval={', '.join(evidence['eval_terms']) or 'none'}",
        f"risk_flags={', '.join(score['risk_flags']) or 'none'}",
        f"reasoning={packet['reasoning']}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_a")
    parser.add_argument("candidate_b")
    parser.add_argument("--evidence-packets", default="outputs/evidence_packets.jsonl")
    args = parser.parse_args()
    packets = load_packets(args.evidence_packets)
    missing = [cid for cid in [args.candidate_a, args.candidate_b] if cid not in packets]
    if missing:
        raise SystemExit(f"Candidate(s) not found in evidence packets: {', '.join(missing)}")
    print("=== Candidate A ===")
    print(summarize(packets[args.candidate_a]))
    print("\n=== Candidate B ===")
    print(summarize(packets[args.candidate_b]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


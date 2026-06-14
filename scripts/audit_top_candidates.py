#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def decision(packet: dict) -> tuple[str, str]:
    score = packet["score_breakdown"]
    evidence = packet["evidence"]
    rank = packet["rank"]
    flags = score["risk_flags"]
    concerns: list[str] = []
    if rank <= 10 and not score["top10_eligible"]:
        concerns.append("top-10 ineligible")
    if not evidence["career_retrieval_terms"]:
        concerns.append("no career retrieval/ranking evidence")
    if not evidence["career_production_terms"]:
        concerns.append("limited career production evidence")
    if flags:
        concerns.append("risk flags: " + "|".join(flags))
    if rank <= 10 and concerns:
        return "investigate", "; ".join(concerns)
    if rank <= 25 and flags:
        return "investigate", "; ".join(concerns)
    return "keep", "; ".join(concerns) if concerns else "passes automated audit checks"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-packets", default="outputs/evidence_packets.jsonl")
    parser.add_argument("--out-csv", default="outputs/top25_audit.csv")
    parser.add_argument("--out-md", default="outputs/top25_audit.md")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()

    packets = []
    with Path(args.evidence_packets).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                packet = json.loads(line)
                if packet["rank"] <= args.limit:
                    packets.append(packet)
    rows = []
    for packet in packets:
        score = packet["score_breakdown"]
        evidence = packet["evidence"]
        audit_decision, notes = decision(packet)
        rows.append(
            {
                "rank": packet["rank"],
                "candidate_id": packet["candidate_id"],
                "score": packet["score"],
                "title": evidence["title"],
                "years": evidence["years"],
                "location": evidence["location"],
                "top10_eligible": score["top10_eligible"],
                "confidence": score["confidence"],
                "risk_flags": "|".join(score["risk_flags"]),
                "career_retrieval_terms": "|".join(evidence["career_retrieval_terms"]),
                "career_production_terms": "|".join(evidence["career_production_terms"]),
                "audit_decision": audit_decision,
                "audit_notes": notes,
            }
        )
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.out_csv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    md = ["# Top-25 Audit", "", f"Evidence source: `{args.evidence_packets}`", ""]
    for row in rows:
        md.append(
            f"- Rank {row['rank']} {row['candidate_id']} ({row['title']}, {row['years']} yrs, {row['location']}): "
            f"{row['audit_decision']} - {row['audit_notes']}"
        )
    Path(args.out_md).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} audit rows to {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


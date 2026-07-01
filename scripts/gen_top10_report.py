#!/usr/bin/env python3
"""Generate TOP10_REPORT.md from the CURRENT submission + evidence packets, so the
showcase can never drift from the committed CSV (a Stage-4 credibility risk if the
report's #1 disagrees with the submission's #1). Run after every rank.

  python3 scripts/gen_top10_report.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "outputs" / "final_submission.csv"
PACKETS = ROOT / "outputs" / "evidence_packets.jsonl"
OUT = ROOT / "TOP10_REPORT.md"


def main() -> int:
    rows = list(csv.DictReader(SUBMISSION.open()))
    packets = {}
    if PACKETS.exists():
        for line in PACKETS.open():
            if line.strip():
                p = json.loads(line)
                packets[p["candidate_id"]] = p

    lines = [
        "# TalentSignal — Top 10 of 100,000 (real Redrob dataset)",
        "",
        "JD: **Senior AI Engineer** (embeddings · retrieval · ranking · NDCG · Python · 5–9 yrs)  ",
        "Pool: **100,000 real candidates** · CPU-only · no network · reproduces offline in budget  ",
        "Engine: **hybrid** (the submitted engine). This report is generated directly from "
        "`outputs/final_submission.csv` + `outputs/evidence_packets.jsonl`, so it always "
        "matches the submission.",
        "",
        "---",
        "",
    ]
    for r in rows[:10]:
        cid = r["candidate_id"]
        p = packets.get(cid, {})
        sb = p.get("score_breakdown", {})
        ev = p.get("evidence", {})
        fac = " · ".join(
            f"`{k}={float(sb.get(k, 0.0)):.2f}`"
            for k in ("technical_evidence", "career_fit", "seniority", "logistics",
                      "behavioral", "trust", "semantic_fit", "requirement_coverage")
            if k in sb
        )
        flags = sb.get("risk_flags") or []
        flag_line = "none (consistency auditor: clean)" if not flags else "; ".join(flags)
        lines += [
            f"## #{r['rank']} — {cid}  ·  score **{r['score']}**",
            f"- **Title read:** {ev.get('title', '') or '—'}  ·  **Years read:** {ev.get('years', '')}",
            f"- **Location:** {ev.get('location', '') or '—'}",
            f"- **Factor breakdown:** {fac}" if fac else "- **Factor breakdown:** (n/a)",
            f"- **Risk flags:** {flag_line}",
            f"- **Reasoning (grounded, rank-aware):** {r['reasoning']}",
            "",
        ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} — top-1 = {rows[0]['candidate_id']} (matches submission)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

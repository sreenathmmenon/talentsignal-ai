#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def render_packet(packet: dict) -> str:
    evidence = packet["evidence"]
    score = packet["score_breakdown"]
    risk = ", ".join(score.get("risk_flags", [])) or "None"
    factors = [
        ("Technical", score["technical_evidence"]),
        ("Career", score["career_fit"]),
        ("Seniority", score["seniority"]),
        ("Logistics", score["logistics"]),
        ("Behavioral", score["behavioral"]),
        ("Trust", score["trust"]),
        ("Confidence", score["confidence"]),
    ]
    bars = "\n".join(
        f"<div class='factor'><span>{name}</span><meter min='0' max='1' value='{value}'></meter><b>{value:.3f}</b></div>"
        for name, value in factors
    )
    return f"""
    <article class='candidate'>
      <header>
        <div><strong>#{packet['rank']} {html.escape(packet['candidate_id'])}</strong></div>
        <div>{html.escape(evidence['title'])} · {evidence['years']} yrs · {html.escape(evidence['location'])}</div>
        <div class='score'>Score {html.escape(packet['score'])} · Top-10 eligible: {score['top10_eligible']}</div>
      </header>
      <p>{html.escape(packet['reasoning'])}</p>
      <section class='grid'>
        <div><h4>Score Factors</h4>{bars}</div>
        <div><h4>Evidence</h4>
          <p><b>Career retrieval:</b> {html.escape(', '.join(evidence.get('career_retrieval_terms', [])) or 'None')}</p>
          <p><b>Production:</b> {html.escape(', '.join(evidence.get('career_production_terms', [])) or 'None')}</p>
          <p><b>Vector/search:</b> {html.escape(', '.join(evidence.get('vector_terms', [])) or 'None')}</p>
          <p><b>Evaluation:</b> {html.escape(', '.join(evidence.get('eval_terms', [])) or 'None')}</p>
          <p><b>Risk flags:</b> {html.escape(risk)}</p>
        </div>
      </section>
    </article>
    """


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a static recruiter cockpit demo.")
    parser.add_argument("--evidence-packets", default="outputs/evidence_packets.jsonl")
    parser.add_argument("--submission", default="outputs/final_submission.csv")
    parser.add_argument("--out", default="demo/recruiter_cockpit.html")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()
    packets = []
    with Path(args.evidence_packets).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                packets.append(json.loads(line))
    packets = packets[: args.limit]
    body = "\n".join(render_packet(packet) for packet in packets)
    doc = f"""<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>TalentSignal Recruiter Cockpit</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; color: #172026; background: #f6f7f9; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    h1 {{ margin-bottom: 4px; }}
    .subtitle {{ color: #58636f; margin-top: 0; }}
    .candidate {{ background: white; border: 1px solid #dfe4ea; border-radius: 8px; padding: 18px; margin: 14px 0; box-shadow: 0 1px 2px rgba(0,0,0,.04); }}
    .candidate header {{ display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; }}
    .score {{ color: #345; font-weight: 600; }}
    .grid {{ display: grid; grid-template-columns: minmax(260px, 1fr) minmax(320px, 1.2fr); gap: 18px; }}
    .factor {{ display: grid; grid-template-columns: 90px 1fr 56px; gap: 10px; align-items: center; margin: 6px 0; }}
    meter {{ width: 100%; }}
    code {{ background: #eef1f4; padding: 2px 5px; border-radius: 4px; }}
    @media (max-width: 760px) {{ main {{ padding: 16px; }} .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
<main>
  <h1>TalentSignal Recruiter Cockpit</h1>
  <p class='subtitle'>Static demo generated from <code>{html.escape(args.evidence_packets)}</code>. Downloadable challenge CSV: <code>{html.escape(args.submission)}</code>.</p>
  {body}
</main>
</body>
</html>
"""
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(doc, encoding="utf-8")
    print(f"Wrote {args.out} with {len(packets)} candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


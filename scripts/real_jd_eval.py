#!/usr/bin/env python3
"""Real-JD evaluation — validate the engine on REAL job descriptions.

Runs each real JD (eval/real_jds.py) against a diverse candidate population that
spans the realistic spectrum recruiters actually see — best fits, under-market
(overqualified), undersell (great person, terse resume), adjacent, weak, and
keyword-stuffers — across Indian and international locations. Reports where each
archetype lands, so we can see the engine's judgment on real roles, not just
synthetic benchmarks.

This is the "proven on real data" credibility artifact. Writes a markdown report.

Usage:
  python scripts/real_jd_eval.py            # uses lexical-only (no model needed)
  python scripts/real_jd_eval.py --hybrid   # live-embed for the hybrid engine
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from eval.real_jds import REAL_JDS
from talentsignal.ingest import ingest
from talentsignal.api import rank

# A diverse candidate population (synthetic, no PII) covering the realistic
# spectrum × India + international. Each is a free-text resume the ingest layer
# parses, so this also exercises the real resume parser.
CANDIDATES = {
    "best_intl": "Maria Schmidt. Berlin, Germany. Senior AI Engineer, 7 years. Shipped production LLM agents with prompt engineering, tool-calling and multi-LLM orchestration across OpenAI and Anthropic. Built guardrails and evaluation. Python and TypeScript, GraphQL. Owned initiatives end to end, mentored engineers. Skills: Python, TypeScript, LLMs, Prompt Engineering, AI Agents, GraphQL, Anthropic, OpenAI, Guardrails",
    "best_india": "Arjun Nair. Bangalore, India. Staff AI Engineer, 8 years. Built a production AI agent platform, RAG systems, MCP integrations and multi-LLM routing. Python and TypeScript, REST and GraphQL. Shipped LLM products to real users and led a team. Skills: Python, TypeScript, AI Agents, RAG, MCP, LLMs, GraphQL, Guardrails",
    "recsys_india": "Divya Rao. Hyderabad, India. Machine Learning Engineer, 5 years. Built recommendation and ranking models for a product discovery feed; ran A/B tests with experiment tracking and model registry; tuned models for production. Python, TensorFlow, PyTorch. Skills: Python, Machine Learning, Recommendation, Ranking, TensorFlow, PyTorch, A/B Testing, NLP",
    "staff_platform_india": "Karthik Iyer. Bangalore, India. Staff Software Engineer, 12 years. Built distributed systems and high-throughput GraphQL and REST APIs; owned reliability and on-call; led system design and mentored engineers. Skills: Python, Go, GraphQL, REST, Kubernetes, PostgreSQL, Distributed Systems, System Design",
    "under_market_14y": "Ravi Menon. Bengaluru, India. Staff Software Engineer, 14 years. Built a multi-LLM conversational platform, RAG assistants and MCP servers. Creator of an open-source LLM SDK with 40K downloads. AI agents, embeddings, GraphQL platforms, distributed systems. Hackathon prize winner. Skills: Python, TypeScript, LLMs, RAG, AI Agents, MCP, GraphQL, Kubernetes",
    "undersell_terse": "Sana Iyer. Pune. AI engineer, 6 years. Did LLM agents and chatbots in production. Python.",
    "adjacent_backend": "Tom Becker. London, UK. Backend Engineer, 6 years. Java and Python microservices and REST APIs. Recently added an LLM feature using OpenAI for a support tool. Skills: Java, Python, REST, OpenAI, Docker",
    "weak_frontend": "Priya Das. Chennai, India. Frontend Developer, 5 years. React and CSS. Curious about AI, did an online course. Skills: React, JavaScript, CSS, HTML",
    "keyword_stuffer": "Vikram Reddy. Hyderabad, India. Marketing Manager, 9 years. Ran marketing campaigns and email funnels; tracked engagement in spreadsheets. Skills: Python, LLMs, AI Agents, Prompt Engineering, GraphQL, RAG, MCP, Guardrails, Kubernetes, Embeddings",
}


def _embedder():
    import os
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    return lambda t: m.encode(t, convert_to_numpy=True, normalize_embeddings=True)


def run(hybrid: bool) -> str:
    embedder = _embedder() if hybrid else None
    recs = []
    id2label = {}
    for label, text in CANDIDATES.items():
        r = ingest(text, fmt="text")[0]
        id2label[r["candidate_id"]] = label
        recs.append(r)

    lines = ["# Real-JD Evaluation Report", "",
             f"Engine: **{'hybrid' if hybrid else 'spine'}** · {len(CANDIDATES)} diverse candidates "
             "(India + international; best / under-market / undersell / adjacent / weak / keyword-stuffer)",
             ""]
    for key, jd in REAL_JDS.items():
        res = rank(jd["text"], recs, top_n=len(recs),
                   engine="hybrid" if hybrid else "spine",
                   embedder=embedder, category=jd["category"])
        lines += [f"## {jd['title']}", f"_source: {jd['source']}_", "",
                  "| rank | candidate | score | tech | career | senior |",
                  "|---|---|---|---|---|---|"]
        for c in res.ranked:
            f = c.factors
            lines.append(f"| {c.rank} | {id2label[c.candidate_id]} | {c.score:.3f} | "
                         f"{f.technical_evidence:.2f} | {f.career_fit:.2f} | {f.seniority:.2f} |")
        # quick sanity flags
        order = [id2label[c.candidate_id] for c in res.ranked]
        stuffer_pos = order.index("keyword_stuffer") + 1
        lines += ["", f"- keyword-stuffer landed at rank **{stuffer_pos}** (lower is better; should be bottom half)", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hybrid", action="store_true")
    ap.add_argument("--out", default="outputs/eval/real_jd_report.md")
    args = ap.parse_args()
    report = run(args.hybrid)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

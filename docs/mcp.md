# TalentSignal MCP Server

Expose the candidate-intelligence engine as tools any agentic system can call —
so an AI agent can rank candidates, parse resumes, structure JDs, and audit
profiles as part of a larger workflow.

## Tools (9)

| Tool | What it does |
|---|---|
| `rank_candidates` | Rank candidates (records or résumé text) against a JD → ranked, explainable shortlist |
| `compare_candidates` | Explain why one ranked candidate beats another — factor-by-factor scorecard |
| `build_interview_kit` | Evidence-grounded interview questions + hire/no-hire rubric for a candidate |
| `candidate_report` | Candidate-facing transparency report (what matched, with proof; what to improve) |
| `compliance` | EEOC four-fifths adverse-impact check on a ranking (your own group labels) |
| `audit_candidate` | Role-independent consistency / honeypot auditor (catches fabricated profiles) |
| `ingest_jd` | Parse a JD into a structured weighted requirement model |
| `screen_resume` | Parse one résumé (text) into a structured candidate profile |
| `explain_ranking` | Rank, then return grounded reasoning for the top picks |

## Prompts (one-click hiring workflows)

Prompts chain the tools in a proven sequence, so a non-expert user gets an outcome,
not a tool list. Invoke via `prompts/list` → `prompts/get`.

| Prompt | Outcome |
|---|---|
| `shortlist_for_role` | Screen résumés against a role → ranked, explained shortlist (surfaces meaning-rescued fits) |
| `fair_hiring_review` | Shortlist **plus** an adverse-impact compliance check — the review HR/legal needs |
| `prep_interview` | Rank, then produce an interview kit for the top pick |
| `explain_to_candidate` | A humane, transparent "why" report for a candidate |

## Run

```bash
python mcp_server.py     # stdio JSON-RPC MCP server
```

No third-party dependency — the server is a hand-rolled MCP (stdio) implementation
that wraps the same `talentsignal.api` facade as the CLI, REST API, and UI.

## Register with an MCP client (e.g. Claude Desktop)

Add to the client's MCP config:

```json
{
  "mcpServers": {
    "talentsignal": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_server.py"]
    }
  }
}
```

Then an agent can call, e.g.:

> "Use talentsignal to rank these three resumes against this job description and
> explain why the top pick won."

## Why it matters

The engine becomes infrastructure other AI systems plug into — not a closed app.
This is the agentic, integratable surface of the product (alongside the REST API
and the UI), all over one engine.

# TalentSignal MCP Server

Expose the candidate-intelligence engine as tools any agentic system can call —
so an AI agent can rank candidates, parse resumes, structure JDs, and audit
profiles as part of a larger workflow.

## Tools

| Tool | What it does |
|---|---|
| `rank_candidates` | Rank candidates (records or resume text) against a JD → ranked, explainable shortlist |
| `ingest_jd` | Parse a JD into a structured weighted requirement model |
| `screen_resume` | Parse one resume (text) into a structured candidate profile |
| `audit_candidate` | Run the consistency / honeypot auditor on a candidate |
| `explain_ranking` | Rank, then return grounded reasoning for the top picks |

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

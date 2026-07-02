# TalentSignal — Live Examples & Validation

Real, captured request/response pairs from the **live** deployments, plus scripts to
validate each surface yourself. Everything here was run against the production URLs.

## Live URLs
- **Studio UI:** https://talentsignal-production.up.railway.app
- **REST API + Swagger docs:** https://talentsignal-api-production.up.railway.app/docs
- **MCP server:** run `python3 mcp_server.py` (stdio; connect to Claude Desktop — see `mcp/`)

---

## REST API — `examples/rest/`

Captured live request/response pairs for every endpoint:

| Endpoint | Files | What it shows |
|---|---|---|
| `GET /health` | `01_health_response.json` | Liveness |
| `POST /rank` | `02_rank_request.json` / `_response.json` | Ranks 2 candidates; ML Engineer #1 (0.52) over Backend (0.0) — meaning match |
| `POST /ingest/jd` | `03_ingest_jd_*.json` | JD → structured requirements (years 5–9 parsed) |
| `POST /audit` | `04_audit_*.json` | Fabrication check → `is_impossible: true` on a 0-months-expert / impossible-tenure profile |
| `POST /compliance` | `05_compliance_*.json` | EEOC four-fifths adverse-impact report |
| `POST /candidate_report` | `06_candidate_report_*.json` | Candidate-facing transparency report |

### Validate the REST API yourself
```bash
# against the live API:
bash examples/rest/validate_rest.sh

# or point at a local server:
python3 api_server.py &                       # starts on :8900
BASE=http://localhost:8900 bash examples/rest/validate_rest.sh
```
Or open the interactive **Swagger UI** and click "Try it out":
https://talentsignal-api-production.up.railway.app/docs

---

## MCP server — `examples/mcp/`

The MCP server is **not a URL** — it's a local stdio process an AI client (Claude Desktop,
agent frameworks) launches. See `examples/mcp/README.md` for:
- Real request/response captures for all 9 tools + 4 prompts
- `validate_mcp.py` — a one-command end-to-end test over the real stdio protocol
- `claude_desktop_config.json` — drop-in config to use it inside Claude Desktop

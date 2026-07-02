# TalentSignal MCP — Test & Use

The MCP server is a **local stdio process** (not a URL). An AI client — Claude Desktop or an
agent framework — launches it and calls its tools. This folder lets you validate it and wire
it into Claude Desktop.

## 1. Validate it yourself (one command)

```bash
python3 examples/mcp/validate_mcp.py
```

This launches the server exactly as a client would and exercises the handshake, **all 9
tools**, **all 4 prompts**, and the error handling over the real stdio JSON-RPC protocol.
Expected: **18 passed, 0 failed**. Add `--save` to also write real captures to
`captures.json`.

Quick manual check (lists the 9 tools):
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 mcp_server.py
```

## 2. Real captured output

`captures.json` holds real request/response data from a live run — including:
- `rank_candidates` → **CAND_A** ranked #1 (a candidate who describes ranking work in their
  *own words*, no JD keywords — matched by meaning).
- `audit_candidate` → **`is_impossible: true`** on a keyword-stuffed profile (expert skill,
  0 months; 15 years tenure vs 4 years experience) — caught by contradiction, not keywords.
- `compliance` (flat labels) → runs without crashing (the bug that broke `fair_hiring_review`
  is fixed).

## 3. Use it inside Claude Desktop

1. Open Claude Desktop's config:
   `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
2. Merge in the contents of **`claude_desktop_config.json`** (in this folder — it already has
   the correct absolute path to `mcp_server.py`).
3. Restart Claude Desktop. A 🔌 tools indicator appears.
4. Try, in Claude Desktop:
   > *"Use talentsignal to rank these three résumés against this JD, flag anything suspicious,
   > and prep me to interview the top candidate."*

Claude will call `rank_candidates` → `audit_candidate` → `build_interview_kit` and answer in
plain English — backed by the real deterministic engine, not a guess.

## The 9 tools
`rank_candidates`, `compare_candidates`, `build_interview_kit`, `candidate_report`,
`compliance`, `audit_candidate`, `ingest_jd`, `screen_resume`, `explain_ranking`.

## The 4 workflow prompts (one-click outcomes)
`shortlist_for_role`, `fair_hiring_review`, `prep_interview`, `explain_to_candidate`.

See `../../docs/mcp.md` for full tool schemas and the robustness guarantees.

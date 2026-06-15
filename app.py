#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).parent / "src"))

from talentsignal.jd_parser import load_job_spec
from talentsignal.ranking import (
    rank_candidates,
    write_evidence_packets,
    write_factor_scores,
    write_risk_report,
    write_risk_summary,
    write_submission,
)

DEFAULT_CANDIDATES = "[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
DEFAULT_JOB_SPEC = "job_specs/redrob_senior_ai_engineer.yaml"
UI_OUTPUT_DIR = Path("outputs/ui")


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TalentSignal AI Recruiter Cockpit</title>
  <style>
    :root {
      --bg: #f4f6f8;
      --panel: #ffffff;
      --line: #d8dee6;
      --text: #172026;
      --muted: #5c6672;
      --accent: #146c63;
      --warn: #9b4d00;
      --bad: #a11c2f;
      --good: #1c7c47;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }
    header.app { background: #101820; color: white; padding: 18px 24px; }
    header.app h1 { margin: 0; font-size: 24px; letter-spacing: 0; }
    header.app p { margin: 6px 0 0; color: #c8d2dc; max-width: 980px; }
    main { max-width: 1320px; margin: 0 auto; padding: 20px; }
    .toolbar { display: grid; grid-template-columns: minmax(260px, 1.3fr) minmax(220px, .8fr) 110px 150px 140px; gap: 12px; align-items: end; background: var(--panel); border: 1px solid var(--line); padding: 16px; border-radius: 8px; }
    .filters { display: grid; grid-template-columns: minmax(260px, 1fr) 180px 150px; gap: 12px; align-items: end; background: var(--panel); border: 1px solid var(--line); border-top: 0; padding: 14px 16px; border-radius: 0 0 8px 8px; }
    label { display: grid; gap: 5px; font-size: 13px; color: var(--muted); font-weight: 650; }
    input, select, button { font: inherit; border-radius: 6px; border: 1px solid var(--line); padding: 10px 11px; background: white; color: var(--text); }
    button { border-color: var(--accent); background: var(--accent); color: white; font-weight: 750; cursor: pointer; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    .status { margin: 14px 0; min-height: 24px; color: var(--muted); }
    .status strong { color: var(--text); }
    .metrics { display: grid; grid-template-columns: repeat(5, minmax(130px, 1fr)); gap: 10px; margin: 14px 0; }
    .metric { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 12px; }
    .metric span { display: block; color: var(--muted); font-size: 12px; font-weight: 700; }
    .metric b { font-size: 22px; }
    .layout { display: grid; grid-template-columns: minmax(480px, 1fr) minmax(360px, .75fr); gap: 14px; }
    .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
    .panel h2 { margin: 0; padding: 13px 15px; border-bottom: 1px solid var(--line); font-size: 16px; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 10px; border-bottom: 1px solid #edf0f3; text-align: left; vertical-align: top; }
    th { color: var(--muted); background: #fafbfc; font-size: 12px; position: sticky; top: 0; }
    tbody tr { cursor: pointer; }
    tbody tr:hover, tbody tr.selected { background: #eef8f6; }
    .pill { display: inline-block; padding: 3px 7px; border-radius: 999px; background: #e7f5ee; color: var(--good); font-size: 12px; font-weight: 750; }
    .pill.warn { background: #fff2df; color: var(--warn); }
    .pill.bad { background: #fde7eb; color: var(--bad); }
    .detail { padding: 15px; }
    .detail h3 { margin: 0 0 5px; }
    .detail .sub { color: var(--muted); margin-bottom: 14px; }
    .reason { line-height: 1.45; background: #f8fafb; border-left: 4px solid var(--accent); padding: 10px 12px; }
    .factors { display: grid; gap: 8px; margin: 14px 0; }
    .factor { display: grid; grid-template-columns: 92px 1fr 52px; gap: 8px; align-items: center; }
    meter { width: 100%; height: 16px; }
    .evidence { display: grid; gap: 9px; }
    .evidence div { padding: 9px; background: #fafbfc; border: 1px solid #edf0f3; border-radius: 6px; }
    .downloads a { display: inline-block; margin: 6px 8px 0 0; color: var(--accent); font-weight: 750; }
    @media (max-width: 940px) {
      .toolbar { grid-template-columns: 1fr; }
      .metrics { grid-template-columns: repeat(2, 1fr); }
      .layout { grid-template-columns: 1fr; }
    }
    @media (max-width: 620px) {
      header.app { padding: 14px 16px; }
      header.app h1 { font-size: 19px; }
      header.app p { font-size: 13px; }
      main { padding: 10px; }
      .filters { grid-template-columns: 1fr; }
      .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .metric { padding: 10px; }
      .metric b { font-size: 18px; }
      table, thead, tbody, tr, td { display: block; }
      thead { display: none; }
      tbody tr { display: grid; grid-template-columns: 78px minmax(0, 1fr); gap: 3px 8px; padding: 10px; border-bottom: 1px solid #edf0f3; }
      tbody td { border-bottom: 0; padding: 0; overflow-wrap: anywhere; }
      tbody td:nth-child(1) { grid-row: 1 / span 4; }
      tbody td:nth-child(2), tbody td:nth-child(3), tbody td:nth-child(4), tbody td:nth-child(5) { grid-column: 2; }
      tbody td:nth-child(4)::before { content: "Evidence: "; color: var(--muted); font-weight: 750; }
      tbody td:nth-child(5)::before { content: "Risk: "; color: var(--muted); font-weight: 750; }
      th, td { font-size: 12px; }
      .factor { grid-template-columns: 76px minmax(0, 1fr) 48px; }
    }
  </style>
</head>
<body>
  <header class="app">
    <h1>TalentSignal AI Recruiter Cockpit</h1>
    <p>Run the actual backend ranker on real candidate data, inspect factor scores, review grounded evidence, audit risk flags, and export the challenge CSV.</p>
  </header>
  <main>
    <section class="toolbar">
      <label>Candidate JSONL path
        <input id="candidatePath" value="__DEFAULT_CANDIDATES__">
      </label>
      <label>Job scorecard
        <input id="jobSpec" value="__DEFAULT_JOB_SPEC__">
      </label>
      <label>Rows
        <select id="topN">
          <option value="25">25</option>
          <option value="50">50</option>
          <option value="100" selected>100</option>
        </select>
      </label>
      <label>Sort
        <select id="sortBy">
          <option value="rank" selected>Rank</option>
          <option value="score">Score</option>
          <option value="confidence">Confidence</option>
          <option value="title">Title</option>
        </select>
      </label>
      <button id="runBtn">Run Ranker</button>
    </section>
    <section class="filters">
      <label>Search shortlist
        <input id="searchBox" placeholder="Candidate ID, title, city, evidence term">
      </label>
      <label>Risk view
        <select id="riskFilter">
          <option value="all" selected>All candidates</option>
          <option value="clear">Clear only</option>
          <option value="flagged">Flagged only</option>
        </select>
      </label>
      <button id="resetBtn" type="button">Reset View</button>
    </section>
    <div id="status" class="status">Ready. This UI calls the local REST backend; no hardcoded candidate cards are used.</div>
    <section class="metrics" id="metrics"></section>
    <section class="layout">
      <div class="panel">
        <h2>Ranked Shortlist</h2>
        <table>
          <thead><tr><th>Rank</th><th>Candidate</th><th>Fit</th><th>Evidence</th><th>Risk</th></tr></thead>
          <tbody id="results"></tbody>
        </table>
      </div>
      <aside class="panel">
        <h2>Evidence Packet</h2>
        <div id="detail" class="detail">Run the ranker and select a candidate.</div>
      </aside>
    </section>
  </main>
  <script>
    let packets = [];
    let selectedIndex = 0;
    const $ = (id) => document.getElementById(id);
    function esc(value) {
      return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
    }
    function terms(items) { return (items && items.length) ? items.map(esc).join(", ") : "None"; }
    function metric(label, value) { return `<div class="metric"><span>${esc(label)}</span><b>${esc(value)}</b></div>`; }
    function factor(name, value) {
      const v = Number(value || 0);
      return `<div class="factor"><span>${esc(name)}</span><meter min="0" max="1" value="${v}"></meter><b>${v.toFixed(3)}</b></div>`;
    }
    function renderMetrics(data) {
      $("metrics").innerHTML = [
        metric("Rows", data.rows.length),
        metric("Runtime", `${data.elapsed_seconds.toFixed(2)}s`),
        metric("Top-10 Eligible", data.summary.top10_eligible_count + "/10"),
        metric("Risk Flags", data.summary.risk_flagged_count),
        metric("CSV", data.files.submission.split("/").pop())
      ].join("");
    }
    function renderRows() {
      const query = $("searchBox").value.trim().toLowerCase();
      const risk = $("riskFilter").value;
      const sortBy = $("sortBy").value;
      let visible = packets.filter((p) => {
        const ev = p.evidence, sc = p.score_breakdown;
        const haystack = [
          p.candidate_id, ev.title, ev.location, p.reasoning,
          ...(ev.career_retrieval_terms || []), ...(ev.vector_terms || []), ...(ev.eval_terms || []), ...(sc.risk_flags || [])
        ].join(" ").toLowerCase();
        const matchesQuery = !query || haystack.includes(query);
        const matchesRisk = risk === "all" || (risk === "clear" && sc.risk_flags.length === 0) || (risk === "flagged" && sc.risk_flags.length > 0);
        return matchesQuery && matchesRisk;
      });
      visible.sort((a, b) => {
        if (sortBy === "score") return Number(b.score) - Number(a.score);
        if (sortBy === "confidence") return Number(b.score_breakdown.confidence) - Number(a.score_breakdown.confidence);
        if (sortBy === "title") return a.evidence.title.localeCompare(b.evidence.title) || a.rank - b.rank;
        return a.rank - b.rank;
      });
      $("results").innerHTML = visible.map((p, idx) => {
        const ev = p.evidence, sc = p.score_breakdown;
        const riskClass = sc.risk_flags.length ? "bad" : "";
        const evidence = ev.career_retrieval_terms.slice(0, 3).join(", ") || ev.vector_terms.slice(0, 2).join(", ");
        return `<tr data-candidate="${esc(p.candidate_id)}" data-idx="${idx}">
          <td><b>#${p.rank}</b><br><span class="pill">${p.score}</span></td>
          <td><b>${esc(p.candidate_id)}</b><br>${esc(ev.title)}<br><small>${esc(ev.years)} yrs · ${esc(ev.location)}</small></td>
          <td>${sc.top10_eligible ? '<span class="pill">eligible</span>' : '<span class="pill warn">review</span>'}<br>conf ${Number(sc.confidence).toFixed(2)}</td>
          <td>${esc(evidence)}</td>
          <td><span class="pill ${riskClass}">${sc.risk_flags.length ? sc.risk_flags.length + " flags" : "clear"}</span></td>
        </tr>`;
      }).join("");
      document.querySelectorAll("#results tr").forEach(row => row.addEventListener("click", () => {
        const packet = visible[Number(row.dataset.idx)];
        selectedIndex = packets.findIndex(p => p.candidate_id === packet.candidate_id);
        selectCandidate(selectedIndex);
      }));
      if (visible.length) {
        selectedIndex = packets.findIndex(p => p.candidate_id === visible[0].candidate_id);
        selectCandidate(selectedIndex);
      } else {
        $("detail").textContent = "No candidates match the current filters.";
      }
    }
    function selectCandidate(idx) {
      document.querySelectorAll("#results tr").forEach(r => r.classList.toggle("selected", Number(r.dataset.idx) === idx));
      const p = packets[idx], ev = p.evidence, sc = p.score_breakdown;
      $("detail").innerHTML = `<h3>#${p.rank} ${esc(p.candidate_id)}</h3>
        <div class="sub">${esc(ev.title)} · ${esc(ev.years)} years · ${esc(ev.location)} · score ${esc(p.score)}</div>
        <p class="reason">${esc(p.reasoning)}</p>
        <div class="factors">
          ${factor("Technical", sc.technical_evidence)}
          ${factor("Career", sc.career_fit)}
          ${factor("Seniority", sc.seniority)}
          ${factor("Logistics", sc.logistics)}
          ${factor("Behavior", sc.behavioral)}
          ${factor("Trust", sc.trust)}
          ${factor("Confidence", sc.confidence)}
        </div>
        <div class="evidence">
          <div><b>Career retrieval/ranking:</b> ${terms(ev.career_retrieval_terms)}</div>
          <div><b>Production:</b> ${terms(ev.career_production_terms)}</div>
          <div><b>Vector/search tooling:</b> ${terms(ev.vector_terms)}</div>
          <div><b>Evaluation:</b> ${terms(ev.eval_terms)}</div>
          <div><b>Risk flags:</b> ${terms(sc.risk_flags)}</div>
        </div>`;
    }
    async function runRanker() {
      const btn = $("runBtn");
      btn.disabled = true;
      $("status").innerHTML = "Running ranker on real candidate data...";
      $("results").innerHTML = "";
      $("detail").textContent = "Waiting for backend results.";
      try {
        const response = await fetch("/api/rank", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            candidates_path: $("candidatePath").value,
            job_spec: $("jobSpec").value,
            top_n: Number($("topN").value)
          })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Ranker failed");
        packets = data.rows;
        $("status").innerHTML = `<strong>Completed.</strong> Processed real data from <code>${esc(data.candidates_path)}</code>. <span class="downloads">
          <a href="/download/ui_submission.csv">CSV</a>
          <a href="/download/ui_factor_scores.csv">Factors</a>
          <a href="/download/ui_evidence_packets.jsonl">Evidence</a>
          <a href="/download/ui_risk_report.csv">Risk</a>
        </span>`;
        renderMetrics(data);
        renderRows();
      } catch (err) {
        $("status").innerHTML = `<span style="color: var(--bad); font-weight: 750;">${esc(err.message)}</span>`;
      } finally {
        btn.disabled = false;
      }
    }
    $("runBtn").addEventListener("click", runRanker);
    $("searchBox").addEventListener("input", renderRows);
    $("riskFilter").addEventListener("change", renderRows);
    $("sortBy").addEventListener("change", renderRows);
    $("resetBtn").addEventListener("click", () => {
      $("searchBox").value = "";
      $("riskFilter").value = "all";
      $("sortBy").value = "rank";
      renderRows();
    });
  </script>
</body>
</html>
"""


class AppHandler(BaseHTTPRequestHandler):
    server_version = "TalentSignalHTTP/1.0"

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            html = INDEX_HTML.replace("__DEFAULT_CANDIDATES__", DEFAULT_CANDIDATES).replace("__DEFAULT_JOB_SPEC__", DEFAULT_JOB_SPEC)
            self._send(HTTPStatus.OK, html.encode("utf-8"), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/status":
            self._json(HTTPStatus.OK, {"status": "ok", "default_candidates": DEFAULT_CANDIDATES, "default_job_spec": DEFAULT_JOB_SPEC})
            return
        if parsed.path.startswith("/download/"):
            filename = Path(unquote(parsed.path.split("/", 2)[2])).name
            file_path = UI_OUTPUT_DIR / filename
            if not file_path.exists():
                self._json(HTTPStatus.NOT_FOUND, {"error": f"not found: {filename}"})
                return
            content_type = "text/csv; charset=utf-8" if filename.endswith(".csv") else "application/octet-stream"
            body = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(body)
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/rank":
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            candidates_path = payload.get("candidates_path") or DEFAULT_CANDIDATES
            job_spec_path = payload.get("job_spec") or DEFAULT_JOB_SPEC
            top_n = int(payload.get("top_n") or 100)
            if top_n < 1 or top_n > 100:
                raise ValueError("top_n must be between 1 and 100")
            if not Path(candidates_path).exists():
                raise ValueError(f"candidate file not found: {candidates_path}")
            if not Path(job_spec_path).exists():
                raise ValueError(f"job spec not found: {job_spec_path}")
            start = time.perf_counter()
            job = load_job_spec(job_spec_path)
            rows = rank_candidates(candidates_path, job, top_n=top_n)
            UI_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            submission = UI_OUTPUT_DIR / "ui_submission.csv"
            factors = UI_OUTPUT_DIR / "ui_factor_scores.csv"
            evidence = UI_OUTPUT_DIR / "ui_evidence_packets.jsonl"
            risk = UI_OUTPUT_DIR / "ui_risk_report.csv"
            summary = UI_OUTPUT_DIR / "ui_risk_summary.json"
            write_submission(rows, submission)
            write_factor_scores(rows, factors)
            write_evidence_packets(rows, evidence)
            write_risk_report(rows, risk)
            write_risk_summary(rows, summary)
            packets = []
            with evidence.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        packets.append(json.loads(line))
            top10 = packets[:10]
            response = {
                "candidates_path": candidates_path,
                "job_spec": job_spec_path,
                "elapsed_seconds": round(time.perf_counter() - start, 3),
                "rows": packets,
                "summary": {
                    "top10_eligible_count": sum(1 for p in top10 if p["score_breakdown"]["top10_eligible"]),
                    "risk_flagged_count": sum(1 for p in packets if p["score_breakdown"]["risk_flags"]),
                },
                "files": {
                    "submission": str(submission),
                    "factor_scores": str(factors),
                    "evidence_packets": str(evidence),
                    "risk_report": str(risk),
                    "risk_summary": str(summary),
                },
            }
            self._json(HTTPStatus.OK, response)
        except Exception as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def serve(host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"TalentSignal UI running at http://{host}:{port}")
    server.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the live TalentSignal Recruiter Cockpit.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    serve(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

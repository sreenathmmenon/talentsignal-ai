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
from talentsignal.boundary_review import boundary_windows
from talentsignal.candidate_compare import compare_by_rank
from talentsignal.interview_kit import build_interview_kits
from talentsignal.ranking import (
    rank_candidates_with_pool,
    write_evidence_packets,
    write_factor_scores,
    write_risk_report,
    write_risk_summary,
    write_submission,
)
from talentsignal.trap_detector import rejected_trap_examples, rejected_trap_examples_from_scored

DEFAULT_CANDIDATES = "[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
DEFAULT_JOB_SPEC = "job_specs/redrob_senior_ai_engineer.yaml"
UI_OUTPUT_DIR = Path("outputs/ui")
PRODUCT_TAGLINE = "Evidence-backed hiring decisions for any role."
HELIX_THEME_CSS = Path("/Users/sreenath/Code/myAIExps/personal-website/design-systems/helix/theme.css")
HELIX_FONT_LINK = (
    "https://fonts.googleapis.com/css2?"
    "family=IBM+Plex+Mono:wght@400;500&"
    "family=IBM+Plex+Sans:wght@400;500;600;700&display=swap"
)


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TalentSignal AI Recruiter Cockpit</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="__FONT_LINK__" rel="stylesheet">
  <link rel="stylesheet" href="/assets/helix-theme.css">
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; }
    .ts-app {
      min-height: 100vh;
      background:
        radial-gradient(circle at 16% -12%, rgba(15,98,254,.12), transparent 448px),
        radial-gradient(circle at 88% -8%, rgba(8,189,186,.06), transparent 448px),
        #07090D;
    }
    .ts-topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
      padding: 16px 24px;
      border-bottom: 1px solid rgba(245,247,251,.08);
    }
    .ts-brand { display: grid; gap: 4px; }
    .ts-brand strong { color: #F5F7FB; font-size: 18px; font-weight: 760; }
    .ts-brand span { color: #94A2B8; font-size: 13px; }
    .ts-env {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border-radius: 999px;
      border: 1px solid rgba(120,169,255,.10);
      background: rgba(15,98,254,.16);
      color: #78A9FF;
      padding: 7px 12px;
      font-size: 12px;
      font-weight: 650;
    }
    .ts-workspace {
      max-width: 1480px;
      margin: 0 auto;
      padding: 24px;
      display: grid;
      grid-template-columns: 210px minmax(0, 1fr);
      gap: 24px;
      align-items: start;
    }
    .ts-sidebar {
      position: sticky;
      top: 20px;
      background: rgba(13,18,25,.82);
      border: 1px solid rgba(245,247,251,.08);
      border-radius: 7px;
      box-shadow: 0 1px 0 rgba(245,247,251,.04) inset, 0 8px 30px rgba(0,0,0,.45);
    }
    .ts-main { min-width: 0; }
    .ts-hero {
      margin-bottom: 18px;
      display: grid;
      gap: 14px;
    }
    .ts-hero h1 {
      margin: 0;
      color: #F5F7FB;
      font-size: 42px;
      font-weight: 760;
      line-height: 1.08;
      letter-spacing: -0.01em;
      max-width: 900px;
    }
    .ts-hero .grad-text {
      background: linear-gradient(135deg, #0F62FE 0%, #08BDBA 100%);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      font-weight: 820;
    }
    .ts-hero p {
      margin: 0;
      max-width: 780px;
      color: #BAC5D6;
      line-height: 1.55;
    }
    .ts-control-card,
    .ts-panel,
    .ts-metric {
      background: rgba(13,18,25,.82);
      border: 1px solid rgba(245,247,251,.08);
      border-radius: 7px;
      box-shadow: 0 1px 0 rgba(245,247,251,.04) inset, 0 8px 30px rgba(0,0,0,.45);
    }
    .ts-control-card { padding: 18px; }
    .ts-form {
      display: grid;
      grid-template-columns: minmax(260px, 1.4fr) minmax(220px, .85fr) 110px 145px 150px;
      gap: 12px;
      align-items: end;
    }
    .ts-filters {
      display: grid;
      grid-template-columns: minmax(260px, 1fr) 180px 150px;
      gap: 12px;
      align-items: end;
      margin-top: 12px;
    }
    .ts-field {
      display: grid;
      gap: 6px;
      color: #94A2B8;
      font-size: 12px;
      font-weight: 650;
      letter-spacing: .05em;
      text-transform: uppercase;
    }
    .ts-field input,
    .ts-field select {
      width: 100%;
      font-family: "IBM Plex Sans", Inter, ui-sans-serif, system-ui, sans-serif;
      font-size: 14px;
      text-transform: none;
      letter-spacing: 0;
      color: #F5F7FB;
      background: #0A0D13;
      border: 1px solid rgba(245,247,251,.08);
      border-radius: 5px;
      padding: 10px 12px;
    }
    .ts-field input:focus,
    .ts-field select:focus {
      outline: none;
      border-color: #0F62FE;
      box-shadow: 0 0 0 3px rgba(15,98,254,.25);
    }
    .ts-form button,
    .ts-filters button {
      justify-content: center;
      min-height: 40px;
    }
    .ts-form .btn-primary {
      background: linear-gradient(135deg, #0F62FE 0%, #08BDBA 100%);
      box-shadow: 0 0 0 1px rgba(15,98,254,.35), 0 8px 30px rgba(15,98,254,.20);
    }
    .ts-status {
      min-height: 28px;
      margin: 14px 0;
      color: #94A2B8;
    }
    .ts-status.is-running {
      border: 1px solid rgba(15,98,254,.32);
      background: rgba(15,98,254,.10);
      border-radius: 7px;
      padding: 12px;
      color: #BAC5D6;
    }
    .ts-progress {
      display: grid;
      gap: 8px;
    }
    .ts-progress-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      color: #F5F7FB;
      font-weight: 650;
    }
    .ts-progress-track {
      position: relative;
      overflow: hidden;
      height: 6px;
      border-radius: 999px;
      background: rgba(245,247,251,.08);
    }
    .ts-progress-track::after {
      content: "";
      position: absolute;
      inset: 0;
      width: 42%;
      border-radius: inherit;
      background: linear-gradient(135deg, #0F62FE 0%, #08BDBA 100%);
      animation: ts-loading 1.25s ease-in-out infinite;
    }
    .ts-run-note { color: #94A2B8; font-size: 13px; }
    @keyframes ts-loading {
      0% { transform: translateX(-115%); }
      50% { transform: translateX(72%); }
      100% { transform: translateX(238%); }
    }
    .btn.is-running {
      cursor: wait;
      opacity: .9;
    }
    .ts-status strong { color: #F5F7FB; }
    .ts-status code {
      font-family: "IBM Plex Mono", ui-monospace, monospace;
      color: #BAC5D6;
    }
    .ts-downloads a {
      margin-left: 10px;
      color: #78A9FF;
      font-weight: 650;
    }
    .ts-metrics {
      display: grid;
      grid-template-columns: repeat(5, minmax(130px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .ts-metric { padding: 16px; }
    .ts-metric span {
      display: block;
      color: #94A2B8;
      font-size: 12px;
      font-weight: 650;
      text-transform: uppercase;
      letter-spacing: .05em;
    }
    .ts-metric b {
      color: #F5F7FB;
      font-size: 24px;
      line-height: 1.1;
    }
    .ts-layout {
      display: grid;
      grid-template-columns: minmax(520px, 1fr) minmax(380px, .72fr);
      gap: 18px;
      align-items: start;
    }
    .ts-intel-grid {
      display: grid;
      grid-template-columns: 1.12fr .88fr;
      gap: 18px;
      margin-bottom: 18px;
    }
    .ts-flow-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
      margin-bottom: 18px;
    }
    .ts-panel { padding: 18px; overflow: hidden; }
    .ts-panel h2 {
      margin: 0 0 14px;
      color: #F5F7FB;
      font-size: 18px;
      font-weight: 650;
    }
    .ts-panel h3 {
      margin: 0 0 8px;
      color: #F5F7FB;
      font-size: 14px;
      font-weight: 650;
    }
    .ts-panel p { color: #BAC5D6; line-height: 1.5; }
    .ts-kv {
      display: grid;
      grid-template-columns: 120px minmax(0, 1fr);
      gap: 8px 12px;
      align-items: start;
      color: #BAC5D6;
      font-size: 13px;
    }
    .ts-kv b {
      color: #94A2B8;
      font-weight: 650;
      text-transform: uppercase;
      letter-spacing: .04em;
      font-size: 11px;
    }
    .ts-chip-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }
    .ts-mini-list {
      display: grid;
      gap: 8px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .ts-mini-list li {
      background: #0A0D13;
      border: 1px solid rgba(245,247,251,.08);
      border-radius: 7px;
      color: #BAC5D6;
      line-height: 1.4;
      padding: 10px;
    }
    .ts-mini-list b { color: #F5F7FB; }
    .ts-compare-card {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .ts-compare-col {
      background: #0A0D13;
      border: 1px solid rgba(245,247,251,.08);
      border-radius: 7px;
      padding: 12px;
      min-width: 0;
    }
    .ts-compare-col strong { color: #F5F7FB; display: block; margin-bottom: 6px; }
    .ts-compare-col span { color: #BAC5D6; font-size: 13px; }
    .ts-outcome {
      margin-top: 10px;
      border-left: 4px solid #0F62FE;
      background: rgba(15,98,254,.12);
      color: #F5F7FB;
      padding: 10px 12px;
      border-radius: 5px;
      line-height: 1.45;
    }
    .ts-table-wrap { overflow: hidden; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td {
      text-align: left;
      vertical-align: top;
      padding: 10px;
      border-bottom: 1px solid rgba(245,247,251,.08);
    }
    th {
      color: #94A2B8;
      font-size: 12px;
      font-weight: 650;
    }
    tbody tr { cursor: pointer; }
    tbody tr:hover,
    tbody tr.selected { background: rgba(15,98,254,.16); }
    .ts-score {
      font-family: "IBM Plex Mono", ui-monospace, monospace;
      color: #42BE65;
      font-weight: 650;
    }
    .ts-detail { display: grid; gap: 14px; }
    .ts-detail h3 { margin: 0; color: #F5F7FB; }
    .ts-sub { color: #94A2B8; }
    .ts-reason,
    .ts-evidence div {
      background: #0A0D13;
      border: 1px solid rgba(245,247,251,.08);
      border-radius: 7px;
      padding: 12px;
      line-height: 1.45;
    }
    .ts-reason { margin: 0; border-left: 4px solid #08BDBA; }
    .ts-factors { display: grid; gap: 9px; }
    .ts-factor {
      display: grid;
      grid-template-columns: 92px minmax(0, 1fr) 54px;
      gap: 8px;
      align-items: center;
    }
    .ts-factor span { color: #BAC5D6; }
    .ts-factor b {
      color: #F5F7FB;
      font-family: "IBM Plex Mono", ui-monospace, monospace;
      font-size: 13px;
    }
    meter { width: 100%; height: 15px; }
    meter::-webkit-meter-optimum-value { background: #42BE65; }
    .ts-evidence { display: grid; gap: 9px; }
    .ts-evidence b { color: #F5F7FB; }
    @media (max-width: 980px) {
      .ts-topbar { display: grid; }
      .ts-workspace { grid-template-columns: 1fr; }
      .ts-sidebar { position: static; width: 100%; }
      .ts-main,
      .ts-hero,
      .ts-control-card,
      .ts-panel { width: 100%; max-width: none; }
      .ts-form,
      .ts-filters,
      .ts-intel-grid,
      .ts-flow-grid,
      .ts-layout { grid-template-columns: 1fr; }
      .ts-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 620px) {
      .ts-topbar,
      .ts-workspace { padding: 14px; }
      .ts-hero h1 { font-size: 30px; }
      table, thead, tbody, tr, td { display: block; }
      thead { display: none; }
      tbody tr {
        display: grid;
        grid-template-columns: 78px minmax(0, 1fr);
        gap: 4px 9px;
        padding: 10px;
        border-bottom: 1px solid rgba(245,247,251,.08);
      }
      tbody td {
        border-bottom: 0;
        padding: 0;
        overflow-wrap: anywhere;
      }
      tbody td:nth-child(1) { grid-row: 1 / span 4; }
      tbody td:nth-child(2),
      tbody td:nth-child(3),
      tbody td:nth-child(4),
      tbody td:nth-child(5) { grid-column: 2; }
      tbody td:nth-child(4)::before {
        content: "Evidence: ";
        color: #94A2B8;
        font-weight: 650;
      }
      tbody td:nth-child(5)::before {
        content: "Risk: ";
        color: #94A2B8;
        font-weight: 650;
      }
      .ts-factor { grid-template-columns: 76px minmax(0, 1fr) 48px; }
    }
  </style>
</head>
<body>
<div class="ts-app">
  <header class="ts-topbar">
    <div class="ts-brand">
      <strong>TalentSignal AI</strong>
      <span>__PRODUCT_TAGLINE__</span>
    </div>
    <span class="ts-env">Production-grade shortlist workspace</span>
  </header>
  <div class="ts-workspace">
    <nav class="sidebar ts-sidebar" aria-label="TalentSignal workflow">
      <div style="display:flex;align-items:center;gap:8px;padding:8px;color:#F5F7FB;font-weight:700">▦ TalentSignal</div>
      <a class="is-active">⬡ Role Intelligence</a>
      <a>◎ Shortlist</a>
      <a>▤ Compare</a>
      <a>◈ Trust Layer</a>
      <a>⌁ Interview Kit</a>
      <a>⤓ Exports</a>
    </nav>
    <main class="ts-main">
      <section class="ts-hero">
        <span class="chip chip-info">Universal JD intelligence engine</span>
        <h1><span class="grad-text">__PRODUCT_TAGLINE__</span></h1>
        <p>Convert any job requirement into a role scorecard, evidence-ranked shortlist, trust review, candidate comparison, interview probes, and reproducible hiring artifact.</p>
      </section>
      <section class="ts-control-card">
        <div class="ts-form">
          <label class="ts-field">Candidate JSONL path
            <input id="candidatePath" value="__DEFAULT_CANDIDATES__">
          </label>
          <label class="ts-field">Job scorecard
            <input id="jobSpec" value="__DEFAULT_JOB_SPEC__">
          </label>
          <label class="ts-field">Rows
            <select id="topN">
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100" selected>100</option>
            </select>
          </label>
          <label class="ts-field">Sort
            <select id="sortBy">
              <option value="rank" selected>Rank</option>
              <option value="score">Score</option>
              <option value="confidence">Confidence</option>
              <option value="title">Title</option>
            </select>
          </label>
          <button class="btn btn-primary" id="runBtn">Generate Shortlist</button>
        </div>
        <div class="ts-filters">
          <label class="ts-field">Search shortlist
            <input id="searchBox" placeholder="Candidate ID, title, city, evidence term">
          </label>
          <label class="ts-field">Risk view
            <select id="riskFilter">
              <option value="all" selected>All candidates</option>
              <option value="clear">Clear only</option>
              <option value="flagged">Flagged only</option>
            </select>
          </label>
          <button class="btn btn-secondary" id="resetBtn" type="button">Reset View</button>
        </div>
      </section>
      <div id="status" class="ts-status" aria-live="polite">Ready. Select a candidate file and scorecard to generate the ranked shortlist.</div>
      <section class="ts-metrics" id="metrics"></section>
      <section class="ts-intel-grid">
        <div class="ts-panel">
          <h2>Role Intelligence</h2>
          <div id="roleIntel" class="ts-kv">Run the ranker to load the job scorecard and decision priorities.</div>
        </div>
        <div class="ts-panel">
          <h2>Decision Framework</h2>
          <ul id="decisionFramework" class="ts-mini-list">
            <li>Run the ranker to expose the weighted factors used for this shortlist.</li>
          </ul>
        </div>
      </section>
      <section class="ts-flow-grid">
        <div class="ts-panel">
          <h2>Compare Mode</h2>
          <div class="ts-compare-card" style="margin-bottom:10px">
            <label class="ts-field">Left rank
              <select id="compareLeft"><option value="1">#1</option><option value="5">#5</option><option value="10">#10</option><option value="25">#25</option><option value="100">#100</option></select>
            </label>
            <label class="ts-field">Right rank
              <select id="compareRight"><option value="2">#2</option><option value="6">#6</option><option value="11">#11</option><option value="26">#26</option><option value="101">#101</option></select>
            </label>
          </div>
          <div id="compareMode">Run the ranker to compare the top two candidates.</div>
        </div>
        <div class="ts-panel">
          <h2>Trust Layer</h2>
          <ul id="trustLayer" class="ts-mini-list">
            <li>Run the ranker to inspect risk concentration and evidence gaps.</li>
          </ul>
        </div>
        <div class="ts-panel">
          <h2>Interview Kit</h2>
          <ul id="interviewKit" class="ts-mini-list">
            <li>Run the ranker to generate candidate-specific interview probes.</li>
          </ul>
        </div>
      </section>
      <section class="ts-flow-grid">
        <div class="ts-panel">
          <h2>Boundary Review</h2>
          <ul id="boundaryReview" class="ts-mini-list">
            <li>Run the ranker to inspect top-10, top-25, and submission cut lines.</li>
          </ul>
        </div>
        <div class="ts-panel">
          <h2>Trap Examples</h2>
          <ul id="trapExamples" class="ts-mini-list">
            <li>Run the ranker to inspect profiles that look strong but carry trust risks.</li>
          </ul>
        </div>
        <div class="ts-panel">
          <h2>Universal JD Proof</h2>
          <ul id="universalProof" class="ts-mini-list">
            <li>The default Redrob scorecard is one role-specific scorecard in a universal JD engine.</li>
          </ul>
        </div>
      </section>
      <section class="ts-layout">
        <div class="ts-panel">
          <h2>Ranked Shortlist</h2>
          <div class="ts-table-wrap">
            <table>
              <thead><tr><th>Rank</th><th>Candidate</th><th>Fit</th><th>Evidence</th><th>Risk</th></tr></thead>
              <tbody id="results"></tbody>
            </table>
          </div>
        </div>
        <aside class="ts-panel">
          <h2>Evidence Packet</h2>
          <div id="detail" class="ts-detail">Run the ranker and select a candidate.</div>
        </aside>
      </section>
    </main>
  </div>
</div>
<script>
let packets = [];
let allPackets = [];
let lastData = null;
let selectedIndex = 0;
const $ = (id) => document.getElementById(id);
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function terms(items) { return (items && items.length) ? items.map(esc).join(", ") : "None"; }
function metric(label, value) {
  return `<div class="ts-metric"><span>${esc(label)}</span><b>${esc(value)}</b></div>`;
}
function chip(value, kind = "chip-info") {
  return `<span class="chip ${kind}">${esc(value)}</span>`;
}
function factor(name, value) {
  const v = Number(value || 0);
  return `<div class="ts-factor"><span>${esc(name)}</span><meter min="0" max="1" value="${v}"></meter><b>${v.toFixed(3)}</b></div>`;
}
function scoreLabel(value) {
  return Number(value || 0).toFixed(3);
}
let runTimer = null;
let runStartedAt = 0;
function setControlsDisabled(disabled) {
  ["candidatePath", "jobSpec", "topN", "sortBy", "searchBox", "riskFilter", "resetBtn", "compareLeft", "compareRight"].forEach(id => {
    const el = $(id);
    if (el) el.disabled = disabled;
  });
}
function renderRunningStatus(stage) {
  const elapsed = Math.max(0, Math.round((Date.now() - runStartedAt) / 1000));
  $("status").classList.add("is-running");
  $("status").innerHTML = `<div class="ts-progress">
    <div class="ts-progress-head"><span>${esc(stage)}</span><span>${elapsed}s</span></div>
    <div class="ts-progress-track" aria-hidden="true"></div>
    <div class="ts-run-note">Scanning candidate data, scoring evidence, auditing trust, and preparing shortlist artifacts. Large files can take around 20-30 seconds locally.</div>
  </div>`;
}
function startRunningStatus() {
  runStartedAt = Date.now();
  renderRunningStatus("Starting ranking pipeline");
  runTimer = window.setInterval(() => {
    const elapsed = Math.round((Date.now() - runStartedAt) / 1000);
    const stage = elapsed < 6 ? "Loading JD scorecard and candidate stream"
      : elapsed < 15 ? "Scoring candidate evidence and trust signals"
      : elapsed < 24 ? "Building shortlist, boundaries, and trap examples"
      : "Writing exports and rendering decision workspace";
    renderRunningStatus(stage);
  }, 1000);
}
function stopRunningStatus() {
  if (runTimer) window.clearInterval(runTimer);
  runTimer = null;
  $("status").classList.remove("is-running");
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
function renderRoleIntel(data) {
  const job = data.job;
  $("roleIntel").innerHTML = `
    <b>Role</b><span>${esc(job.title)}</span>
    <b>Category</b><span>${esc(job.category_label || job.category)}</span>
    <b>Experience</b><span>${esc(job.strongest_min_years)}-${esc(job.strongest_max_years)} strongest, ${esc(job.preferred_min_years)}-${esc(job.preferred_max_years)} preferred</span>
    <b>Locations</b><span>${esc(job.preferred_locations.join(", "))}</span>
    <b>Must-have</b><span><span class="ts-chip-row">${job.must_have.map(v => chip(v, "chip-info")).join("")}</span></span>
    <b>Evidence focus</b><span><span class="ts-chip-row">${(job.category_evidence_priorities || []).map(v => chip(v, "chip-ok")).join("")}</span></span>
    <b>Negative signals</b><span><span class="ts-chip-row">${job.disqualifiers.map(v => chip(v, "chip-crit")).join("")}</span></span>
  `;
  $("decisionFramework").innerHTML = Object.entries(job.weights).map(([name, weight]) =>
    `<li><b>${esc(name.replaceAll("_", " "))}</b><br>${Math.round(Number(weight) * 100)}% of the fit model for this role.</li>`
  ).join("");
}
function strongestFactor(packet) {
  const entries = Object.entries(packet.score_breakdown).filter(([k, v]) => typeof v === "number" && !["score", "confidence"].includes(k));
  entries.sort((a, b) => Number(b[1]) - Number(a[1]));
  return entries[0] || ["evidence", 0];
}
function weakestFactor(packet) {
  const entries = Object.entries(packet.score_breakdown).filter(([k, v]) => typeof v === "number" && !["score", "confidence"].includes(k));
  entries.sort((a, b) => Number(a[1]) - Number(b[1]));
  return entries[0] || ["evidence", 0];
}
function packetByRank(rank) {
  return allPackets.find(p => Number(p.rank) === Number(rank));
}
function renderCompare() {
  const leftRank = Number($("compareLeft").value);
  const rightRank = Number($("compareRight").value);
  const a = packetByRank(leftRank);
  const b = packetByRank(rightRank);
  if (!a || !b) {
    $("compareMode").textContent = "Need at least two ranked candidates for comparison.";
    return;
  }
  const aStrong = strongestFactor(a), bStrong = strongestFactor(b);
  const delta = Number(a.score) - Number(b.score);
  $("compareMode").innerHTML = `
    <div class="ts-compare-card">
      <div class="ts-compare-col"><strong>#${a.rank} ${esc(a.candidate_id)}</strong><span>${esc(a.evidence.title)}<br>Score ${esc(a.score)} · confidence ${scoreLabel(a.score_breakdown.confidence)}<br>Best signal: ${esc(aStrong[0].replaceAll("_", " "))} ${scoreLabel(aStrong[1])}</span></div>
      <div class="ts-compare-col"><strong>#${b.rank} ${esc(b.candidate_id)}</strong><span>${esc(b.evidence.title)}<br>Score ${esc(b.score)} · confidence ${scoreLabel(b.score_breakdown.confidence)}<br>Best signal: ${esc(bStrong[0].replaceAll("_", " "))} ${scoreLabel(bStrong[1])}</span></div>
    </div>
    <div class="ts-outcome">Recommendation: ${delta >= 0 ? "keep" : "review whether"} #${a.rank} ahead of #${b.rank}; score delta ${delta.toFixed(4)}. The scorecard weighs role evidence, career fit, logistics, behavioral availability, and trust together instead of keyword overlap alone.</div>
  `;
}
function renderTrustLayer(data) {
  const flagged = packets.filter(p => p.score_breakdown.risk_flags.length);
  const top10Flagged = packets.slice(0, 10).filter(p => p.score_breakdown.risk_flags.length);
  const lowConfidence = packets.filter(p => Number(p.score_breakdown.confidence) < 0.55);
  $("trustLayer").innerHTML = [
    `<li><b>Top-10 risk pressure</b><br>${top10Flagged.length} of the first 10 candidates carry risk flags.</li>`,
    `<li><b>Evidence coverage</b><br>${data.summary.top10_eligible_count} of top 10 pass the top-candidate eligibility gate.</li>`,
    `<li><b>Review queue</b><br>${flagged.length} flagged candidates and ${lowConfidence.length} low-confidence candidates in the visible shortlist.</li>`
  ].join("");
}
function renderInterviewKit() {
  if (!packets.length) return;
  const p = packets[selectedIndex] || packets[0];
  const ev = p.evidence, weak = weakestFactor(p), risks = p.score_breakdown.risk_flags || [];
  const retrieval = (ev.career_retrieval_terms || ev.vector_terms || ["search/retrieval evidence"]).slice(0, 2).join(", ");
  $("interviewKit").innerHTML = [
    `<li><b>Technical depth</b><br>Ask ${esc(p.candidate_id)} to walk through a production ranking, retrieval, or recommendation system they shipped, including evaluation and failure modes.</li>`,
    `<li><b>Evidence validation</b><br>Probe the specific profile evidence around ${esc(retrieval || "the strongest matching terms")} and ask for architecture-level details.</li>`,
    `<li><b>Risk/weak area</b><br>Explore ${esc(weak[0].replaceAll("_", " "))}; current score is ${scoreLabel(weak[1])}. ${risks.length ? "Also verify: " + esc(risks.join(", ")) + "." : "No explicit risk flags in the current packet."}</li>`
  ].join("");
}
function renderBoundaryReview(data) {
  const comparisons = data.v2.boundary_review.comparisons || [];
  const windows = data.v2.boundary_review.windows || [];
  const comparisonItems = comparisons.map(c => `<li><b>#${esc(c.left_rank)} vs #${esc(c.right_rank)}</b><br>${esc(c.recommendation)}</li>`);
  const windowItems = windows.map(w => `<li><b>${esc(w.name.replaceAll("_", " "))}</b><br>${w.candidates.map(c => "#" + c.rank + " " + c.candidate_id).join(", ")}</li>`);
  $("boundaryReview").innerHTML = [...comparisonItems, ...windowItems].slice(0, 5).join("") || "<li>No boundary rows available for the selected top N.</li>";
}
function renderTrapExamples(data) {
  const examples = data.v2.trap_examples || [];
  $("trapExamples").innerHTML = examples.map(ex => `<li><b>#${esc(ex.rank)} ${esc(ex.candidate_id)}</b><br>${esc(ex.reason)}<br>${esc((ex.evidence_terms || []).join(", "))}</li>`).join("") || "<li>No trap examples found in the current analysis window.</li>";
}
function renderUniversalProof(data) {
  const job = data.job;
  $("universalProof").innerHTML = [
    `<li><b>Current scorecard</b><br>${esc(job.id)} is loaded from YAML and validated against the universal factor model.</li>`,
    `<li><b>Category defaults</b><br>${esc(job.category_label || job.category)} supplies core signals, evidence priorities, and common risks.</li>`,
    `<li><b>Analysis depth</b><br>${esc(data.v2.analysis_rows)} ranked candidates inspected for shortlist, boundaries, traps, and interview workflow.</li>`
  ].join("");
}
function renderProductModules(data) {
  renderRoleIntel(data);
  renderCompare();
  renderTrustLayer(data);
  renderInterviewKit();
  renderBoundaryReview(data);
  renderTrapExamples(data);
  renderUniversalProof(data);
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
    const evidence = ev.career_retrieval_terms.slice(0, 3).join(", ") || ev.vector_terms.slice(0, 2).join(", ");
    return `<tr data-candidate="${esc(p.candidate_id)}" data-idx="${idx}">
      <td><b>#${p.rank}</b><br><span class="chip chip-ok ts-score">${p.score}</span></td>
      <td><b>${esc(p.candidate_id)}</b><br>${esc(ev.title)}<br><small>${esc(ev.years)} yrs · ${esc(ev.location)}</small></td>
      <td>${sc.top10_eligible ? '<span class="chip chip-ok">eligible</span>' : '<span class="chip chip-high">review</span>'}<br>conf ${Number(sc.confidence).toFixed(2)}</td>
      <td>${esc(evidence)}</td>
      <td><span class="chip ${sc.risk_flags.length ? 'chip-crit' : 'chip-ok'}">${sc.risk_flags.length ? sc.risk_flags.length + " flags" : "clear"}</span></td>
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
  const p = packets[idx];
  document.querySelectorAll("#results tr").forEach(r => r.classList.toggle("selected", r.dataset.candidate === p.candidate_id));
  const ev = p.evidence, sc = p.score_breakdown;
  $("detail").innerHTML = `<h3>#${p.rank} ${esc(p.candidate_id)}</h3>
    <div class="ts-sub">${esc(ev.title)} · ${esc(ev.years)} years · ${esc(ev.location)} · score ${esc(p.score)}</div>
    <p class="ts-reason">${esc(p.reasoning)}</p>
    <div class="ts-factors">
      ${factor("Technical", sc.technical_evidence)}
      ${factor("Career", sc.career_fit)}
      ${factor("Seniority", sc.seniority)}
      ${factor("Logistics", sc.logistics)}
      ${factor("Behavior", sc.behavioral)}
      ${factor("Trust", sc.trust)}
      ${factor("Confidence", sc.confidence)}
    </div>
    <div class="ts-evidence">
      <div><b>Career retrieval/ranking:</b> ${terms(ev.career_retrieval_terms)}</div>
      <div><b>Production:</b> ${terms(ev.career_production_terms)}</div>
      <div><b>Vector/search tooling:</b> ${terms(ev.vector_terms)}</div>
      <div><b>Evaluation:</b> ${terms(ev.eval_terms)}</div>
      <div><b>Risk flags:</b> ${terms(sc.risk_flags)}</div>
    </div>`;
  renderInterviewKit();
}
async function runRanker() {
  const btn = $("runBtn");
  btn.disabled = true;
  btn.classList.add("is-running");
  btn.textContent = "Generating...";
  setControlsDisabled(true);
  startRunningStatus();
  $("results").innerHTML = "";
  $("detail").textContent = "Preparing evidence packets.";
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
    lastData = data;
    packets = data.rows;
    allPackets = data.v2.analysis_packets || data.rows;
    stopRunningStatus();
    $("status").innerHTML = `<strong>Completed.</strong> Ranked shortlist generated from the selected candidate file in ${data.elapsed_seconds.toFixed(2)}s. <span class="ts-downloads">
      <a href="/download/ui_submission.csv">CSV</a>
      <a href="/download/ui_factor_scores.csv">Factors</a>
      <a href="/download/ui_evidence_packets.jsonl">Evidence</a>
      <a href="/download/ui_risk_report.csv">Risk</a>
    </span>`;
    renderMetrics(data);
    renderProductModules(data);
    renderRows();
  } catch (err) {
    stopRunningStatus();
    $("status").innerHTML = `<span style="color:#FA4D56;font-weight:700">${esc(err.message)}</span>`;
  } finally {
    btn.disabled = false;
    btn.classList.remove("is-running");
    btn.textContent = "Generate Shortlist";
    setControlsDisabled(false);
  }
}
$("runBtn").addEventListener("click", runRanker);
$("searchBox").addEventListener("input", renderRows);
$("riskFilter").addEventListener("change", renderRows);
$("sortBy").addEventListener("change", renderRows);
$("compareLeft").addEventListener("change", renderCompare);
$("compareRight").addEventListener("change", renderCompare);
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

    def _render_index(self) -> bytes:
        html = (
            INDEX_HTML.replace("__DEFAULT_CANDIDATES__", DEFAULT_CANDIDATES)
            .replace("__DEFAULT_JOB_SPEC__", DEFAULT_JOB_SPEC)
            .replace("__PRODUCT_TAGLINE__", PRODUCT_TAGLINE)
            .replace("__FONT_LINK__", HELIX_FONT_LINK)
        )
        return html.encode("utf-8")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            # Canonical product is now TalentSignal Studio (python studio.py).
            moved = ("<!doctype html><meta charset=utf-8><title>TalentSignal</title>"
                     "<body style='margin:0;background:#07070B;color:#F5F6FC;font:16px/1.6 system-ui;"
                     "display:grid;place-items:center;height:100vh;text-align:center'>"
                     "<div><h1 style='font-size:30px;font-weight:800'>TalentSignal</h1>"
                     "<p style='color:#878DAB'>The product UI is now <b>Studio</b> — run "
                     "<code style='color:#67E8F9'>python studio.py</code> and open "
                     "<a style='color:#67E8F9' href='http://127.0.0.1:8888'>127.0.0.1:8888</a>.</p></div></body>")
            self._send(HTTPStatus.OK, moved, "text/html; charset=utf-8")
            return
        if parsed.path == "/assets/helix-theme.css":
            if not HELIX_THEME_CSS.exists():
                self._json(HTTPStatus.NOT_FOUND, {"error": "helix theme.css not found"})
                return
            self._send(HTTPStatus.OK, HELIX_THEME_CSS.read_bytes(), "text/css; charset=utf-8")
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

    def _rank_hybrid(self, candidates_path, job, analysis_n):
        """Rank a (small) sample with the hybrid engine, live-embedding the
        sample and the JD's requirements. Intended for the sandbox/demo path on
        <=~100 candidates; the full 100K run uses the precomputed index instead.
        """
        from talentsignal import artifacts
        from talentsignal.io import iter_candidates
        from talentsignal.ranking import score_pool_hybrid, _rows_from_scored
        records = list(iter_candidates(candidates_path))
        req_emb = cand_index = None
        try:
            import os
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
            texts = [artifacts.evidence_text_of(c) for c in records]
            ids = [c["candidate_id"] for c in records]
            emb = model.encode(texts, batch_size=128, convert_to_numpy=True, normalize_embeddings=True)
            cand_index = ({cid: i for i, cid in enumerate(ids)}, emb)
            req_texts = [r.text for r in getattr(job, "requirements", ()) or ()]
            if req_texts:
                req_emb = model.encode(req_texts, convert_to_numpy=True, normalize_embeddings=True)
        except Exception:
            # No model available -> hybrid degrades to lexical-only, still works.
            cand_index = None
        scored = score_pool_hybrid(records, job, candidate_embeddings=cand_index, req_embeddings=req_emb)
        return _rows_from_scored(scored, job, analysis_n), scored

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
            jd_text = (payload.get("jd_text") or "").strip()
            engine = (payload.get("engine") or "spine").lower()
            top_n = int(payload.get("top_n") or 100)
            if top_n < 1 or top_n > 100:
                raise ValueError("top_n must be between 1 and 100")
            if not Path(candidates_path).exists():
                raise ValueError(f"candidate file not found: {candidates_path}")
            start = time.perf_counter()
            # JD: free text (any role, no YAML needed) OR a structured spec file.
            if jd_text:
                from talentsignal.jd_parser import job_spec_from_jd_text
                job = job_spec_from_jd_text(
                    jd_text, job_id=payload.get("job_id") or "ingested_jd",
                    category=payload.get("category") or "ai_ml_search_ranking")
            else:
                if not Path(job_spec_path).exists():
                    raise ValueError(f"job spec not found: {job_spec_path}")
                job = load_job_spec(job_spec_path)
            analysis_n = 110 if top_n == 100 else max(top_n, min(110, top_n + 10))
            if engine == "hybrid":
                analysis_rows, scored_pool = self._rank_hybrid(candidates_path, job, analysis_n)
            else:
                analysis_rows, scored_pool = rank_candidates_with_pool(candidates_path, job, top_n=analysis_n)
            rows = analysis_rows[:top_n]
            UI_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            submission = UI_OUTPUT_DIR / "ui_submission.csv"
            factors = UI_OUTPUT_DIR / "ui_factor_scores.csv"
            evidence = UI_OUTPUT_DIR / "ui_evidence_packets.jsonl"
            risk = UI_OUTPUT_DIR / "ui_risk_report.csv"
            summary = UI_OUTPUT_DIR / "ui_risk_summary.json"
            write_submission(rows, submission)
            write_factor_scores(rows, factors)
            write_evidence_packets(analysis_rows, evidence)
            write_risk_report(rows, risk)
            write_risk_summary(rows, summary)
            packets = []
            with evidence.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        packets.append(json.loads(line))
            visible_packets = packets[:top_n]
            top10 = visible_packets[:10]
            top_compare = compare_by_rank(packets, 1, 2)
            trap_examples = rejected_trap_examples_from_scored(scored_pool, limit=5) or rejected_trap_examples(packets, limit=5)
            response = {
                "candidates_path": candidates_path,
                "job_spec": job_spec_path,
                "elapsed_seconds": round(time.perf_counter() - start, 3),
                "job": {
                    "id": job.id,
                    "title": job.title,
                    "category": job.category,
                    "category_label": job.category_label,
                    "category_core_signals": list(job.category_core_signals),
                    "category_evidence_priorities": list(job.category_evidence_priorities),
                    "category_common_risks": list(job.category_common_risks),
                    "preferred_min_years": job.preferred_min_years,
                    "preferred_max_years": job.preferred_max_years,
                    "strongest_min_years": job.strongest_min_years,
                    "strongest_max_years": job.strongest_max_years,
                    "preferred_locations": list(job.preferred_locations),
                    "country_preferred": job.country_preferred,
                    "must_have": list(job.must_have),
                    "nice_to_have": list(job.nice_to_have),
                    "disqualifiers": list(job.disqualifiers),
                    "weights": job.weights,
                },
                "rows": visible_packets,
                "v2": {
                    "analysis_rows": len(packets),
                    "analysis_packets": packets,
                    "top_compare": top_compare,
                    "boundary_review": boundary_windows(packets)[0],
                    "trap_examples": trap_examples,
                    "interview_kits": build_interview_kits(visible_packets, job, limit=10),
                },
                "summary": {
                    "top10_eligible_count": sum(1 for p in top10 if p["score_breakdown"]["top10_eligible"]),
                    "risk_flagged_count": sum(1 for p in visible_packets if p["score_breakdown"]["risk_flags"]),
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

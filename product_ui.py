#!/usr/bin/env python3
"""TalentSignal Product UI — the wow surface.

Drop in ANY job description (paste or file) and ANY set of resumes/candidates in
ANY format (PDF, DOCX, TXT, CSV, JSON, LinkedIn, or pasted text), and get a live,
ranked, explainable shortlist: per-candidate fit factors, which JD requirement
matched which evidence, risk/honeypot flags with the contradicting facts, and
grounded reasoning. Export to CSV.

Self-contained: stdlib http.server, serves a single-page app, and runs the same
talentsignal.api facade + ingest layer behind the scenes (no logic duplication).

Run:
  python product_ui.py --host 127.0.0.1 --port 8800
"""
from __future__ import annotations

import argparse
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent / "src"))

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>TalentSignal — Universal Candidate Intelligence</title>
<style>
:root{--bg:#0b1020;--panel:#141a2e;--panel2:#1b2440;--ink:#e8ecf6;--mut:#9aa6c4;
--acc:#5b8cff;--good:#39d98a;--warn:#ffb454;--bad:#ff6b6b;--line:#26304f;}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;
background:linear-gradient(160deg,#070b16,#0b1020);color:var(--ink)}
header{padding:22px 28px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:14px}
header h1{font-size:19px;margin:0;letter-spacing:.3px}
header .tag{color:var(--mut);font-size:13px}
.badge{margin-left:auto;font-size:12px;color:var(--good);border:1px solid var(--line);
padding:4px 10px;border-radius:20px}
.wrap{display:grid;grid-template-columns:380px 1fr;gap:0;min-height:calc(100vh - 66px)}
.left{padding:22px;border-right:1px solid var(--line);background:var(--panel)}
.right{padding:22px;overflow:auto}
label{display:block;font-size:12px;color:var(--mut);margin:14px 0 6px;text-transform:uppercase;letter-spacing:.5px}
textarea,input,select{width:100%;background:var(--panel2);border:1px solid var(--line);
color:var(--ink);border-radius:10px;padding:11px;font:inherit;resize:vertical}
textarea{min-height:120px}
.drop{border:1.5px dashed var(--line);border-radius:12px;padding:18px;text-align:center;
color:var(--mut);background:var(--panel2);cursor:pointer;transition:.2s}
.drop.hi{border-color:var(--acc);color:var(--ink)}
.row{display:flex;gap:10px}.row>*{flex:1}
button{margin-top:18px;width:100%;background:linear-gradient(90deg,#5b8cff,#7c5bff);
border:0;color:#fff;font-weight:600;padding:13px;border-radius:11px;cursor:pointer;font-size:15px}
button:disabled{opacity:.5;cursor:wait}
.files{margin-top:10px;font-size:13px;color:var(--mut)}
.files span{display:inline-block;background:var(--panel2);border:1px solid var(--line);
border-radius:14px;padding:3px 10px;margin:3px 4px 0 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:14px}
.card.t1{border-left:3px solid var(--good)}.card.t2{border-left:3px solid var(--acc)}
.card.t3{border-left:3px solid var(--warn)}
.crank{display:flex;align-items:baseline;gap:12px}
.crank .r{font-size:24px;font-weight:700;color:var(--acc);min-width:42px}
.crank .nm{font-size:17px;font-weight:600}.crank .sc{margin-left:auto;color:var(--mut);font-variant-numeric:tabular-nums}
.meta{color:var(--mut);font-size:13px;margin:2px 0 10px 54px}
.reason{margin:0 0 12px 54px}
.factors{display:flex;gap:6px;margin:0 0 10px 54px;flex-wrap:wrap}
.bar{flex:1;min-width:90px}.bar .lb{font-size:10px;color:var(--mut);text-transform:uppercase}
.bar .tr{height:6px;background:var(--panel2);border-radius:4px;overflow:hidden;margin-top:3px}
.bar .fl{height:100%;background:linear-gradient(90deg,#5b8cff,#39d98a)}
.flags{margin:6px 0 0 54px}.flag{display:inline-block;font-size:12px;color:#ffd9d9;
background:rgba(255,107,107,.12);border:1px solid rgba(255,107,107,.3);border-radius:8px;padding:3px 9px;margin:3px 4px 0 0}
.reqs{margin:8px 0 0 54px;font-size:12.5px;color:var(--mut)}
.reqs .m{color:var(--good)}
.empty{color:var(--mut);text-align:center;margin-top:80px}
.toolbar{display:flex;gap:10px;margin-bottom:16px;align-items:center}
.toolbar .stat{color:var(--mut);font-size:13px}.toolbar a{margin-left:auto;color:var(--acc);text-decoration:none}
.spin{display:inline-block;width:16px;height:16px;border:2px solid var(--line);border-top-color:var(--acc);
border-radius:50%;animation:s .7s linear infinite;vertical-align:-3px}@keyframes s{to{transform:rotate(360deg)}}
</style></head><body>
<header><h1>TalentSignal</h1><span class="tag">Universal candidate intelligence — any JD, any resume, any format</span>
<span class="badge">live engine</span></header>
<div class="wrap">
  <div class="left">
    <label>Job description (paste, any role)</label>
    <textarea id="jd" placeholder="Senior AI Engineer. Must have production embeddings/retrieval and ranking experience, evaluation frameworks (NDCG/MAP). 5-9 years. Pune/Noida...">Senior AI Engineer — Founding Team

We need someone who has shipped retrieval and ranking systems to real users. You must have production experience with embeddings-based retrieval and vector/hybrid search, strong Python, and you must have designed evaluation frameworks for ranking (NDCG, MRR, MAP, A/B testing).

We will not move forward with: pure research with no production deployment; careers entirely at services companies with no product evidence; computer-vision-only specialists with no NLP/retrieval.

5-9 years. Pune or Noida.</textarea>
    <div class="row"><div><label>Category</label>
      <select id="cat"><option value="ai_ml_search_ranking">AI / ML / Search</option>
      <option value="sales_gtm">Sales / GTM</option><option value="data_analytics">Data / Analytics</option>
      <option value="backend_engineering">Backend</option><option value="product_management">Product</option>
      <option value="design_product">Design</option></select></div>
      <div><label>Top N</label><input id="topn" type="number" value="10" min="1" max="100"/></div></div>
    <label>Candidates — drop resumes / files (pdf, docx, txt, csv, json) or paste below</label>
    <div class="drop" id="drop">⬇ Drag &amp; drop resume files here, or click to choose</div>
    <input id="file" type="file" multiple style="display:none"/>
    <div class="files" id="files"></div>
    <textarea id="paste" placeholder="...or paste one or more resumes / a JSON array of candidates here"></textarea>
    <button id="go">Rank candidates</button>
  </div>
  <div class="right">
    <div class="toolbar"><span class="stat" id="stat">Drop a JD and candidates, then rank.</span>
      <a id="dl" href="#" style="display:none">⬇ Export CSV</a></div>
    <div id="out"><div class="empty">No results yet — your ranked shortlist will appear here.</div></div>
  </div>
</div>
<script>
const $=id=>document.getElementById(id);
let pendingFiles=[];
const drop=$('drop'),file=$('file');
drop.onclick=()=>file.click();
['dragover','dragenter'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.add('hi')}));
['dragleave','drop'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.remove('hi')}));
drop.addEventListener('drop',ev=>{addFiles(ev.dataTransfer.files)});
file.onchange=()=>addFiles(file.files);
function addFiles(fl){for(const f of fl)pendingFiles.push(f);renderFiles()}
function renderFiles(){$('files').innerHTML=pendingFiles.map(f=>`<span>${f.name}</span>`).join('')}
async function readFiles(){
  const out=[];
  for(const f of pendingFiles){
    const ext=f.name.split('.').pop().toLowerCase();
    if(['txt','csv','json','jsonl','md'].includes(ext)){out.push({name:f.name,ext,text:await f.text()});}
    else{const b=await f.arrayBuffer();out.push({name:f.name,ext,b64:btoa(String.fromCharCode(...new Uint8Array(b)))});}
  }
  return out;
}
let lastCSV='';
$('go').onclick=async()=>{
  const btn=$('go');btn.disabled=true;
  $('stat').innerHTML='<span class="spin"></span> Ingesting & ranking…';
  try{
    const files=await readFiles();
    const body={jd:$('jd').value,category:$('cat').value,top_n:+$('topn').value,
      files, paste:$('paste').value};
    const r=await fetch('/api/rank',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await r.json();
    if(data.error){$('stat').textContent='Error: '+data.error;btn.disabled=false;return;}
    render(data);
  }catch(e){$('stat').textContent='Error: '+e.message;}
  btn.disabled=false;
};
function bar(lb,v){return `<div class="bar"><div class="lb">${lb}</div><div class="tr"><div class="fl" style="width:${Math.round(v*100)}%"></div></div></div>`;}
function render(data){
  $('stat').textContent=`${data.candidate_count} candidates · ${data.ranked.length} shown · ${data.job_title} · engine: ${data.engine} · ${data.elapsed_seconds}s`;
  lastCSV='candidate_id,rank,score,reasoning\\n'+data.ranked.map(c=>`${c.candidate_id},${c.rank},${c.score.toFixed(6)},"${(c.reasoning||'').replace(/"/g,'""')}"`).join('\\n');
  $('dl').style.display='inline';$('dl').onclick=()=>{const b=new Blob([lastCSV],{type:'text/csv'});const u=URL.createObjectURL(b);const a=document.createElement('a');a.href=u;a.download='shortlist.csv';a.click();};
  $('out').innerHTML=data.ranked.map(c=>{
    const f=c.factors||{};const tier=c.rank<=3?'t1':c.rank<=8?'t2':'t3';
    const flags=(c.risk_flags||[]).map(x=>`<span class="flag" title="${(x.detail||'').replace(/"/g,'&quot;')}">${x.code}</span>`).join('');
    const reqs=(c.requirement_matches||[]).slice(0,3).map(m=>`<span class="m">${(m.matched_keywords||[]).join(', ')||m.requirement.slice(0,40)}</span>`).join(' · ');
    return `<div class="card ${tier}">
      <div class="crank"><div class="r">#${c.rank}</div><div class="nm">${c.title||c.candidate_id}</div><div class="sc">${c.score.toFixed(3)}</div></div>
      <div class="meta">${c.candidate_id} · ${(c.years||0).toFixed(1)} yrs · ${c.location||'—'} · confidence ${(c.confidence||0).toFixed(2)}</div>
      <div class="reason">${c.reasoning||''}</div>
      <div class="factors">${bar('tech',f.technical_evidence||0)}${bar('career',f.career_fit||0)}${bar('senior',f.seniority||0)}${bar('behav',f.behavioral||0)}${bar('trust',f.trust||0)}${bar('semantic',f.semantic_fit||0)}</div>
      ${reqs?`<div class="reqs">matched: ${reqs}</div>`:''}
      ${flags?`<div class="flags">${flags}</div>`:''}
    </div>`;
  }).join('');
}
</script></body></html>"""


_EMBEDDER = {"model": None, "tried": False}


def _get_embedder():
    """Return a cached callable(list[str]) -> np.ndarray, or None if sentence-
    transformers isn't available. Lets the UI use the hybrid engine on small
    samples for best quality, with a clean spine fallback."""
    if _EMBEDDER["tried"]:
        return _EMBEDDER["model"]
    _EMBEDDER["tried"] = True
    try:
        import os
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        _EMBEDDER["model"] = lambda texts: m.encode(texts, convert_to_numpy=True,
                                                    normalize_embeddings=True)
    except Exception:  # noqa: BLE001 - no model -> spine fallback
        _EMBEDDER["model"] = None
    return _EMBEDDER["model"]


def _ingest_inputs(files, paste):
    """Turn UI inputs (uploaded files + pasted text) into candidate records."""
    import base64
    import tempfile
    from talentsignal.ingest import ingest
    records = []
    for f in files or []:
        ext = (f.get("ext") or "").lower()
        try:
            if "text" in f:
                fmt = {"jsonl": "json", "md": "text"}.get(ext, ext if ext in ("csv", "json", "txt") else "text")
                fmt = "text" if fmt == "txt" else fmt
                records.extend(ingest(f["text"], fmt=fmt))
            elif "b64" in f:
                raw = base64.b64decode(f["b64"])
                with tempfile.NamedTemporaryFile(suffix="." + ext, delete=False) as tmp:
                    tmp.write(raw)
                    path = tmp.name
                records.extend(ingest(path))
        except Exception as exc:  # noqa: BLE001 - one bad file shouldn't kill the batch
            records.append({"candidate_id": "CAND_0000000", "profile": {"summary": f"(parse failed: {exc})"},
                            "career_history": [], "skills": [], "redrob_signals": {}})
    if paste and paste.strip():
        txt = paste.strip()
        if txt[0] in "[{":
            try:
                records.extend(ingest(txt, fmt="json"))
            except Exception:  # noqa: BLE001
                records.extend(ingest(txt, fmt="text"))
        else:
            # Multiple pasted resumes are separated by a blank line (>=2 newlines).
            # Split so each becomes its own candidate; a single resume stays whole.
            import re
            blocks = [b.strip() for b in re.split(r"\n\s*\n\s*\n+|\n\s*\n(?=[A-Z])", txt) if b.strip()]
            # Heuristic: only split if blocks look like separate resumes (each has
            # enough content); otherwise treat the whole paste as one resume.
            if len(blocks) > 1 and all(len(b) > 40 for b in blocks):
                for b in blocks:
                    records.extend(ingest(b, fmt="text"))
            else:
                records.extend(ingest(txt, fmt="text"))
    return records


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, status, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else (json.dumps(body).encode() if ctype == "application/json" else body.encode())
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if urlparse(self.path).path in ("/", "/index.html"):
            self._send(HTTPStatus.OK, PAGE, "text/html; charset=utf-8")
        else:
            self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self):
        if urlparse(self.path).path != "/api/rank":
            self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            from talentsignal.api import rank
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            records = _ingest_inputs(body.get("files"), body.get("paste"))
            if not records:
                self._send(HTTPStatus.OK, {"error": "no candidates parsed from the provided files/text"})
                return
            # Small samples -> use the best (hybrid) engine with a live embedder if
            # available; fall back to the zero-dependency spine engine otherwise.
            embedder = _get_embedder() if len(records) <= 200 else None
            engine = "hybrid" if embedder else "spine"
            res = rank(body.get("jd", ""), records, top_n=int(body.get("top_n", 10)),
                       engine=engine, embedder=embedder,
                       category=body.get("category", "ai_ml_search_ranking"))
            self._send(HTTPStatus.OK, res.to_dict())
        except Exception as exc:  # noqa: BLE001
            self._send(HTTPStatus.OK, {"error": f"{type(exc).__name__}: {exc}"})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8800)
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"TalentSignal Product UI → http://{args.host}:{args.port}")
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

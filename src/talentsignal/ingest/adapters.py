"""Built-in ingest adapters: JSON/JSONL, CSV, text/paste, PDF, DOCX, LinkedIn.

Each adapter turns one input format into canonical candidate records. Heavy or
optional dependencies (pypdf, python-docx) are imported lazily inside the adapter
so importing the ingest layer stays cheap and a missing optional dep only fails
the format that needs it.
"""
from __future__ import annotations

import csv as _csv
import json
import re
from pathlib import Path
from typing import Any

from .model import Candidate, canonical_record, normalize_record
from .registry import register_adapter
from .resume_parser import parse_resume_text


# --- JSON / JSONL (the challenge shape, and generic profile json) --------------

@register_adapter("json", extensions=[".json", ".jsonl"])
def json_adapter(source: Any, **opts) -> list[dict[str, Any]]:
    if isinstance(source, dict):
        return [normalize_record(dict(source))]
    text = _read_text(source)
    text = text.strip()
    records: list[dict[str, Any]] = []
    if not text:
        return records
    if text[0] == "[":
        for rec in json.loads(text):
            records.append(normalize_record(rec))
    else:
        # JSONL (one object per line) — or a single object
        lines = [ln for ln in text.splitlines() if ln.strip()]
        if len(lines) == 1 and text[0] == "{":
            records.append(normalize_record(json.loads(text)))
        else:
            for ln in lines:
                records.append(normalize_record(json.loads(ln)))
    return records


# --- CSV (one candidate per row, column-mapped) --------------------------------

# default header aliases -> canonical fields
_CSV_MAP = {
    "name": "name", "full_name": "name", "candidate": "name",
    "title": "current_title", "current_title": "current_title", "headline": "headline",
    "company": "current_company", "current_company": "current_company",
    "summary": "summary", "about": "summary", "bio": "summary",
    "location": "location", "city": "location", "country": "country",
    "years": "years_of_experience", "experience": "years_of_experience",
    "years_of_experience": "years_of_experience",
    "skills": "skills", "industry": "current_industry",
}


@register_adapter("csv", extensions=[".csv", ".tsv"])
def csv_adapter(source: Any, **opts) -> list[dict[str, Any]]:
    text = _read_text(source)
    delim = "\t" if (str(source).endswith(".tsv")) else ","
    reader = _csv.DictReader(text.splitlines(), delimiter=delim)
    out = []
    for row in reader:
        c = Candidate(source="csv")
        for raw_key, val in row.items():
            if raw_key is None:
                continue
            key = _CSV_MAP.get(raw_key.strip().lower())
            if not key or not val:
                continue
            if key == "years_of_experience":
                c.years_of_experience = _num(val)
            elif key == "skills":
                c.skills = [{"name": s.strip(), "proficiency": "intermediate",
                             "endorsements": 0, "duration_months": 12}
                            for s in re.split(r"[;,|]", val) if s.strip()]
            else:
                setattr(c, key, val.strip())
        out.append(c.to_record())
    return out


# --- Plain text / pasted resume ------------------------------------------------

@register_adapter("text", extensions=[".txt"])
def text_adapter(source: Any, *, use_llm: bool = False, **opts) -> list[dict[str, Any]]:
    text = _read_text(source)
    if not text.strip():
        return []
    cand = parse_resume_text(text, use_llm=use_llm)
    return [cand.to_record()]


# --- PDF (pypdf) ---------------------------------------------------------------

@register_adapter("pdf", extensions=[".pdf"])
def pdf_adapter(source: Any, *, use_llm: bool = False, **opts) -> list[dict[str, Any]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pypdf required for PDF ingest: pip install pypdf") from exc
    reader = PdfReader(str(source))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    cand = parse_resume_text(text, use_llm=use_llm)
    cand.source = "pdf"
    return [cand.to_record()]


# --- DOCX (python-docx) --------------------------------------------------------

@register_adapter("docx", extensions=[".docx"])
def docx_adapter(source: Any, *, use_llm: bool = False, **opts) -> list[dict[str, Any]]:
    try:
        import docx  # python-docx
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("python-docx required for DOCX ingest: pip install python-docx") from exc
    document = docx.Document(str(source))
    text = "\n".join(p.text for p in document.paragraphs)
    cand = parse_resume_text(text, use_llm=use_llm)
    cand.source = "docx"
    return [cand.to_record()]


# --- LinkedIn export (their archive CSV/JSON) ----------------------------------

@register_adapter("linkedin", extensions=[])
def linkedin_adapter(source: Any, **opts) -> list[dict[str, Any]]:
    """Map a LinkedIn 'Profile.csv'/positions export into a candidate.

    LinkedIn data export is a folder of CSVs (Profile.csv, Positions.csv,
    Skills.csv). We accept a dict already keyed by those, or a single CSV path
    that looks like a LinkedIn profile export.
    """
    if isinstance(source, dict):
        data = source
    else:
        # treat as a Profile.csv-style single file
        return csv_adapter(source, **opts)
    c = Candidate(source="linkedin")
    prof = data.get("profile", {})
    c.name = prof.get("First Name", "") + " " + prof.get("Last Name", "")
    c.headline = prof.get("Headline", "")
    c.summary = prof.get("Summary", "")
    c.location = prof.get("Geo Location", "")
    for pos in data.get("positions", []):
        c.career.append({
            "company": pos.get("Company Name", ""),
            "title": pos.get("Title", ""),
            "description": pos.get("Description", ""),
            "start_date": pos.get("Started On", ""),
            "end_date": pos.get("Finished On") or None,
            "is_current": not pos.get("Finished On"),
            "duration_months": 0,
        })
    c.skills = [{"name": s.get("Name", ""), "proficiency": "intermediate",
                 "endorsements": 0, "duration_months": 12}
                for s in data.get("skills", [])]
    return [c.to_record()]


# --- helpers -------------------------------------------------------------------

def _read_text(source: Any) -> str:
    if isinstance(source, (bytes, bytearray)):
        return source.decode("utf-8", "ignore")
    p = Path(str(source))
    try:
        if p.exists() and p.is_file():
            return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        pass
    return str(source)  # treat as inline content


def _num(v: Any) -> float:
    m = re.search(r"\d+(?:\.\d+)?", str(v))
    return float(m.group()) if m else 0.0

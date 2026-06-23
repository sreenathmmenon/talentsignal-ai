"""Resume text -> structured Candidate. Hybrid: local default + optional LLM.

Local mode (default): deterministic, offline, free, reproducible — section
detection + heuristics. Good enough to rank, and it never needs the network
(so it is consistent with the hackathon's no-network ranking constraint and
costs nothing).

LLM mode (use_llm=True): hand the raw resume text to Claude and get back a clean
structured profile — far more robust on messy real-world layouts. This is an
INGEST-time call only; ranking stays offline. Falls back to local mode if the
LLM is unavailable, so it always returns something.

Confidence reflects how much structure we recovered, so downstream surfaces can
flag low-confidence parses for human review.
"""
from __future__ import annotations

import re
from .model import Candidate, parse_duration_months

# Section headers we recognize (case-insensitive, line-leading).
_SECTIONS = {
    "experience": r"(work\s+experience|experience|employment|professional\s+experience|career)",
    "education": r"(education|academic)",
    "skills": r"(skills|technical\s+skills|core\s+competencies|technologies)",
    "summary": r"(summary|profile|objective|about)",
}
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
_YEARS_EXP = re.compile(r"(\d{1,2}(?:\.\d)?)\+?\s*years?", re.IGNORECASE)
_DATE_RANGE = re.compile(
    r"(\b(?:19|20)\d{2}\b)\s*[-–to]+\s*((?:19|20)\d{2}\b|present|current)",
    re.IGNORECASE)
# common job-title-ish line: "Senior X Engineer at Company"
_TITLE_AT = re.compile(r"^(.{3,60}?)\s+(?:at|@|,)\s+(.{2,60})$")


def parse_resume_text(text: str, *, use_llm: bool = False) -> Candidate:
    if use_llm:
        cand = _parse_with_llm(text)
        if cand is not None:
            return cand
        # fall through to local on failure
    return _parse_local(text)


# --- local deterministic parser ------------------------------------------------

def _parse_local(text: str) -> Candidate:
    lines = [ln.rstrip() for ln in text.splitlines()]
    nonempty = [ln for ln in lines if ln.strip()]
    c = Candidate(source="resume:local", raw_text=text)

    # name: first non-empty line that isn't an email/phone/section header
    for ln in nonempty[:5]:
        if not _EMAIL.search(ln) and not _PHONE.search(ln) and not _is_section(ln) and len(ln.split()) <= 6:
            c.name = ln.strip()
            break

    # location/country from a contact line (often "City, Country" near the top)
    for ln in nonempty[:6]:
        loc = _extract_location(ln)
        if loc:
            c.location, c.country = loc
            break

    sections = _split_sections(lines)

    # summary
    c.summary = " ".join(sections.get("summary", [])).strip()[:1000]
    if not c.summary:
        # fall back to first paragraph
        c.summary = " ".join(nonempty[1:4])[:600]

    # stated years of experience
    m = _YEARS_EXP.search(text)
    if m:
        c.years_of_experience = float(m.group(1))

    # experience entries
    c.career = _parse_experience(sections.get("experience", []))
    if c.career:
        cur = c.career[0]
        c.current_title = cur.get("title", "")
        c.current_company = cur.get("company", "")
        if not c.years_of_experience:
            months = sum(int(j.get("duration_months") or 0) for j in c.career)
            c.years_of_experience = round(months / 12.0, 1)

    # education
    c.education = _parse_education(sections.get("education", []))

    # skills
    c.skills = _parse_skills(sections.get("skills", []))

    # confidence: how much structure did we recover?
    got = sum([bool(c.name), bool(c.summary), bool(c.career), bool(c.skills), bool(c.years_of_experience)])
    c.confidence = round(0.2 + 0.16 * got, 2)
    return c


_CITIES = ("Bangalore", "Bengaluru", "Pune", "Noida", "Delhi", "Gurgaon", "Gurugram",
           "Mumbai", "Hyderabad", "Chennai", "Kolkata", "Trivandrum", "Kochi", "Remote",
           "London", "Singapore", "Toronto", "Berlin", "New York", "San Francisco")
_COUNTRIES = ("India", "USA", "United States", "UK", "United Kingdom", "Canada",
              "Germany", "Singapore", "Australia")


def _extract_location(line: str) -> tuple[str, str] | None:
    found_city = next((c for c in _CITIES if re.search(rf"\b{re.escape(c)}\b", line)), "")
    found_country = next((c for c in _COUNTRIES if re.search(rf"\b{re.escape(c)}\b", line)), "")
    if found_city or found_country:
        if found_city and not found_country and found_city not in ("London", "Singapore", "Toronto", "Berlin"):
            found_country = "India" if found_city in _CITIES[:14] else ""
        return (found_city or found_country, found_country or "")
    return None


def _is_section(line: str) -> bool:
    low = line.strip().lower()
    return any(re.match(rf"^{pat}\b", low) for pat in _SECTIONS.values())


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    current = "summary"
    out[current] = []
    for ln in lines:
        low = ln.strip().lower()
        matched = None
        for name, pat in _SECTIONS.items():
            if re.match(rf"^{pat}\b[:\s]*$", low) or re.match(rf"^{pat}\b", low) and len(low) < 30:
                matched = name
                break
        if matched:
            current = matched
            out.setdefault(current, [])
            continue
        out.setdefault(current, []).append(ln)
    return out


def _parse_experience(lines: list[str]) -> list[dict]:
    jobs: list[dict] = []
    buf: list[str] = []

    def flush(header: str, body: list[str]):
        title, company = "", ""
        mt = _TITLE_AT.match(header.strip())
        if mt:
            title, company = mt.group(1).strip(), mt.group(2).strip()
        else:
            title = header.strip()[:60]
        start = end = None
        dm = _DATE_RANGE.search(header + " " + " ".join(body[:1]))
        if dm:
            start, end_raw = dm.group(1), dm.group(2)
            end = None if end_raw.lower() in ("present", "current") else end_raw
        months = parse_duration_months(start or "", end) if start else 0
        jobs.append({
            "title": title, "company": company,
            "description": " ".join(body).strip()[:800],
            "start_date": (start + "-01") if start and len(start) == 4 else (start or ""),
            "end_date": (end + "-01") if end and len(end) == 4 else end,
            "is_current": end is None and start is not None,
            "duration_months": months,
            "industry": "", "company_size": "51-200",
        })

    header = None
    for ln in lines:
        if not ln.strip():
            continue
        # a line with a date range or 'Title at Company' looks like a new entry header
        if _DATE_RANGE.search(ln) or _TITLE_AT.match(ln.strip()):
            if header is not None:
                flush(header, buf)
            header, buf = ln, []
        else:
            buf.append(ln)
    if header is not None:
        flush(header, buf)
    return jobs[:10]


def _parse_education(lines: list[str]) -> list[dict]:
    edu = []
    for ln in lines:
        if not ln.strip():
            continue
        ym = re.search(r"((?:19|20)\d{2})", ln)
        edu.append({
            "institution": ln.strip()[:80],
            "degree": _guess_degree(ln),
            "field_of_study": "",
            "start_year": int(ym.group(1)) - 4 if ym else 2014,
            "end_year": int(ym.group(1)) if ym else 2018,
            "tier": "unknown",
        })
        if len(edu) >= 5:
            break
    return edu


def _guess_degree(line: str) -> str:
    for deg in ("ph.d", "phd", "m.tech", "mtech", "b.tech", "btech", "mba", "m.sc", "msc",
                "b.sc", "bsc", "bachelor", "master", "b.e", "m.e"):
        if deg in line.lower():
            return deg.upper()
    return ""


def _parse_skills(lines: list[str]) -> list[dict]:
    text = " ".join(lines)
    raw = re.split(r"[,;|••\n]+", text)
    skills = []
    seen = set()
    for s in raw:
        name = s.strip(" .-")
        if 2 <= len(name) <= 30 and name.lower() not in seen and not name.lower().startswith("skill"):
            seen.add(name.lower())
            skills.append({"name": name, "proficiency": "intermediate",
                           "endorsements": 0, "duration_months": 12})
        if len(skills) >= 30:
            break
    return skills


# --- LLM parser (optional, ingest-time only) -----------------------------------

def _parse_with_llm(text: str) -> Candidate | None:
    """Use Claude to structure a messy resume. Returns None if unavailable so the
    caller falls back to local parsing. Ranking never depends on this."""
    try:
        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        import anthropic  # optional dep
    except ImportError:
        return None
    try:
        import json as _json
        client = anthropic.Anthropic(api_key=api_key)
        prompt = (
            "Extract this resume into JSON with keys: name, summary, "
            "years_of_experience (number), current_title, current_company, location, "
            "country, career (list of {title, company, description, start_date, end_date, "
            "duration_months, is_current}), education (list), skills (list of {name, "
            "proficiency, duration_months}). Resume:\n\n" + text[:12000]
        )
        msg = client.messages.create(
            model="claude-opus-4-8", max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text
        data = _json.loads(re.search(r"\{.*\}", raw, re.DOTALL).group())
        c = Candidate(source="resume:llm", raw_text=text, confidence=0.9)
        c.name = data.get("name", "")
        c.summary = data.get("summary", "")
        c.years_of_experience = float(data.get("years_of_experience") or 0)
        c.current_title = data.get("current_title", "")
        c.current_company = data.get("current_company", "")
        c.location = data.get("location", "")
        c.country = data.get("country", "")
        c.career = data.get("career", []) or []
        c.education = data.get("education", []) or []
        c.skills = data.get("skills", []) or []
        return c
    except Exception:  # noqa: BLE001 - any failure -> fall back to local
        return None

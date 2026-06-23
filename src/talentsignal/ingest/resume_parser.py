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
    "experience": r"(work\s+experience|work\s+history|experience|employment|professional\s+experience|career)",
    "education": r"(education|academic)",
    "skills": r"(technical\s+skills|core\s+competencies|technologies|skills)",
    "summary": r"(summary|profile|objective|about)",
}

# A gazetteer of common tech skills, used as a fallback to recover skills that
# appear anywhere in the text when there's no clean SKILLS section. Conservative
# (only well-known multi-char tech terms) to avoid false positives.
_KNOWN_SKILLS = (
    "python", "typescript", "javascript", "java", "golang", "go", "rust", "c++", "scala",
    "react", "node.js", "node", "graphql", "apollo", "fastapi", "rest", "django", "flask",
    "kubernetes", "docker", "aws", "azure", "gcp", "openstack", "kafka", "rabbitmq", "terraform",
    "mongodb", "postgresql", "mysql", "mariadb", "redis", "elasticsearch", "opensearch",
    "llms", "llm", "rag", "ai agents", "agents", "mcp", "embeddings", "prompt engineering",
    "langchain", "langgraph", "crewai", "chromadb", "milvus", "pinecone", "qdrant", "faiss",
    "vector db", "vector search", "ollama", "watsonx", "openai", "anthropic", "claude", "gemini",
    "pytorch", "tensorflow", "scikit-learn", "xgboost", "lightgbm", "hugging face", "transformers",
    "ranking", "recommendation", "recommendation systems", "learning to rank", "ndcg", "semantic search",
    "reinforcement learning", "guardrails", "tool calling", "fine-tuning", "lora", "qlora", "peft",
    "ci/cd", "salesforce", "sentiment analysis", "distributed systems", "microservices",
)
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

    # experience entries — try the experience section, else scan all lines
    # (paragraph/terse resumes have no section headers).
    c.career = _parse_experience(sections.get("experience", []) or nonempty)
    if c.career:
        cur = c.career[0]
        c.current_title = cur.get("title", "")
        c.current_company = cur.get("company", "")
        if not c.years_of_experience:
            months = sum(int(j.get("duration_months") or 0) for j in c.career)
            c.years_of_experience = round(months / 12.0, 1)

    # Title fallback: infer from the summary/whole text when no career title parsed.
    if not c.current_title:
        c.current_title = _infer_title(text)

    # Career fallback: if nothing structured parsed but we clearly have a role +
    # experience (paragraph/terse resume), synthesize one role from the summary so
    # career-based matching has evidence instead of nothing.
    if not c.career and c.current_title:
        months = int((c.years_of_experience or 0) * 12)
        c.career = [{
            "title": c.current_title, "company": "",
            "description": (c.summary or text)[:800],
            "start_date": "", "end_date": None, "is_current": True,
            "duration_months": months, "industry": "", "company_size": "51-200",
        }]

    # education
    c.education = _parse_education(sections.get("education", []))

    # skills (section + inline + gazetteer fallback over the whole text)
    c.skills = _parse_skills(sections.get("skills", []), text)

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
    """Split into summary/experience/education/skills sections. A header is a short
    line that starts with a known section word (case-insensitive, ALL-CAPS ok),
    optionally followed by ':' — e.g. 'EXPERIENCE', 'Technical Skills:', 'WORK HISTORY'."""
    out: dict[str, list[str]] = {"summary": []}
    current = "summary"
    for ln in lines:
        stripped = ln.strip()
        low = stripped.lower().rstrip(":").strip()
        matched = None
        # a header line is short and IS (essentially) just the section word
        if len(stripped.split()) <= 3:
            for name, pat in _SECTIONS.items():
                if re.fullmatch(rf"{pat}\b", low):
                    matched = name
                    break
        if matched:
            current = matched
            out.setdefault(current, [])
            continue
        out.setdefault(current, []).append(ln)
    return out


# Words that signal a line is a job title (used to detect entry headers when
# there's no "Title at Company" or date on the line).
_TITLE_WORDS = re.compile(
    r"\b(engineer|developer|analyst|manager|lead|architect|scientist|consultant|"
    r"designer|director|head|specialist|administrator|sde|intern|principal|staff|"
    r"senior|advisory|associate)\b", re.IGNORECASE)


def _infer_title(text: str) -> str:
    """Infer a job title from free text — find the title-word and grab the
    preceding qualifier(s), e.g. 'staff AI engineer' -> 'Staff AI Engineer'."""
    m = re.search(
        r"\b((?:senior|staff|lead|principal|advisory|associate|junior)\s+)?"
        r"((?:ai|ml|data|backend|frontend|full[\s-]?stack|software|cloud|devops|nlp|"
        r"platform|security|systems|product)\s+){0,2}"
        r"(engineer|developer|analyst|manager|architect|scientist|"
        r"consultant|designer|director|specialist)\b", text, re.IGNORECASE)
    if m:
        title = re.sub(r"\s+", " ", m.group(0)).strip()
        return title.title() if title.islower() else title
    return ""


def _make_job(title: str, company: str, date_line: str, body: list[str]) -> dict:
    start = end = None
    dm = _DATE_RANGE.search(date_line)
    if dm:
        start, end_raw = dm.group(1), dm.group(2)
        end = None if end_raw.lower() in ("present", "current") else end_raw
    months = parse_duration_months(start or "", end) if start else 0
    return {
        "title": title.strip()[:60], "company": company.strip()[:60],
        "description": " ".join(body).strip()[:800],
        "start_date": (start + "-01") if start and len(start) == 4 else (start or ""),
        "end_date": (end + "-01") if end and len(end) == 4 else end,
        "is_current": end is None and start is not None,
        "duration_months": months, "industry": "", "company_size": "51-200",
    }


def _split_header_parts(line: str) -> tuple[str, str, str]:
    """From a header line, return (title, company, date_fragment). Handles
    'Title at Company (2019 - present)', 'TITLE | COMPANY | 2018-PRESENT',
    'Title, Company, 2019 - 2021'."""
    date_frag = ""
    dm = _DATE_RANGE.search(line)
    if dm:
        date_frag = dm.group(0)
        line = line.replace(dm.group(0), " ")
    line = re.sub(r"[()]", " ", line).strip(" ,-|")
    # pipe or 'at'/'@'/comma separated
    parts = [p.strip() for p in re.split(r"\s*[|@]\s*|\s+at\s+|\s*,\s*", line) if p.strip()]
    if len(parts) >= 2:
        return parts[0], parts[1], date_frag
    return (parts[0] if parts else line.strip()), "", date_frag


def _looks_like_header(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith(("-", "•", "·", "*")):
        return False
    return bool(_DATE_RANGE.search(s) or _TITLE_AT.match(s) or
                ("|" in s and _TITLE_WORDS.search(s)) or
                (_TITLE_WORDS.search(s) and len(s.split()) <= 8))


def _parse_experience(lines: list[str]) -> list[dict]:
    """Group experience lines into jobs. Robust to: title-at-company, pipe format,
    and the common 'title line / company line / date line' split layout."""
    jobs: list[dict] = []
    title = company = date_line = ""
    body: list[str] = []
    have_header = False

    def flush():
        nonlocal title, company, date_line, body, have_header
        if have_header:
            jobs.append(_make_job(title, company, date_line, body))
        title = company = date_line = ""
        body = []
        have_header = False

    i = 0
    nonempty = [ln for ln in lines if ln.strip()]
    while i < len(nonempty):
        ln = nonempty[i].strip()
        if _looks_like_header(ln):
            flush()
            t, c, d = _split_header_parts(ln)
            title, company, date_line = t, c, d
            have_header = True
            # split layout: next 1-2 short lines may be company / a bare date range
            for j in (i + 1, i + 2):
                if j < len(nonempty):
                    nxt = nonempty[j].strip()
                    if not company and nxt and len(nxt.split()) <= 4 and not _DATE_RANGE.search(nxt) \
                       and not nxt.startswith(("-", "•")) and not _TITLE_WORDS.search(nxt):
                        company = nxt; i = j
                    elif not date_line and _DATE_RANGE.search(nxt) and len(nxt.split()) <= 4:
                        date_line = nxt; i = j
        else:
            body.append(ln)
        i += 1
    flush()
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


def _mk_skill(name: str) -> dict:
    return {"name": name, "proficiency": "intermediate", "endorsements": 0, "duration_months": 12}


def _parse_skills(section_lines: list[str], full_text: str) -> list[dict]:
    """Recover skills from (a) a SKILLS section if present, (b) inline 'Skills: a, b'
    anywhere, and (c) a gazetteer scan of the whole text as a fallback. De-duped,
    case-insensitive."""
    skills: list[dict] = []
    seen: set[str] = set()

    def add(name: str):
        name = name.strip(" .-•·|")
        key = name.lower()
        if 2 <= len(name) <= 30 and key not in seen and not key.startswith("skill"):
            seen.add(key)
            skills.append(_mk_skill(name))

    # (a) explicit section content
    for s in re.split(r"[,;|•·\n]+", " ".join(section_lines)):
        add(s)

    # (b) inline "Skills: x, y, z" or "Technical Skills - ..." anywhere in the text
    for m in re.finditer(r"(?:technical\s+skills|skills)\s*[:\-]\s*(.+)", full_text, re.IGNORECASE):
        for s in re.split(r"[,;|•·]+", m.group(1)):
            add(s)

    # (c) gazetteer fallback — recover well-known skills mentioned anywhere, so a
    # paragraph resume with no SKILLS section still yields a skill list.
    low = full_text.lower()
    for kw in _KNOWN_SKILLS:
        if kw in seen:
            continue
        # whole-token / phrase presence (word-boundary safe for single tokens)
        if (" " in kw and kw in low) or re.search(rf"(?<![a-z0-9]){re.escape(kw)}(?![a-z0-9])", low):
            # title-case display for readability
            add(kw if any(ch in kw for ch in "+.#/") else kw.title())
        if len(skills) >= 30:
            break

    return skills[:30]


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

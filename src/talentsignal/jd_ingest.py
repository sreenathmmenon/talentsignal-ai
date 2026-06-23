"""Free-text Job Description ingestion -> structured, weighted requirement model.

The front door of the general product: drop in ANY job description as plain text
and get back a list of Requirement objects the ranking engine scores against.
No hosted LLM, no network — a transparent cue-lexicon + regex pipeline, so every
extracted requirement is explainable ("this became a disqualifier because the
sentence started with 'we will not move forward with'").

Output: a RequirementModel with
  * requirements: list[Requirement] (kind: must_have | nice_to_have | disqualifier),
    each with a weight reflecting how strongly the JD emphasizes it,
  * seniority band (min/max years) parsed from "X-Y years",
  * preferred locations parsed against a city gazetteer.

This maps cleanly onto the existing JobSpec fields, so an ingested JD and a
hand-written YAML scorecard feed the SAME scoring path.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

# --- requirement kinds ------------------------------------------------------

MUST_HAVE = "must_have"
NICE_TO_HAVE = "nice_to_have"
DISQUALIFIER = "disqualifier"

# Default weights by kind; individual requirements can be boosted by cue strength.
KIND_WEIGHT = {MUST_HAVE: 1.0, NICE_TO_HAVE: 0.4, DISQUALIFIER: 1.0}

# Section headers / inline cues that flip the active requirement kind.
MUST_CUES = (
    "must have", "must-have", "you must", "required", "requirement", "you need",
    "absolutely need", "things you absolutely need", "we need", "you should have",
)
NICE_CUES = (
    "nice to have", "nice-to-have", "bonus", "plus", "preferred", "would like you to have",
    "things we'd like", "good to have",
)
DISQUALIFIER_CUES = (
    "will not move forward", "we will not", "do not want", "don't want",
    "disqualif", "we explicitly do not", "not a fit", "we won't", "red flag",
)

# Phrases that mark an individual sentence as emphasized (boost weight).
EMPHASIS_CUES = ("must", "required", "strong", "absolutely", "essential", "critical", "expect")

# Small city gazetteer for location extraction (extend freely; explainable).
CITY_GAZETTEER = (
    "Pune", "Noida", "Delhi", "Gurgaon", "Gurugram", "Mumbai", "Hyderabad",
    "Bangalore", "Bengaluru", "Chennai", "Kolkata", "Ahmedabad", "Remote",
    "Trivandrum", "Kochi", "Vizag",
)

# Tokens that are too generic to be a useful requirement keyword on their own.
_STOPWORDS = {
    "the", "and", "a", "an", "of", "to", "with", "for", "in", "on", "or", "you",
    "your", "we", "our", "have", "has", "is", "are", "be", "been", "that", "this",
    "it", "as", "at", "by", "from", "must", "should", "will", "not", "no", "any",
    "who", "what", "how", "their", "them", "they", "i", "me", "us", "but", "if",
    "real", "users", "experience", "production", "work", "years", "year", "role",
}

_SENT_SPLIT = re.compile(r"(?<=[.!?;:\n])\s+|\n+")
_YEARS_RE = re.compile(r"(\d{1,2})\s*[-–to]+\s*(\d{1,2})\s*\+?\s*years", re.IGNORECASE)
_YEARS_MIN_RE = re.compile(r"(\d{1,2})\s*\+\s*years", re.IGNORECASE)


@dataclass(frozen=True)
class Requirement:
    text: str          # the human-readable requirement sentence/phrase
    kind: str          # must_have | nice_to_have | disqualifier
    weight: float      # relative importance
    keywords: tuple[str, ...]  # salient lexical tokens (for the lexical channel)


@dataclass
class RequirementModel:
    title: str
    requirements: list[Requirement] = field(default_factory=list)
    preferred_locations: tuple[str, ...] = ()
    min_years: float | None = None
    max_years: float | None = None

    def by_kind(self, kind: str) -> list[Requirement]:
        return [r for r in self.requirements if r.kind == kind]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _keywords(sentence: str, limit: int = 6) -> tuple[str, ...]:
    """Salient lowercase tokens from a sentence, for the lexical match channel.

    Keeps multi-char alphanumerics that aren't stopwords, preserving order and
    de-duplicating. Hyphenated/tool tokens (e.g. 'sentence-transformers') survive.
    """
    toks = re.findall(r"[a-zA-Z][a-zA-Z0-9+#/.\-]{1,}", sentence.lower())
    out: list[str] = []
    for t in toks:
        t = t.strip(".-/")
        if len(t) < 3 or t in _STOPWORDS:
            continue
        if t not in out:
            out.append(t)
        if len(out) >= limit:
            break
    return tuple(out)


def _kind_for(line_lower: str, current: str) -> str:
    """Decide the requirement kind for a line: an explicit cue flips the section;
    otherwise inherit the current section's kind."""
    if any(c in line_lower for c in DISQUALIFIER_CUES):
        return DISQUALIFIER
    if any(c in line_lower for c in NICE_CUES):
        return NICE_TO_HAVE
    if any(c in line_lower for c in MUST_CUES):
        return MUST_HAVE
    return current


def _is_header_only(line: str) -> bool:
    """A short line that is purely a section header (e.g. 'Things you need:')."""
    return len(line.split()) <= 6 and line.rstrip().endswith(":")


_REQ_VERB = re.compile(
    r"\b(must|require|need|should|experience|build|built|ship|design|own|lead|"
    r"deliver|understand|fluen|aware|able|coding|knowledge|track record|"
    r"proficien|familiar|deep|strong|hands.?on)\b", re.IGNORECASE)
_ROLE_WORD = re.compile(
    r"\b(engineer|developer|analyst|manager|architect|scientist|consultant|"
    r"designer|director|specialist|lead|executive|representative)\b", re.IGNORECASE)


def _is_title_or_intro(sent: str) -> bool:
    """True for a job-title / intro line that should not be a scored requirement:
    short, contains a role word, and has no requirement verb (so it reads like a
    title 'Senior AI Engineer at GitLab', not 'must have ...')."""
    words = sent.split()
    if len(words) > 12:
        return False
    if _REQ_VERB.search(sent):
        return False
    # a role word present, or a "... at Company" / "Role. Location." shape
    return bool(_ROLE_WORD.search(sent))


def _is_logistics_only(sent: str) -> bool:
    """True for short lines that are only a seniority band and/or locations
    (e.g. '4-9 years in enterprise sales.', 'Mumbai, Bangalore, or Delhi.').
    These are captured structurally, not as scored requirements."""
    low = sent.lower()
    has_years = bool(_YEARS_RE.search(sent) or _YEARS_MIN_RE.search(sent))
    cities = _extract_locations(sent)
    if not has_years and not cities:
        return False
    # Remove the years phrase and city names; if little substance remains, it's logistics.
    residue = _YEARS_RE.sub("", low)
    residue = _YEARS_MIN_RE.sub("", residue)
    for city in cities:
        residue = re.sub(rf"\b{re.escape(city.lower())}\b", "", residue)
    residue_tokens = [t for t in re.findall(r"[a-z]{3,}", residue) if t not in _STOPWORDS
                      and t not in {"based", "ideally", "willing", "relocate", "enterprise", "sales"}]
    if len(residue_tokens) <= 2 and len(sent.split()) <= 12:
        return True
    # A line whose dominant content is an experience band (e.g. "5-9 years of
    # experience, ideally 6-8 ...") is seniority metadata, not a requirement,
    # even when longer — it has no must/disqualifier verb and leads with years.
    if has_years and not any(c in low for c in DISQUALIFIER_CUES) and re.match(r"\s*\d", sent):
        return True
    return False


def _extract_years(text: str) -> tuple[float | None, float | None]:
    m = _YEARS_RE.search(text)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return float(min(a, b)), float(max(a, b))
    m = _YEARS_MIN_RE.search(text)
    if m:
        return float(m.group(1)), None
    return None, None


def _extract_locations(text: str) -> tuple[str, ...]:
    found: list[str] = []
    for city in CITY_GAZETTEER:
        if re.search(rf"\b{re.escape(city)}\b", text, re.IGNORECASE) and city not in found:
            found.append(city)
    return tuple(found)


def ingest_text(text: str, title: str = "") -> RequirementModel:
    """Parse a free-text JD into a structured, weighted requirement model."""
    text = text or ""
    if not title:
        # first non-empty line is a reasonable title guess
        for line in text.splitlines():
            if line.strip():
                title = _norm(line)
                break

    model = RequirementModel(title=title or "Untitled Role")
    model.min_years, model.max_years = _extract_years(text)
    model.preferred_locations = _extract_locations(text)

    current_kind = MUST_HAVE  # default before any cue: treat substantive lines as requirements
    seen: set[str] = set()

    for i, raw in enumerate(_SENT_SPLIT.split(text)):
        sent = _norm(raw)
        if not sent:
            continue
        low = sent.lower()
        kind = _kind_for(low, current_kind)
        # A line that flips the section also sets current_kind for following lines.
        if kind != current_kind and (_is_header_only(sent) or any(c in low for c in DISQUALIFIER_CUES + NICE_CUES + MUST_CUES)):
            current_kind = kind
        if _is_header_only(sent):
            continue  # header itself isn't a requirement
        # Skip pure logistics lines (years/location only) — they're captured as
        # the seniority band and preferred_locations, not as scored requirements.
        if _is_logistics_only(sent):
            continue
        # Skip the job title / intro line (e.g. "Senior AI Engineer at GitLab.",
        # "Machine Learning Engineer. Bangalore."). A title matched as a
        # "requirement" gives every candidate spurious credit for sharing the role
        # word, which inflates weak candidates. A title line is short, has no
        # requirement verb, and reads like "Role [at Company]".
        if i < 4 and _is_title_or_intro(sent):
            continue
        # Skip lines with too little substance to be a requirement.
        kws = _keywords(sent)
        if len(kws) < 2:
            continue
        # Disqualifier sentences are often long; split on inner separators for clarity
        # but keep as one requirement to preserve meaning.
        key = low[:80]
        if key in seen:
            continue
        seen.add(key)
        weight = KIND_WEIGHT[kind]
        if any(c in low for c in EMPHASIS_CUES) and kind == MUST_HAVE:
            weight *= 1.25
        model.requirements.append(Requirement(text=sent, kind=kind, weight=round(weight, 3), keywords=kws))

    return model


def must_have_phrases(model: RequirementModel) -> tuple[str, ...]:
    """Flatten must-have requirement texts (compat with JobSpec.must_have shape)."""
    return tuple(r.text for r in model.by_kind(MUST_HAVE))


def disqualifier_phrases(model: RequirementModel) -> tuple[str, ...]:
    return tuple(r.text for r in model.by_kind(DISQUALIFIER))


def all_keywords(reqs: Iterable[Requirement]) -> set[str]:
    out: set[str] = set()
    for r in reqs:
        out.update(r.keywords)
    return out

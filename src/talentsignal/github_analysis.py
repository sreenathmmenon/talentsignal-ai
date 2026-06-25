"""GitHub-repo analysis — surface real engineering evidence from a candidate's
OWN linked public profile (the kind of signal SeekOut charges for).

This reads ONLY a GitHub profile the candidate themselves linked in their resume
(public API, consented data — no scraping of un-linked people). It turns public
signals into an explainable evidence score: languages used, public repos,
total stars (peer validation), and recent push activity. Offline-safe: with no
network it returns a clear "not fetched" result so ranking never depends on it
and never blocks.

Privacy stance (consistent with the product's no-scraping moat): we analyze only
a profile URL the candidate put on their own resume, via the public API, and we
report exactly what we used.
"""
from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass, field
from typing import Any

_GH_USER_RE = re.compile(r"github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38})?)", re.IGNORECASE)
_API = "https://api.github.com"


@dataclass
class GithubProfile:
    username: str = ""
    fetched: bool = False
    public_repos: int = 0
    followers: int = 0
    total_stars: int = 0
    top_languages: list[str] = field(default_factory=list)
    recently_active: bool = False
    evidence: str = ""
    score: float = 0.0   # 0..1 normalized engineering-activity signal

    def to_dict(self) -> dict[str, Any]:
        return {"username": self.username, "fetched": self.fetched,
                "public_repos": self.public_repos, "followers": self.followers,
                "total_stars": self.total_stars, "top_languages": self.top_languages,
                "recently_active": self.recently_active, "score": round(self.score, 3),
                "evidence": self.evidence}


def find_github_username(candidate: dict[str, Any]) -> str:
    """Extract a GitHub username from the candidate's OWN resume text/links."""
    parts = [str(candidate.get("profile", {}).get("summary", "")),
             str(candidate.get("profile", {}).get("headline", ""))]
    for j in candidate.get("career_history", []) or []:
        parts.append(str(j.get("description", "")))
    for link in candidate.get("links", []) or []:
        parts.append(str(link))
    blob = " ".join(parts)
    m = _GH_USER_RE.search(blob)
    if not m:
        return ""
    name = m.group(1)
    # exclude common non-user paths
    if name.lower() in {"about", "features", "pricing", "topics", "orgs", "sponsors"}:
        return ""
    return name


def _get(url: str, timeout: float) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "talentsignal"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def analyze_github(candidate: dict[str, Any], *, timeout: float = 6.0,
                   max_repos: int = 30) -> GithubProfile:
    """Fetch and score a candidate's public GitHub profile. Offline-safe: any
    network/parse failure returns a clear not-fetched result (never raises)."""
    username = find_github_username(candidate)
    if not username:
        return GithubProfile(evidence="no GitHub profile linked in the resume")
    prof = GithubProfile(username=username)
    try:
        user = _get(f"{_API}/users/{username}", timeout)
        prof.public_repos = int(user.get("public_repos") or 0)
        prof.followers = int(user.get("followers") or 0)
        repos = _get(f"{_API}/users/{username}/repos?per_page={max_repos}&sort=pushed", timeout)
        if isinstance(repos, list):
            langs: dict[str, int] = {}
            for r in repos:
                if r.get("fork"):
                    continue
                prof.total_stars += int(r.get("stargazers_count") or 0)
                lang = r.get("language")
                if lang:
                    langs[lang] = langs.get(lang, 0) + 1
            prof.top_languages = [l for l, _ in sorted(langs.items(), key=lambda x: -x[1])][:5]
            # recent activity: any non-fork repo pushed in the API's most-recent set
            prof.recently_active = any(not r.get("fork") for r in repos[:5])
        prof.fetched = True
    except Exception as exc:  # noqa: BLE001 - offline / rate-limited / bad user
        prof.evidence = f"GitHub profile '{username}' linked but not fetched ({type(exc).__name__})"
        return prof

    # Normalized engineering-activity score from public, consented signals.
    import math
    repo_s = min(1.0, math.log1p(prof.public_repos) / math.log1p(40))
    star_s = min(1.0, math.log1p(prof.total_stars) / math.log1p(500))
    foll_s = min(1.0, math.log1p(prof.followers) / math.log1p(300))
    active = 1.0 if prof.recently_active else 0.4
    prof.score = round(0.35 * repo_s + 0.35 * star_s + 0.15 * foll_s + 0.15 * active, 3)
    langs = ", ".join(prof.top_languages) or "—"
    prof.evidence = (f"{prof.public_repos} public repos, {prof.total_stars} stars, "
                     f"{prof.followers} followers; languages: {langs}"
                     f"{'; recently active' if prof.recently_active else ''}")
    return prof

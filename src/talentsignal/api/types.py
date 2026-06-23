"""Typed result objects — the stable output contract of the engine.

These are deliberately plain dataclasses with `to_dict()` so every surface
(MCP/REST/UI/CLI) serializes results identically and integrators get a clear,
versioned shape. Internal engine objects (ScoreBreakdown, CandidateEvidence)
are mapped INTO these views, so the public contract is decoupled from internals.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class RequirementMatchView:
    """How one JD requirement matched (or didn't) for a candidate."""
    requirement: str
    kind: str            # must_have | nice_to_have | disqualifier
    score: float         # 0..1 combined match
    dense: float         # 0..1 semantic
    lexical: float       # 0..1 keyword
    matched_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RiskFlagView:
    """An explainable risk/consistency flag with the contradicting facts."""
    code: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FactorBreakdown:
    """The six scoring factors plus the hybrid sub-signals."""
    technical_evidence: float
    career_fit: float
    seniority: float
    logistics: float
    behavioral: float
    trust: float
    semantic_fit: float = 0.0
    lexical_fit: float = 0.0
    requirement_coverage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RankedCandidate:
    candidate_id: str
    rank: int
    score: float
    reasoning: str
    title: str = ""
    years: float = 0.0
    location: str = ""
    factors: FactorBreakdown | None = None
    requirement_matches: list[RequirementMatchView] = field(default_factory=list)
    risk_flags: list[RiskFlagView] = field(default_factory=list)
    top10_eligible: bool = True
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class RankResult:
    """The full result of ranking a candidate pool against a JD."""
    job_title: str
    job_id: str
    engine: str                       # spine | hybrid
    candidate_count: int
    ranked: list[RankedCandidate]
    requirements: list[dict[str, Any]] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    api_version: str = "1.0.0"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_title": self.job_title,
            "job_id": self.job_id,
            "engine": self.engine,
            "candidate_count": self.candidate_count,
            "elapsed_seconds": self.elapsed_seconds,
            "api_version": self.api_version,
            "notes": self.notes,
            "requirements": self.requirements,
            "ranked": [c.to_dict() for c in self.ranked],
        }

    def to_csv_rows(self) -> list[dict[str, Any]]:
        """The challenge submission shape: candidate_id,rank,score,reasoning."""
        return [
            {"candidate_id": c.candidate_id, "rank": c.rank,
             "score": f"{c.score:.6f}", "reasoning": c.reasoning}
            for c in self.ranked
        ]

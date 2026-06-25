"""TalentSignal public API.

The single, stable surface every other component builds on — the CLI, the MCP
server, the REST API, and the product UI all call `rank()` here rather than
reaching into engine internals. Import-light: this module pulls in heavy pieces
(embeddings, ingest adapters) lazily so `import talentsignal.api` stays cheap.

    from talentsignal.api import rank, RankResult

    result = rank(jd="Senior AI Engineer ...", candidates=[...])
    for c in result.ranked:
        print(c.rank, c.candidate_id, c.score, c.reasoning)
"""
from __future__ import annotations

from .types import (
    FactorBreakdown,
    RankedCandidate,
    RankResult,
    RequirementMatchView,
    RiskFlagView,
)
from .facade import rank, TalentSignal
from .batch import rank_file, rank_many_jds, rank_to_csv

__all__ = [
    "rank",
    "TalentSignal",
    "rank_file",
    "rank_many_jds",
    "rank_to_csv",
    "RankResult",
    "RankedCandidate",
    "FactorBreakdown",
    "RequirementMatchView",
    "RiskFlagView",
]

__api_version__ = "1.0.0"

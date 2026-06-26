"""The engine facade — one clean entry point for ranking.

`rank(jd, candidates)` accepts a JD as free text / structured spec / file, and
candidates as already-structured records (the ingest layer, Epic B, adds raw
files on top of this), runs the hybrid or spine engine, and returns a typed
RankResult. Every other surface (MCP, REST, UI, CLI) calls this — so there is
one implementation of "how ranking works", not five.

Design choices:
  * Format-agnostic JD: str (free text), JobSpec, or a path to .yaml/.md/.txt.
  * Candidates: list of dict records (canonical schema). Raw files are handled
    by the ingest layer which produces these dicts.
  * Engine: "hybrid" (semantic, best) when an index/embedder is available,
    else gracefully "spine" or lexical-only — always returns a result.
  * No file/CSV coupling: results are returned as objects; writing CSV is a
    separate concern (RankResult.to_csv_rows()).
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Iterable

from ..jd_parser import JobSpec, load_job_spec, job_spec_from_jd_text
from .types import (
    FactorBreakdown, RankResult, RankedCandidate, RequirementMatchView, RiskFlagView,
)


def _safe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Defensively normalize incoming candidate records so a partial/malformed
    record (missing profile/career/skills/signals, or no candidate_id) never
    crashes ranking. A production engine must degrade, not throw."""
    out: list[dict[str, Any]] = []
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            continue
        rec = dict(rec)
        # Coerce missing OR explicitly-null fields to safe defaults. A real-world
        # export commonly has keys present with null values (career_history:null),
        # which setdefault would leave as None and crash downstream iteration.
        if not isinstance(rec.get("candidate_id"), str):
            rec["candidate_id"] = f"CAND_{i:07d}"
        if not isinstance(rec.get("profile"), dict):
            rec["profile"] = {}
        for key in ("career_history", "education", "skills"):
            if not isinstance(rec.get(key), list):
                rec[key] = []
        if not isinstance(rec.get("redrob_signals"), dict):
            rec["redrob_signals"] = {}
        out.append(rec)
    return out


def _resolve_job(jd: Any, *, category: str, title: str) -> JobSpec:
    """Turn any JD form into a JobSpec."""
    if isinstance(jd, JobSpec):
        return jd
    if isinstance(jd, (str, Path)):
        p = Path(jd) if not isinstance(jd, Path) else jd
        # a path to a file?
        try:
            if p.exists() and p.suffix in {".yaml", ".yml"}:
                return load_job_spec(p)
            if p.exists() and p.suffix in {".md", ".txt"}:
                return job_spec_from_jd_text(p.read_text(encoding="utf-8"),
                                             job_id=p.stem, category=category, title=title)
        except (OSError, ValueError):
            pass
        # otherwise treat the string as the JD text itself
        return job_spec_from_jd_text(str(jd), category=category, title=title)
    raise TypeError(f"unsupported jd type: {type(jd)}")


def _map_requirement_matches(score) -> list[RequirementMatchView]:
    """Map the matched-requirement tuples on a ScoreBreakdown to views."""
    out: list[RequirementMatchView] = []
    for item in getattr(score, "matched_requirements", ()) or ():
        # tuples are (req_text, keywords) or (req_text, keywords, evidence_span)
        req_text, kws = item[0], item[1]
        span = item[2] if len(item) > 2 else ""
        out.append(RequirementMatchView(
            requirement=req_text, kind="must_have", score=0.0, dense=0.0, lexical=0.0,
            matched_keywords=list(kws), evidence_span=span,
        ))
    return out


def _map_risk_flags(score) -> list[RiskFlagView]:
    flags = []
    notes = list(getattr(score, "concern_notes", ()) or ())
    codes = list(getattr(score, "risk_flags", ()) or [])
    # pair codes with notes where possible; fall back to code-only
    for i, code in enumerate(codes):
        detail = notes[i] if i < len(notes) else code.replace("_", " ")
        flags.append(RiskFlagView(code=code, detail=detail))
    return flags


def _to_ranked_candidate(row: dict[str, Any], rank_i: int) -> RankedCandidate:
    score = row.get("_score")
    ev = row.get("_evidence")
    factors = None
    if score is not None:
        factors = FactorBreakdown(
            technical_evidence=score.technical_evidence,
            career_fit=score.career_fit,
            seniority=score.seniority,
            logistics=score.logistics,
            behavioral=score.behavioral,
            trust=score.trust,
            semantic_fit=getattr(score, "semantic_fit", 0.0),
            lexical_fit=getattr(score, "lexical_fit", 0.0),
            requirement_coverage=getattr(score, "requirement_coverage", 0.0),
            role_relevance=getattr(score, "role_relevance", 0.0),
            general_quality=getattr(score, "general_quality", 0.0),
        )
    return RankedCandidate(
        candidate_id=row["candidate_id"],
        rank=int(row["rank"]),
        score=float(row["score"]),
        reasoning=row.get("reasoning", ""),
        title=getattr(ev, "title", "") if ev else "",
        years=getattr(ev, "years", 0.0) if ev else 0.0,
        location=getattr(ev, "location", "") if ev else "",
        factors=factors,
        requirement_matches=_map_requirement_matches(score) if score else [],
        risk_flags=_map_risk_flags(score) if score else [],
        top10_eligible=getattr(score, "top10_eligible", True) if score else True,
        confidence=getattr(score, "confidence", 0.0) if score else 0.0,
    )


class TalentSignal:
    """Reusable engine handle. Construct once (optionally with a precomputed
    index / embedder), call rank() many times.

    This is the object an integrator holds: stateless ranking, pluggable
    embedding source, deterministic.
    """

    def __init__(self, *, index_dir: str | None = None, embedder=None):
        self.index_dir = index_dir
        self.embedder = embedder  # callable(list[str]) -> np.ndarray, optional

    def rank(
        self,
        jd: Any,
        candidates: Iterable[dict[str, Any]],
        *,
        top_n: int = 100,
        engine: str = "hybrid",
        category: str = "ai_ml_search_ranking",
        title: str = "",
    ) -> RankResult:
        from ..ranking import rank_records, score_pool_hybrid, _rows_from_scored

        start = time.perf_counter()
        job = _resolve_job(jd, category=category, title=title)
        records = _safe_records(list(candidates))
        notes: list[str] = []

        if engine == "hybrid":
            req_emb = None
            cand_index = None
            if self.embedder is not None:
                # live-embed (small pools / demo)
                from .. import artifacts
                texts = [artifacts.evidence_text_of(c) for c in records]
                ids = [c["candidate_id"] for c in records]
                emb = self.embedder(texts)
                cand_index = ({cid: i for i, cid in enumerate(ids)}, emb)
                req_texts = [r.text for r in getattr(job, "requirements", ()) or ()]
                if req_texts:
                    req_emb = self.embedder(req_texts)
            scored = score_pool_hybrid(records, job, index_dir=self.index_dir,
                                       candidate_embeddings=cand_index, req_embeddings=req_emb)
            rows = _rows_from_scored(scored, job, top_n)
            used_engine = "hybrid"
            if self.index_dir is None and self.embedder is None:
                notes.append("no embedding index/embedder provided; hybrid ran lexical-only")
        else:
            rows = rank_records(records, job, top_n=top_n)
            used_engine = "spine"

        ranked = [_to_ranked_candidate(r, i + 1) for i, r in enumerate(rows)]
        requirements = [
            {"text": r.text, "kind": r.kind, "weight": r.weight}
            for r in (getattr(job, "requirements", ()) or ())
        ]
        return RankResult(
            job_title=job.title,
            job_id=job.id,
            engine=used_engine,
            candidate_count=len(records),
            ranked=ranked,
            requirements=requirements,
            elapsed_seconds=round(time.perf_counter() - start, 3),
            notes=notes,
        )


def rank(
    jd: Any,
    candidates: Iterable[dict[str, Any]],
    *,
    top_n: int = 100,
    engine: str = "hybrid",
    index_dir: str | None = None,
    embedder=None,
    category: str = "ai_ml_search_ranking",
    title: str = "",
) -> RankResult:
    """One-shot ranking facade. See TalentSignal.rank for details."""
    return TalentSignal(index_dir=index_dir, embedder=embedder).rank(
        jd, candidates, top_n=top_n, engine=engine, category=category, title=title)

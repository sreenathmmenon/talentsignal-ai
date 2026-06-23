from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from .features import build_evidence
from .io import iter_candidates
from .jd_parser import JobSpec
from .reasoning import generate_reasoning
from .scoring import score_candidate


def score_pool_from_iter(
    candidates: "Iterable[dict[str, Any]]", job: JobSpec
) -> list[tuple[Any, Any, dict[str, Any]]]:
    """Score an in-memory iterable of candidate records and return them sorted
    best-first. Shared by the file-based ranker and the eval harness so both
    exercise the exact same scoring path."""
    scored: list[tuple[Any, Any, dict[str, Any]]] = []
    for candidate in candidates:
        ev = build_evidence(candidate)
        score = score_candidate(ev, job)
        scored.append((score, ev, candidate))
    scored.sort(key=lambda item: (-item[0].final_score, item[1].candidate_id))
    return scored


def _score_pool(candidates_path: str | Path, job: JobSpec) -> list[tuple[Any, Any, dict[str, Any]]]:
    return score_pool_from_iter(iter_candidates(candidates_path), job)


def rank_records(records: "Iterable[dict[str, Any]]", job: JobSpec, top_n: int = 100) -> list[dict[str, Any]]:
    """Rank in-memory candidate records (used by eval + demo)."""
    return _rows_from_scored(score_pool_from_iter(records, job), job, top_n)


def score_pool_hybrid(
    candidates: "Iterable[dict[str, Any]]",
    job: JobSpec,
    *,
    index_dir: str | None = None,
    req_embeddings=None,
    candidate_embeddings=None,      # optional: (id_to_row, emb_matrix)
    live_embedder=None,             # optional callable(list[str]) -> np.ndarray for demo
    alpha: float | None = None,
) -> list[tuple[Any, Any, dict[str, Any]]]:
    """Score a pool with the hybrid (semantic + schema + consistency) engine.

    Embeddings are optional: if a precomputed index (or live embedder) is given,
    the dense channel is active; otherwise it degrades to lexical-only — the
    system always produces a ranking. This is the same scoring path for any JD.
    """
    from . import artifacts
    from . import semantic_match as sm
    from .consistency_audit import audit_candidate
    from .schema_profile import schema_signals
    from .scoring import score_candidate_hybrid

    requirements = list(getattr(job, "requirements", ()) or ())
    a = sm.DEFAULT_ALPHA if alpha is None else alpha

    # Resolve candidate + requirement embeddings (precomputed index path).
    id_to_row = emb = None
    if candidate_embeddings is not None:
        id_to_row, emb = candidate_embeddings
    elif index_dir is not None:
        id_to_row, emb, _meta = artifacts.load_candidate_index(index_dir)
    if req_embeddings is None and index_dir is not None:
        req_embeddings = artifacts.load_requirement_embeddings(job.id, index_dir)

    scored: list[tuple[Any, Any, dict[str, Any]]] = []
    for candidate in candidates:
        ev = build_evidence(candidate)
        cid = ev.candidate_id
        evidence_text = artifacts.evidence_text_of(candidate)
        ev_vec = None
        if emb is not None and id_to_row is not None and cid in id_to_row:
            ev_vec = emb[id_to_row[cid]]
        elif live_embedder is not None:
            ev_vec = live_embedder([evidence_text])[0]
        result = sm.match(requirements, req_embeddings, evidence_text, ev_vec, alpha=a)
        schema_sig = schema_signals(candidate)
        consistency = audit_candidate(candidate)
        score = score_candidate_hybrid(ev, job, match_result=result,
                                       schema_sig=schema_sig, consistency=consistency)
        scored.append((score, ev, candidate))
    scored.sort(key=lambda item: (-item[0].final_score, item[1].candidate_id))
    return scored


def rank_records_hybrid(records, job: JobSpec, top_n: int = 100, **kwargs) -> list[dict[str, Any]]:
    return _rows_from_scored(score_pool_hybrid(records, job, **kwargs), job, top_n)


def _rows_from_scored(scored: list[tuple[Any, Any, dict[str, Any]]], job: JobSpec, top_n: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rank, (score, ev, _candidate) in enumerate(scored[:top_n], start=1):
        # Ensure strict non-increasing scores after rounding and deterministic ordering.
        display_score = max(0.0, score.final_score - (rank - 1) * 0.000001)
        rows.append(
            {
                "candidate_id": ev.candidate_id,
                "rank": rank,
                "score": f"{display_score:.6f}",
                "reasoning": generate_reasoning(ev, score, rank, job),
                "_score": score,
                "_evidence": ev,
            }
        )
    return rows


def rank_candidates(candidates_path: str | Path, job: JobSpec, top_n: int = 100) -> list[dict[str, Any]]:
    return _rows_from_scored(_score_pool(candidates_path, job), job, top_n)


def rank_candidates_with_pool(
    candidates_path: str | Path, job: JobSpec, top_n: int = 100
) -> tuple[list[dict[str, Any]], list[tuple[Any, Any, dict[str, Any]]]]:
    scored = _score_pool(candidates_path, job)
    return _rows_from_scored(scored, job, top_n), scored


def write_submission(rows: list[dict[str, Any]], out_path: str | Path) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(out_path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in ["candidate_id", "rank", "score", "reasoning"]})


def write_factor_scores(rows: list[dict[str, Any]], out_path: str | Path) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "candidate_id",
        "rank",
        "score",
        "technical_evidence",
        "career_fit",
        "seniority",
        "logistics",
        "behavioral",
        "trust",
        "confidence",
        "top10_eligible",
        "penalty",
        "risk_flags",
        "career_retrieval_count",
        "career_production_count",
        "vector_count",
        "eval_count",
        "ml_count",
        "career_retrieval_terms",
        "career_production_terms",
        "vector_terms",
        "eval_terms",
    ]
    with Path(out_path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            score = row["_score"]
            writer.writerow(
                {
                    "candidate_id": row["candidate_id"],
                    "rank": row["rank"],
                    "score": row["score"],
                    "technical_evidence": score.technical_evidence,
                    "career_fit": score.career_fit,
                    "seniority": score.seniority,
                    "logistics": score.logistics,
                    "behavioral": score.behavioral,
                    "trust": score.trust,
                    "confidence": score.confidence,
                    "top10_eligible": score.top10_eligible,
                    "penalty": score.penalty,
                    "risk_flags": "|".join(score.risk_flags),
                    "career_retrieval_count": len(row["_evidence"].career_retrieval_terms),
                    "career_production_count": len(row["_evidence"].career_production_terms),
                    "vector_count": len(row["_evidence"].vector_terms),
                    "eval_count": len(row["_evidence"].eval_terms),
                    "ml_count": len(row["_evidence"].ml_terms),
                    "career_retrieval_terms": "|".join(row["_evidence"].career_retrieval_terms),
                    "career_production_terms": "|".join(row["_evidence"].career_production_terms),
                    "vector_terms": "|".join(row["_evidence"].vector_terms),
                    "eval_terms": "|".join(row["_evidence"].eval_terms),
                }
            )


def write_risk_report(rows: list[dict[str, Any]], out_path: str | Path) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fields = ["candidate_id", "rank", "score", "penalty", "risk_flags", "top10_eligible", "audit_note"]
    with Path(out_path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            score = row["_score"]
            ev = row["_evidence"]
            note_parts = []
            if score.risk_flags:
                note_parts.append("risk flags present")
            if row["rank"] <= 10 and not score.top10_eligible:
                note_parts.append("not top-10 eligible")
            if not ev.career_retrieval_terms:
                note_parts.append("limited career retrieval/ranking evidence")
            writer.writerow(
                {
                    "candidate_id": row["candidate_id"],
                    "rank": row["rank"],
                    "score": row["score"],
                    "penalty": score.penalty,
                    "risk_flags": "|".join(score.risk_flags),
                    "top10_eligible": score.top10_eligible,
                    "audit_note": "; ".join(note_parts) if note_parts else "no material risk flags",
                }
            )


def write_risk_summary(rows: list[dict[str, Any]], out_path: str | Path) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    top10_ineligible = 0
    for row in rows:
        score = row["_score"]
        if row["rank"] <= 10 and not score.top10_eligible:
            top10_ineligible += 1
        for flag in score.risk_flags:
            counts[flag] = counts.get(flag, 0) + 1
    summary = {
        "rows": len(rows),
        "top10_ineligible": top10_ineligible,
        "risk_flag_counts": dict(sorted(counts.items())),
        "top100_with_any_risk_flag": sum(1 for row in rows if row["_score"].risk_flags),
    }
    Path(out_path).write_text(json.dumps(summary, indent=2), encoding="utf-8")


def write_evidence_packets(rows: list[dict[str, Any]], out_path: str | Path) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(out_path).open("w", encoding="utf-8") as handle:
        for row in rows:
            ev = row["_evidence"]
            score = row["_score"]
            packet = {
                "candidate_id": row["candidate_id"],
                "rank": row["rank"],
                "score": row["score"],
                "reasoning": row["reasoning"],
                "score_breakdown": asdict(score),
                "evidence": {
                    "title": ev.title,
                    "years": ev.years,
                    "location": ev.location,
                    "country": ev.country,
                    "career_retrieval_terms": ev.career_retrieval_terms,
                    "career_production_terms": ev.career_production_terms,
                    "skill_retrieval_terms": ev.skill_retrieval_terms,
                    "skill_vector_terms": ev.skill_vector_terms,
                    "skill_ml_terms": ev.skill_ml_terms,
                    "vector_terms": ev.vector_terms,
                    "eval_terms": ev.eval_terms,
                    "production_terms": ev.production_terms,
                    "risk_flags": score.risk_flags,
                    "top10_eligible": score.top10_eligible,
                    "confidence": score.confidence,
                },
            }
            handle.write(json.dumps(packet, ensure_ascii=False) + "\n")

"""Hybrid semantic matching between JD requirements and candidate evidence.

This is the engine that lets a candidate who wrote "built the system that decides
which profiles surface first for a recruiter" match the requirement "shipped a
ranking system" — with ZERO shared keywords. It replaces hardcoded keyword
membership as the primary relevance signal.

Two channels, combined per requirement:
  * DENSE   — cosine similarity between a requirement's embedding and the
              candidate's evidence embedding (captures meaning/paraphrase).
  * LEXICAL — overlap of the requirement's salient keywords with the candidate's
              evidence text (captures exact tool/skill terms the dense channel
              can blur, e.g. "FAISS", "NDCG").

    req_score = alpha * dense + (1 - alpha) * lexical

Aggregated across requirements (weighted by each requirement's importance) into
a single semantic_fit / lexical_fit, plus per-requirement match details used for
grounded reasoning.

CRITICAL: this module imports numpy ONLY. It never imports sentence-transformers
or torch, so it is safe to use inside the <=5-min, no-network ranking step. The
embeddings it consumes are produced offline by precompute.py and loaded by
artifacts.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

try:
    import numpy as np
    _HAVE_NUMPY = True
except Exception:  # pragma: no cover - numpy is a hard dep for the hybrid path
    _HAVE_NUMPY = False


DEFAULT_ALPHA = 0.6  # weight on the dense (semantic) channel; tuned via eval


@dataclass
class RequirementMatch:
    req_text: str
    kind: str          # must_have | nice_to_have | disqualifier
    weight: float
    dense: float       # 0..1 cosine (clamped)
    lexical: float     # 0..1 keyword overlap
    score: float       # combined req_score
    matched_keywords: tuple[str, ...]


@dataclass
class MatchResult:
    semantic_fit: float          # weighted aggregate over must/nice requirements
    lexical_fit: float           # weighted lexical-only aggregate
    disqualifier_hit: float      # max disqualifier match (0..1); high = likely a bad fit
    requirement_matches: list[RequirementMatch]
    coverage: float              # fraction of must-have requirements with a real match


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9+#./\-]{3,}", (text or "").lower())}


def lexical_overlap(req_keywords: Sequence[str], evidence_tokens: set[str]) -> tuple[float, tuple[str, ...]]:
    """Fraction of a requirement's keywords present (whole-token) in the evidence.

    Whole-token match (not substring) so 'ml' never matches inside 'html'. Tool
    keywords are matched against a normalized token set of the candidate text.
    """
    if not req_keywords:
        return 0.0, ()
    matched = tuple(k for k in req_keywords if k in evidence_tokens)
    return len(matched) / len(req_keywords), matched


# Sentence-embedding cosines for topically-related text cluster in a narrow band
# (empirically ~0.1 irrelevant .. ~0.7 strong for MiniLM on our evidence text).
# Rescaling that band to [0,1] restores discrimination so a true paraphrase fit
# separates clearly from an off-topic profile instead of all bunching near ~0.3.
_COS_FLOOR = 0.12
_COS_CEIL = 0.65


def cosine(a, b) -> float:
    """Rescaled cosine similarity in [0,1].

    Raw cosine is computed, then the informative band [_COS_FLOOR, _COS_CEIL] is
    stretched to [0,1] (values below the floor -> 0, above the ceil -> 1). This
    is a monotonic transform, so it never reorders two candidates against the
    same requirement; it only widens the gaps the final score can use.
    """
    if not _HAVE_NUMPY:
        return 0.0
    a = np.asarray(a, dtype="float32")
    b = np.asarray(b, dtype="float32")
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    sim = float(np.dot(a, b) / (na * nb))
    scaled = (sim - _COS_FLOOR) / (_COS_CEIL - _COS_FLOOR)
    return max(0.0, min(1.0, scaled))


def match(
    requirements: Sequence,                 # list of jd_ingest.Requirement-like objects
    req_embeddings,                          # np.ndarray [R, D] aligned with requirements, or None
    evidence_text: str,
    evidence_embedding,                      # np.ndarray [D] or None (lexical-only fallback)
    *,
    alpha: float = DEFAULT_ALPHA,
) -> MatchResult:
    """Compute hybrid match between a JD's requirements and one candidate.

    If embeddings are unavailable (None), gracefully degrades to lexical-only so
    the system still works without the precomputed index.
    """
    evidence_tokens = _tokenize(evidence_text)
    matches: list[RequirementMatch] = []

    use_dense = (
        _HAVE_NUMPY and req_embeddings is not None and evidence_embedding is not None
        and len(req_embeddings) == len(requirements)
    )

    must_total = 0.0
    must_weighted_score = 0.0
    nice_total = 0.0
    nice_weighted_score = 0.0
    lexical_weighted = 0.0
    lexical_total = 0.0
    disq_hit = 0.0
    must_covered = 0
    must_count = 0

    for i, req in enumerate(requirements):
        kw = tuple(getattr(req, "keywords", ()) or ())
        lex, matched_kw = lexical_overlap(kw, evidence_tokens)
        dense = cosine(req_embeddings[i], evidence_embedding) if use_dense else 0.0
        if use_dense:
            req_score = alpha * dense + (1.0 - alpha) * lex
        else:
            req_score = lex  # lexical-only fallback
        kind = getattr(req, "kind", "must_have")
        weight = float(getattr(req, "weight", 1.0))
        matches.append(RequirementMatch(
            req_text=getattr(req, "text", ""), kind=kind, weight=weight,
            dense=round(dense, 4), lexical=round(lex, 4), score=round(req_score, 4),
            matched_keywords=matched_kw,
        ))

        if kind == "disqualifier":
            disq_hit = max(disq_hit, req_score)
        elif kind == "nice_to_have":
            nice_total += weight
            nice_weighted_score += weight * req_score
        else:  # must_have
            must_total += weight
            must_weighted_score += weight * req_score
            must_count += 1
            if req_score >= 0.30:
                must_covered += 1
        lexical_total += weight
        lexical_weighted += weight * lex

    # semantic_fit emphasizes must-haves, with nice-to-haves as a smaller bonus.
    must_fit = (must_weighted_score / must_total) if must_total else 0.0
    nice_fit = (nice_weighted_score / nice_total) if nice_total else 0.0
    semantic_fit = round(min(1.0, 0.85 * must_fit + 0.15 * nice_fit), 4)
    lexical_fit = round((lexical_weighted / lexical_total) if lexical_total else 0.0, 4)
    coverage = round((must_covered / must_count) if must_count else 0.0, 4)

    return MatchResult(
        semantic_fit=semantic_fit,
        lexical_fit=lexical_fit,
        disqualifier_hit=round(disq_hit, 4),
        requirement_matches=matches,
        coverage=coverage,
    )

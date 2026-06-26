from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def audit_packets(path: str | Path) -> list[str]:
    warnings: list[str] = []
    packets: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                packets.append(json.loads(line))
            except json.JSONDecodeError as exc:
                warnings.append(f"line {line_no}: invalid JSON: {exc}")
    if len(packets) != 100:
        warnings.append(f"expected 100 evidence packets, found {len(packets)}")

    reason_counter = Counter(packet.get("reasoning", "").strip() for packet in packets)
    for reason, count in reason_counter.items():
        if count > 1:
            warnings.append(f"repeated reasoning {count} times: {reason[:120]}")

    for packet in packets:
        cid = packet.get("candidate_id", "UNKNOWN")
        rank = int(packet.get("rank", 999))
        reasoning = packet.get("reasoning", "").strip()
        evidence = packet.get("evidence", {})
        score = packet.get("score_breakdown", {})
        if not reasoning:
            warnings.append(f"{cid}: empty reasoning")
        if len(reasoning) < 40:
            warnings.append(f"{cid}: reasoning too short")
        if len(reasoning) > 500:
            warnings.append(f"{cid}: reasoning too long")
        # Honest concerns are allowed even for high ranks when grounded in profile facts.
        if rank > 75 and "excellent" in reasoning.lower():
            warnings.append(f"{cid}: low-rank row uses overly strong wording")

        supported_terms = set()
        for key in [
            "career_retrieval_terms",
            "career_production_terms",
            "skill_retrieval_terms",
            "skill_vector_terms",
            "skill_ml_terms",
            "vector_terms",
            "eval_terms",
            "production_terms",
        ]:
            supported_terms.update(str(term).lower() for term in evidence.get(key, []))
        supported_terms.update(
            str(evidence.get(key, "")).lower()
            for key in ["title", "location", "country"]
            if evidence.get(key)
        )
        # GROUNDING CHECK — runs on BOTH engines (the production path is hybrid).
        # Build the set of whole tokens actually present in the candidate's own
        # evidence text, plus the matched-requirement keywords the engine cited.
        # Any technical term the reasoning mentions must appear in one of these,
        # so reasoning can never claim a skill the candidate's profile doesn't show.
        evidence_blob = " ".join(str(evidence.get(k, "")) for k in
                                 ("all_text", "career_text", "skill_text", "title",
                                  "summary", "headline")).lower()
        import re as _re
        evidence_tokens = set(_re.findall(r"[a-z0-9+#./]+", evidence_blob))
        evidence_tokens |= supported_terms
        # matched-requirement keywords the engine surfaced (grounded by construction)
        for m in (packet.get("matched_requirements") or score.get("matched_requirements") or []):
            kws = m[1] if isinstance(m, (list, tuple)) and len(m) > 1 else []
            evidence_tokens.update(str(k).lower() for k in (kws or []))

        lowered = reasoning.lower()
        CHECK_TERMS = ["bm25", "ranking", "retrieval", "recommendation", "search",
                       "faiss", "qdrant", "milvus", "pinecone", "weaviate",
                       "elasticsearch", "ndcg", "mrr", "embeddings", "embedding",
                       "kubernetes", "kafka", "pytorch", "tensorflow"]
        for term in CHECK_TERMS:
            if _re.search(r"\b" + _re.escape(term) + r"\b", lowered) and term not in evidence_tokens:
                warnings.append(f"{cid}: reasoning mentions unsupported term '{term}' [{score.get('engine','?')}]")
    return warnings


def write_audit(path: str | Path, out_path: str | Path) -> list[str]:
    warnings = audit_packets(path)
    output = {
        "evidence_packets": str(path),
        "warning_count": len(warnings),
        "warnings": warnings,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(output, indent=2), encoding="utf-8")
    return warnings

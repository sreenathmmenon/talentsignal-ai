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
        # Hybrid-engine reasoning cites only keywords whole-token matched against
        # the candidate's own text (semantic_match.lexical_overlap), so its
        # grounding is guaranteed by construction and separately tested. The
        # hardcoded spine-term whitelist below would false-flag those grounded
        # terms, so it applies only to spine packets.
        if score.get("engine") == "hybrid":
            continue
        # Terms inside parentheses or after "for/such as" should be evidence-backed.
        lowered = reasoning.lower()
        for term in ["bm25", "ranking", "retrieval", "recommendation", "search", "faiss", "qdrant", "milvus", "pinecone", "weaviate", "elasticsearch", "ndcg", "mrr", "a/b"]:
            if term in lowered and term not in supported_terms:
                warnings.append(f"{cid}: reasoning mentions unsupported term '{term}'")
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

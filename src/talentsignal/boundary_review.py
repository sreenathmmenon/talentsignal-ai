from __future__ import annotations

from typing import Any

from .candidate_compare import compare_by_rank


def boundary_windows(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    windows = [
        ("top_10_boundary", 8, 12),
        ("top_25_boundary", 20, 30),
        ("submission_boundary", 90, 100),
    ]
    reviews: list[dict[str, Any]] = []
    by_rank = {int(packet["rank"]): packet for packet in packets}
    for name, start, end in windows:
        members = [by_rank[rank] for rank in range(start, end + 1) if rank in by_rank]
        if not members:
            continue
        reviews.append(
            {
                "name": name,
                "start_rank": start,
                "end_rank": end,
                "candidates": [
                    {
                        "rank": packet["rank"],
                        "candidate_id": packet["candidate_id"],
                        "score": packet["score"],
                        "title": packet["evidence"]["title"],
                        "confidence": packet["score_breakdown"]["confidence"],
                        "risk_flags": packet["score_breakdown"]["risk_flags"],
                    }
                    for packet in members
                ],
            }
        )
    comparisons = [
        item
        for item in (
            compare_by_rank(packets, 10, 11),
            compare_by_rank(packets, 25, 26),
            compare_by_rank(packets, 100, 101),
        )
        if item is not None
    ]
    return [{"windows": reviews, "comparisons": comparisons}]


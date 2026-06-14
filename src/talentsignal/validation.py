from __future__ import annotations

import csv
from pathlib import Path


REQUIRED_HEADER = ["candidate_id", "rank", "score", "reasoning"]


def validate_rows(csv_path: str | Path, valid_ids: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    with Path(csv_path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return ["empty csv"]
        if header != REQUIRED_HEADER:
            errors.append(f"bad header: {header}")
        rows = [row for row in reader if any(cell.strip() for cell in row)]
    if len(rows) != 100:
        errors.append(f"expected 100 rows, found {len(rows)}")
    seen_ids: set[str] = set()
    seen_ranks: set[int] = set()
    last_score = float("inf")
    for idx, row in enumerate(rows, start=2):
        if len(row) != 4:
            errors.append(f"row {idx}: expected 4 columns")
            continue
        cid, rank_s, score_s, reasoning = row
        if cid in seen_ids:
            errors.append(f"row {idx}: duplicate candidate {cid}")
        seen_ids.add(cid)
        if valid_ids is not None and cid not in valid_ids:
            errors.append(f"row {idx}: unknown candidate {cid}")
        try:
            rank = int(rank_s)
        except ValueError:
            errors.append(f"row {idx}: invalid rank {rank_s}")
            continue
        seen_ranks.add(rank)
        try:
            score = float(score_s)
        except ValueError:
            errors.append(f"row {idx}: invalid score {score_s}")
            continue
        if score > last_score:
            errors.append(f"row {idx}: score increases")
        last_score = score
        if not reasoning.strip():
            errors.append(f"row {idx}: empty reasoning")
    missing = set(range(1, 101)) - seen_ranks
    if missing:
        errors.append(f"missing ranks: {sorted(missing)}")
    return errors


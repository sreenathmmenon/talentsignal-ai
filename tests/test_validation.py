"""Submission validator (our internal validate_rows). It must catch every way a
submission CSV can be malformed — these tests exercise each error branch so the
validator can never silently pass a bad file."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from talentsignal.validation import validate_rows, REQUIRED_HEADER


def _write(tmp_path, header, rows):
    p = tmp_path / "sub.csv"
    import csv
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if header is not None:
            w.writerow(header)
        for r in rows:
            w.writerow(r)
    return p


def _good_rows(n=100):
    # strictly non-increasing scores, ranks 1..n, unique ids, non-empty reasoning
    return [[f"CAND_{i:07d}", i, round(1.0 - i * 0.001, 6), f"reason {i}"]
            for i in range(1, n + 1)]


def test_valid_submission_has_no_errors(tmp_path):
    p = _write(tmp_path, REQUIRED_HEADER, _good_rows())
    assert validate_rows(p) == []


def test_empty_file_flagged(tmp_path):
    p = tmp_path / "e.csv"
    p.write_text("", encoding="utf-8")
    assert validate_rows(p) == ["empty csv"]


def test_bad_header_flagged(tmp_path):
    p = _write(tmp_path, ["id", "rank", "score", "reasoning"], _good_rows())
    assert any("bad header" in e for e in validate_rows(p))


def test_wrong_row_count_flagged(tmp_path):
    p = _write(tmp_path, REQUIRED_HEADER, _good_rows(99))
    errs = validate_rows(p)
    assert any("expected 100 rows" in e for e in errs)


def test_duplicate_candidate_flagged(tmp_path):
    rows = _good_rows()
    rows[5][0] = rows[4][0]  # duplicate id
    p = _write(tmp_path, REQUIRED_HEADER, rows)
    assert any("duplicate candidate" in e for e in validate_rows(p))


def test_unknown_candidate_flagged(tmp_path):
    rows = _good_rows(1) + _good_rows(99)  # 100 rows but reuse the same set
    p = _write(tmp_path, REQUIRED_HEADER, _good_rows())
    errs = validate_rows(p, valid_ids={"CAND_0000001"})
    assert any("unknown candidate" in e for e in errs)


def test_invalid_rank_flagged(tmp_path):
    rows = _good_rows()
    rows[0][1] = "one"
    p = _write(tmp_path, REQUIRED_HEADER, rows)
    assert any("invalid rank" in e for e in validate_rows(p))


def test_invalid_score_flagged(tmp_path):
    rows = _good_rows()
    rows[0][2] = "high"
    p = _write(tmp_path, REQUIRED_HEADER, rows)
    assert any("invalid score" in e for e in validate_rows(p))


def test_increasing_score_flagged(tmp_path):
    rows = _good_rows()
    rows[10][2] = 0.999  # higher than the row above -> score increases
    p = _write(tmp_path, REQUIRED_HEADER, rows)
    assert any("score increases" in e for e in validate_rows(p))


def test_empty_reasoning_flagged(tmp_path):
    rows = _good_rows()
    rows[3][3] = "   "
    p = _write(tmp_path, REQUIRED_HEADER, rows)
    assert any("empty reasoning" in e for e in validate_rows(p))


def test_wrong_column_count_flagged(tmp_path):
    rows = _good_rows()
    rows[2] = ["CAND_0000003", 3, 0.9]  # only 3 cols
    p = _write(tmp_path, REQUIRED_HEADER, rows)
    assert any("expected 4 columns" in e for e in validate_rows(p))


def test_missing_rank_flagged(tmp_path):
    rows = _good_rows()
    rows[0][1] = 200  # rank 1 now missing from the 1..100 set
    p = _write(tmp_path, REQUIRED_HEADER, rows)
    assert any("missing ranks" in e for e in validate_rows(p))


def test_the_committed_submission_passes():
    """The actual committed submission must pass our internal validator too."""
    sub = Path(__file__).resolve().parents[1] / "outputs" / "final_submission.csv"
    if sub.exists():
        assert validate_rows(sub) == []

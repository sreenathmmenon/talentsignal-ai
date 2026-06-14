#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.explanation_audit import write_audit
from talentsignal.io import iter_candidates
from talentsignal.validation import validate_rows


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--submission", default="outputs/final_submission.csv")
    parser.add_argument("--official-validator", default="[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py")
    parser.add_argument("--report", default="outputs/final_validation_report.json")
    args = parser.parse_args()

    start = time.perf_counter()
    valid_ids = {candidate["candidate_id"] for candidate in iter_candidates(args.candidates)}
    internal_errors = validate_rows(args.submission, valid_ids)
    official = subprocess.run(
        [sys.executable, args.official_validator, args.submission],
        text=True,
        capture_output=True,
        check=False,
    )
    explanation_warnings = write_audit("outputs/evidence_packets.jsonl", "outputs/explanation_audit.json")
    with Path(args.submission).open("r", encoding="utf-8", newline="") as handle:
        row_count = sum(1 for _ in csv.reader(handle)) - 1
    report = {
        "submission": args.submission,
        "row_count": row_count,
        "sha256": sha256(args.submission),
        "internal_error_count": len(internal_errors),
        "internal_errors": internal_errors,
        "official_validator_returncode": official.returncode,
        "official_validator_stdout": official.stdout.strip(),
        "official_validator_stderr": official.stderr.strip(),
        "explanation_warning_count": len(explanation_warnings),
        "explanation_warnings": explanation_warnings,
        "elapsed_seconds": round(time.perf_counter() - start, 3),
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not internal_errors and official.returncode == 0 and not explanation_warnings else 1


if __name__ == "__main__":
    raise SystemExit(main())


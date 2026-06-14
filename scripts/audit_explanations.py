#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from talentsignal.explanation_audit import write_audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-packets", default="outputs/evidence_packets.jsonl")
    parser.add_argument("--out", default="outputs/explanation_audit.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    warnings = write_audit(args.evidence_packets, args.out)
    print(f"Explanation audit warnings: {len(warnings)}")
    for warning in warnings[:20]:
        print(f"- {warning}")
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


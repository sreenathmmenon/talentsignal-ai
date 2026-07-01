#!/usr/bin/env python3
"""Pre-bake the 100K "Proof at scale" result to a static JSON.

The live 100K ranking loads the full candidate pool + the 146 MB embedding index
into memory (~1-2 GB peak) and takes ~30-70s. On a small hosted demo box (e.g.
Railway Hobby, ~512 MB) that would OOM or tie up the box per visitor. Since the
result is DETERMINISTIC, we bake it once here and the Studio serves the snapshot
instantly when the live data isn't present (the hosted case), while still ranking
live when the full dataset IS present (local dev).

  python3 scripts/prebake_challenge.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "outputs" / "challenge_prebaked.json"


def main() -> int:
    import importlib.util
    spec = importlib.util.spec_from_file_location("studio", ROOT / "studio.py")
    studio = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(studio)

    res = studio.do_challenge({"engine": "spine"})
    if res.get("error"):
        print(f"cannot pre-bake (live data needed to generate the snapshot): {res['error']}",
              file=sys.stderr)
        return 1
    res["from_cache"] = True
    res["live"] = False
    res["prebaked"] = True
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} — {res.get('total')} candidates, top-1 = "
          f"{res['top'][0]['candidate_id'] if res.get('top') else '?'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

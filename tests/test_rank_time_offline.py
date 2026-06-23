"""Stage-3 reproduction safety: the ranking-step import surface must NOT pull in
sentence-transformers or torch (those are precompute-only). If this test fails,
the hybrid rank step could attempt a model load / network call inside the
no-network sandbox and get disqualified.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_rank_time_imports_are_numpy_only() -> None:
    probe = (
        "import sys; sys.path.insert(0, 'src');"
        "from talentsignal.ranking import score_pool_hybrid, rank_candidates;"
        "from talentsignal import artifacts, semantic_match, consistency_audit, schema_profile;"
        "bad=[m for m in ('torch','sentence_transformers','transformers') if m in sys.modules];"
        "print('BAD' if bad else 'OK', bad)"
    )
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, cwd=str(ROOT))
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("OK"), result.stdout

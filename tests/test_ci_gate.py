"""The CI quality gate runs and passes on the current codebase. This makes the
gate itself part of the test suite, so a broken gate is caught too.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_gate_passes():
    r = subprocess.run([sys.executable, "scripts/ci_gate.py"],
                       capture_output=True, text=True, cwd=str(ROOT))
    assert r.returncode == 0, f"CI gate failed:\n{r.stdout}\n{r.stderr}"
    assert "CI GATE PASSED" in r.stdout


def test_workflow_file_exists():
    wf = ROOT / ".github" / "workflows" / "ci.yml"
    assert wf.exists()
    text = wf.read_text()
    assert "pytest" in text and "ci_gate.py" in text

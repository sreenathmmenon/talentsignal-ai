"""Reproduction packaging: the Dockerfile is offline-configured and the
reproduction verifier's no-network-import check holds. (The full 100K offline
reproduction is exercised by scripts/verify_reproduction.py, which needs the
challenge data; here we test the pieces that don't.)
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def test_dockerfile_is_offline_configured() -> None:
    text = (ROOT / "Dockerfile").read_text()
    assert "FROM python:3.11-slim" in text
    assert "HF_HUB_OFFLINE" in text and "TRANSFORMERS_OFFLINE" in text
    assert "requirements.txt" in text  # installs only the rank-time dep


def _deps(path: Path) -> list[str]:
    """Non-comment, non-blank requirement lines (package specs only)."""
    return [ln.strip() for ln in path.read_text().splitlines()
            if ln.strip() and not ln.strip().startswith("#")]


def test_requirements_split_keeps_rank_light() -> None:
    rank_deps = _deps(ROOT / "requirements.txt")
    assert any("numpy" in d for d in rank_deps)
    # heavy deps must NOT be actual rank-time requirements (comments don't count)
    assert not any("torch" in d for d in rank_deps)
    assert not any("sentence-transformers" in d for d in rank_deps)
    pre = _deps(ROOT / "requirements-precompute.txt")
    assert any("sentence-transformers" in d for d in pre)
    assert any("torch" in d for d in pre)  # they live here instead


def test_verifier_no_network_import_check() -> None:
    spec = importlib.util.spec_from_file_location(
        "verify_reproduction", ROOT / "scripts" / "verify_reproduction.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.check_no_network_imports() is True

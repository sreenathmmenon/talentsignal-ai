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


def test_requirements_split_keeps_rank_light() -> None:
    rank_reqs = (ROOT / "requirements.txt").read_text()
    assert "numpy" in rank_reqs
    # heavy deps must NOT be in the rank-time requirements
    assert "torch" not in rank_reqs and "sentence-transformers" not in rank_reqs
    pre = (ROOT / "requirements-precompute.txt").read_text()
    assert "sentence-transformers" in pre and "torch" in pre  # they live here instead


def test_verifier_no_network_import_check() -> None:
    spec = importlib.util.spec_from_file_location(
        "verify_reproduction", ROOT / "scripts" / "verify_reproduction.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.check_no_network_imports() is True

"""Load/save the precomputed semantic index — numpy + json ONLY.

This is the boundary that keeps the ranking step within budget and offline: the
expensive embedding work happens in precompute.py (which imports
sentence-transformers); everything at rank time goes through here and touches
only numpy arrays already on disk. This module must NEVER import
sentence-transformers or torch.

Index layout (under outputs/index/ by default):
    candidate_ids.json   ordered list of candidate_ids (row order of the matrix)
    embeddings.npy       float32 [N, D], L2-normalized candidate evidence vectors
    meta.json            {model, dim, count, normalized}

Requirement embeddings for a specific JD are stored separately (per-JD), since
they're tiny and JD-dependent:
    req_<job_id>.npy     float32 [R, D] aligned with the JD's requirement order
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore

DEFAULT_INDEX_DIR = "outputs/index"


def index_paths(index_dir: str | Path = DEFAULT_INDEX_DIR) -> dict[str, Path]:
    d = Path(index_dir)
    return {
        "dir": d,
        "ids": d / "candidate_ids.json",
        "embeddings": d / "embeddings.npy",
        "meta": d / "meta.json",
    }


def save_candidate_index(
    candidate_ids: list[str], embeddings, model_name: str, index_dir: str | Path = DEFAULT_INDEX_DIR
) -> None:
    """Persist the candidate embedding matrix + id order + metadata."""
    if np is None:
        raise RuntimeError("numpy required to save the index")
    p = index_paths(index_dir)
    p["dir"].mkdir(parents=True, exist_ok=True)
    arr = np.asarray(embeddings, dtype="float32")
    # L2-normalize so rank-time similarity is a plain dot product.
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    arr = arr / norms
    np.save(p["embeddings"], arr)
    p["ids"].write_text(json.dumps(candidate_ids), encoding="utf-8")
    p["meta"].write_text(json.dumps({
        "model": model_name, "dim": int(arr.shape[1]), "count": int(arr.shape[0]),
        "normalized": True,
    }, indent=2), encoding="utf-8")


def _is_lfs_pointer(path: Path) -> bool:
    """A Git-LFS pointer is a tiny text stub that a clone WITHOUT `git lfs pull`
    leaves in place of the real binary. Detect it so we can fail with an
    actionable message instead of a cryptic numpy pickle error."""
    try:
        if path.stat().st_size > 1024:
            return False  # real .npy is megabytes; pointers are ~130 bytes
        with path.open("rb") as fh:
            head = fh.read(64)
        return head.startswith(b"version https://git-lfs")
    except OSError:
        return False


def load_candidate_index(index_dir: str | Path = DEFAULT_INDEX_DIR):
    """Return (id_to_row: dict[str,int], embeddings: np.ndarray, meta: dict) or
    (None, None, None) if the index is absent (caller falls back to lexical).

    If the embeddings file is present but is an un-pulled Git-LFS pointer, raise
    a loud, actionable error rather than crashing on np.load or silently
    degrading to a different (lexical) ranking — the latter would produce a
    valid-but-WRONG top-100 that does not match the submitted CSV."""
    if np is None:
        return None, None, None
    p = index_paths(index_dir)
    if not (p["ids"].exists() and p["embeddings"].exists()):
        return None, None, None
    if _is_lfs_pointer(p["embeddings"]):
        raise RuntimeError(
            f"The embedding index at {p['embeddings']} is a Git-LFS pointer, not the "
            f"real file — this clone has not pulled LFS objects. Run:\n\n"
            f"    git lfs install && git lfs pull\n\n"
            f"then re-run. (Without the index the hybrid engine cannot reproduce the "
            f"submitted CSV.)"
        )
    ids = json.loads(p["ids"].read_text(encoding="utf-8"))
    emb = np.load(p["embeddings"], mmap_mode="r")  # mmap keeps RAM flat for 100K
    meta = json.loads(p["meta"].read_text(encoding="utf-8")) if p["meta"].exists() else {}
    id_to_row = {cid: i for i, cid in enumerate(ids)}
    return id_to_row, emb, meta


def save_requirement_embeddings(
    job_id: str, req_embeddings, index_dir: str | Path = DEFAULT_INDEX_DIR
) -> Path:
    if np is None:
        raise RuntimeError("numpy required")
    d = Path(index_dir)
    d.mkdir(parents=True, exist_ok=True)
    arr = np.asarray(req_embeddings, dtype="float32")
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    arr = arr / norms
    out = d / f"req_{job_id}.npy"
    np.save(out, arr)
    return out


def load_requirement_embeddings(job_id: str, index_dir: str | Path = DEFAULT_INDEX_DIR):
    if np is None:
        return None
    out = Path(index_dir) / f"req_{job_id}.npy"
    if not out.exists():
        return None
    if _is_lfs_pointer(out):
        raise RuntimeError(
            f"The requirement embeddings at {out} are a Git-LFS pointer, not the real "
            f"file. Run `git lfs install && git lfs pull` then re-run."
        )
    return np.load(out)


def evidence_text_of(candidate: dict[str, Any]) -> str:
    """The canonical evidence text we embed for a candidate: summary + career
    descriptions + skill names. Kept in one place so precompute and any live
    embedding use the EXACT same text (otherwise vectors wouldn't be comparable).
    """
    profile = candidate.get("profile", {}) or {}
    parts = [str(profile.get("summary", "")), str(profile.get("headline", ""))]
    for job in candidate.get("career_history", []) or []:
        if isinstance(job, dict):
            parts.append(str(job.get("title", "")))
            parts.append(str(job.get("description", "")))
    for skill in candidate.get("skills", []) or []:
        # skills may be {"name": ...} objects OR plain strings
        if isinstance(skill, dict):
            parts.append(str(skill.get("name", "")))
        elif isinstance(skill, str):
            parts.append(skill)
    return " ".join(p for p in parts if p).strip()

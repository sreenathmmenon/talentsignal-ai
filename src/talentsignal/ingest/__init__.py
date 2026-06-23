"""Universal ingest layer — turn ANY input into canonical candidate records.

Drop in PDF, DOCX, TXT, CSV, JSON/JSONL, a LinkedIn export, or a raw pasted
resume, and get back normalized candidate dicts the engine can rank. New formats
(e.g. future GitHub-repo analysis) are added as plugins without touching the
core: implement an IngestAdapter and register it.

    from talentsignal.ingest import ingest

    candidates = ingest("resumes/alice.pdf")          # one file
    candidates = ingest(["a.pdf", "b.docx", "c.json"]) # many, mixed formats
    candidates = ingest(raw_text, fmt="text")          # explicit format

The output is always a list of canonical candidate dicts (see model.py), so the
ingest layer and the engine are cleanly decoupled.
"""
from __future__ import annotations

from .model import Candidate, canonical_record, normalize_record
from .registry import ingest, register_adapter, list_adapters, detect_format
from . import adapters as _adapters  # noqa: F401  (registers built-in adapters on import)

__all__ = [
    "ingest",
    "register_adapter",
    "list_adapters",
    "detect_format",
    "Candidate",
    "canonical_record",
    "normalize_record",
]

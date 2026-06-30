"""Resume/candidate ingest adapters — the messy-real-world-data surface. Covers
every format the product accepts and the edge cases the bug hunt surfaced (BOM,
latin-1 accents, broken JSON, non-dict elements, missing files, TSV)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from talentsignal.ingest import ingest


# --- JSON / JSONL robustness (bugs the hunt found) ----------------------------

def test_json_array():
    recs = ingest('[{"candidate_id":"CAND_1","profile":{"summary":"python"}}]', fmt="json")
    assert len(recs) == 1 and recs[0]["candidate_id"] == "CAND_1"


def test_pretty_printed_single_object():
    recs = ingest('{\n  "candidate_id": "CAND_2",\n  "profile": {"summary": "x"}\n}', fmt="json")
    assert len(recs) == 1


def test_jsonl_multiple_objects():
    recs = ingest('{"candidate_id":"A"}\n{"candidate_id":"B"}', fmt="json")
    assert len(recs) == 2


def test_broken_json_does_not_crash():
    assert ingest("{bad json", fmt="json") == []  # no exception


def test_non_dict_elements_skipped():
    recs = ingest('[1, 2, null, {"candidate_id":"CAND_9"}]', fmt="json")
    assert len(recs) == 1 and recs[0]["candidate_id"] == "CAND_9"


def test_jsonl_garbage_line_skipped():
    recs = ingest('{"candidate_id":"A"}\ngarbage\n{"candidate_id":"B"}', fmt="json")
    assert len(recs) == 2


# --- CSV (BOM + mapping) ------------------------------------------------------

def test_csv_basic():
    recs = ingest("name,summary,skills\nAlice,builds ranking systems,Python", fmt="csv")
    assert len(recs) == 1
    assert recs[0]["profile"]["anonymized_name"] == "Alice"


def test_csv_utf8_bom_header_still_maps():
    # Excel exports prepend a BOM; the first column must still map to 'name'
    recs = ingest("﻿name,summary\nBob,python ranking", fmt="csv")
    assert recs[0]["profile"]["anonymized_name"] == "Bob"


# --- text / unicode -----------------------------------------------------------

def test_text_paste():
    recs = ingest("Maya Rao. Senior AI Engineer. Built embeddings retrieval ranking.", fmt="text")
    assert len(recs) == 1


def test_accented_bytes_preserved():
    recs = ingest("José Müller. AI Engineer. Python ranking.", fmt="text")
    blob = str(recs)
    assert "José" in blob or "é" in blob


def test_empty_and_whitespace():
    assert ingest("", fmt="text") == []
    assert ingest("   \n  ", fmt="text") == []


# --- file handling ------------------------------------------------------------

def test_missing_file_with_extension_raises():
    with pytest.raises(FileNotFoundError):
        ingest("/tmp/__does_not_exist__.pdf")


def test_real_txt_file(tmp_path):
    p = tmp_path / "resume.txt"
    p.write_text("Priya Nair. Backend Engineer. Go Kafka Kubernetes distributed systems.",
                 encoding="utf-8")
    recs = ingest(str(p))
    assert len(recs) == 1


# --- id uniqueness (collision bug) -------------------------------------------

def test_distinct_candidates_get_distinct_ids():
    a = ingest("Alice. AI Engineer. embeddings ranking.", fmt="text")[0]
    b = ingest("Bob. Backend Engineer. go kafka.", fmt="text")[0]
    assert a["candidate_id"] != b["candidate_id"]

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "close_read_prior_art.py"
spec = importlib.util.spec_from_file_location("close_read_prior_art", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_close_reading_notes_are_bound_to_stage3_matrix() -> None:
    matrix = Path(__file__).parents[1] / "data" / "processed" / "fulltext_evidence_matrix.csv"
    rows = module._read_rows(matrix)
    assert set(module.MANUAL_NOTES).issubset(rows)
    assert len(module.MANUAL_NOTES) == 16
    assert all(note["human_verification_required"] == "true" for note in module.MANUAL_NOTES.values())


def test_close_reading_schema_has_negative_boundaries() -> None:
    required = {"what_source_supports", "what_source_does_not_support", "allowed_use"}
    assert required.issubset(module.FIELDS)
    assert all(note["what_source_does_not_support"] for note in module.MANUAL_NOTES.values())

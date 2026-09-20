from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_v3_close_reading_tracker.py"
spec = importlib.util.spec_from_file_location("build_v3_close_reading_tracker", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_tracker_distinguishes_card_access_and_pending(tmp_path: Path) -> None:
    (tmp_path / "A_first.md").write_text("# card\n", encoding="utf-8")
    queue = [
        {"candidate_id": "A", "priority_tier": "P0", "review_targets_routing_only": "SP1", "title": "has card"},
        {"candidate_id": "B", "priority_tier": "P0", "review_targets_routing_only": "SP2", "title": "ready"},
        {"candidate_id": "C", "priority_tier": "P1", "review_targets_routing_only": "SP3", "title": "blocked"},
    ]
    audit = [
        {"candidate_id": "A", "close_reading_eligibility": "eligible"},
        {"candidate_id": "B", "close_reading_eligibility": "eligible"},
        {"candidate_id": "C", "close_reading_eligibility": "requires_alternative_or_manual_inspection"},
    ]
    rows = module.make_tracker(queue, audit, tmp_path)
    assert [row["close_reading_status"] for row in rows] == [
        "completed_passage_localized_card",
        "ready_for_close_reading",
        "requires_fulltext_or_manual_access_check",
    ]

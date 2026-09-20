from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_v3_reading_packet.py"
spec = importlib.util.spec_from_file_location("build_v3_reading_packet", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_excerpt_marks_source_page() -> None:
    excerpts = module.excerpt_block(["Abstract. Intro text.", "Methods and results are here.", "Conclusion: constrained scope."])
    assert any(label == "Conclusión o limitación" and page == 3 for label, page, _ in excerpts)


def test_build_packet_applies_offset_after_eligibility() -> None:
    rows = [
        {"candidate_id": "A", "priority_tier": "P0", "title": "A", "authors": "", "year": "", "venue": "", "doi": "", "priority_score": "1", "review_targets_routing_only": "", "fulltext_local_path": "x"},
        {"candidate_id": "B", "priority_tier": "P0", "title": "B", "authors": "", "year": "", "venue": "", "doi": "", "priority_score": "1", "review_targets_routing_only": "", "fulltext_local_path": "x"},
    ]
    audit = {"A": {"close_reading_eligibility": "eligible"}, "B": {"close_reading_eligibility": "eligible"}}
    packet = module.build_packet(rows, audit, "P0", limit=1, offset=1)
    assert "## 1. B" in packet
    assert "## 1. A" not in packet

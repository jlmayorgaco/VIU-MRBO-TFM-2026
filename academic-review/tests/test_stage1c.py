from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "stage1c.py"
spec = importlib.util.spec_from_file_location("stage1c", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_query_repair_round_is_bounded() -> None:
    config = module.yaml.safe_load(module.REPAIR_CONFIG.read_text(encoding="utf-8"))

    assert len(config["query_families"]) <= config["max_query_families"] <= 12
    assert len({item["id"] for item in config["query_families"]}) == len(config["query_families"])


def test_new_query_record_preserves_evidence_boundary() -> None:
    record = module.prepare_new_record(
        {
            "candidate_id": "C_TEST",
            "provenance": "openalex",
            "provenance_sources": "openalex",
            "provenance_queries": "Q8_game_dynamics",
            "evidence_status": "not_evidence",
            "screening_status": "pending",
        },
        "Q8_game_dynamics",
    )

    assert record["evidence_status"] == "not_evidence"
    assert record["screening_status"] == "pending"
    assert "stage1c_query_repair" in record["provenance"]

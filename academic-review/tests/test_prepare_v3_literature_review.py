from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "prepare_v3_literature_review.py"
spec = importlib.util.spec_from_file_location("prepare_v3_literature_review", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_targets_route_without_claiming_evidence() -> None:
    row = {
        "title": "Distributed coalition formation for cooperative payload transport",
        "coordination_architecture": "distributed; coalition",
        "physical_layer": "payload; wrench",
    }
    assert {"SP1", "SP2"}.issubset(module.derive_targets(row))


def test_priority_keeps_core_transport_ahead_of_context() -> None:
    core = {"scientific_role": "CORE", "title": "Cooperative transport", "physical_layer": "payload", "doi": "10.1/x"}
    context = {"scientific_role": "CONTEXT", "title": "Warehouse overview", "doi": ""}
    assert module.priority_score(core, module.derive_targets(core)) > module.priority_score(context, module.derive_targets(context))


def test_routing_ignores_structural_terms_without_metadata_support() -> None:
    row = {"title": "A general systems paper", "method": "auction; caging; navigation"}
    assert module.derive_targets(row) == ["CONTEXT"]


def test_query_ledger_marks_history_as_not_a_v3_execution() -> None:
    rows = module.query_ledger_rows(
        [{"database": "web_of_science", "execution_id": "F01_primary", "query_id": "F01", "exact_query": "x"}],
        {"F01_primary": {"status": "partial", "expected_records": 80, "observed_records": 50}},
    )
    assert rows[0]["historical_status"] == "partial"
    assert rows[0]["v3_execution_status"] == "not_queried"

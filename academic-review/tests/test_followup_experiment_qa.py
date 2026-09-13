from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "followup_experiment_qa.py"
spec = importlib.util.spec_from_file_location("followup_experiment_qa", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_missing_manifest_is_not_interpreted_as_result(monkeypatch) -> None:
    monkeypatch.setattr(
        module,
        "CAMPAIGNS",
        (
            {
                "campaign": "MISSING_TEST_CAMPAIGN",
                "config": "tests/does_not_exist.yaml",
                "manifest": "results/does_not_exist/manifest.json",
                "notes": "test",
            },
        ),
    )
    rows = module.collect()
    missing = [row for row in rows if row["present"] == "false"]
    assert missing
    assert all(row["status"] == "not_run" for row in missing)


def test_campaign_registry_keeps_required_gates() -> None:
    specs = {row["campaign"]: row for row in module.CAMPAIGNS}
    assert "PASS pilot audit" in specs["SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2"]["notes"]
    assert "CARGO_E2E_CONFIRMATORY_v1" in specs
    assert len(specs) == 8

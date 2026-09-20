from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "multisource-v2" / "scripts" / "run_multisource_v2.py"
spec = importlib.util.spec_from_file_location("multisource_v2_under_test", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_query_plan_contains_primary_and_foundational_windows():
    config = module.yaml.safe_load(module.CONFIG.read_text(encoding="utf-8"))
    plan = module.query_plan(config)
    assert len(plan) == 22
    assert {row["window_id"] for row in plan} == {"primary", "foundational"}
    assert all(row["from_year"] <= row["to_year"] for row in plan)
    assert {row["query_id"] for row in plan} == {f"F{i:02d}" for i in range(1, 17)}


def test_identity_key_prefers_normalized_doi():
    assert module.identity_key({"doi_norm": "https://doi.org/10.1000/ABC"}) == "doi:10.1000/abc"
    assert module.identity_key({"title": "A Shared Payload", "year": "2024"}) == "tav:a shared payload|2024"


def test_unique_by_source_does_not_drop_records_from_other_sources():
    rows = [
        {"source": "arxiv", "doi_norm": "10.1000/x", "title": "x", "year": "2024"},
        {"source": "arxiv", "doi_norm": "10.1000/x", "title": "x duplicate", "year": "2024"},
        {"source": "dblp", "doi_norm": "10.1000/x", "title": "x", "year": "2024"},
    ]
    grouped = module.unique_by_source(rows)
    assert len(grouped["arxiv"]) == 1
    assert len(grouped["dblp"]) == 1


def test_openaire_wrapper_is_normalized_without_fabricating_missing_fields():
    item = {
        "id": "openaire:1",
        "metadata": {
            "oaf:entity": {
                "oaf:result": {
                    "title": {"$": "Distributed Payload Transport"},
                    "creator": [{"name": {"$": "A. Researcher"}}],
                    "pid": [{"classid": "doi", "$": "10.1000/test"}],
                }
            }
        },
    }
    parsed = module.openaire_result(item)
    assert parsed["title"] == "Distributed Payload Transport"
    assert parsed["doi"] == "10.1000/test"
    assert parsed["year"] == ""


def test_metadata_candidate_retains_no_evidence_state():
    row = module.record("arxiv", "F01", "primary", title="A paper", year="2024", source_id="2401.00001")
    assert row is not None
    assert row["evidence_status"] == "not_evidence"
    assert row["screening_status"] == "pending"

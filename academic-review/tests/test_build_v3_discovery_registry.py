from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_v3_discovery_registry.py"
spec = importlib.util.spec_from_file_location("build_v3_discovery_registry", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_registry_merges_doi_and_resets_v3_screening() -> None:
    seed = {"candidate_id": "SEED", "title": "Coalition Method", "year": "2020", "doi": "10.1/Example", "screening_decision": "include_fulltext", "fulltext_status": "verified", "evidence_status": "not_evidence", "provenance": "crossref", "provenance_sources": "crossref", "provenance_queries": "legacy"}
    open_record = {"candidate_id": "OPEN", "title": "Coalition Method", "year": "2020", "doi_norm": "10.1/example", "abstract": "verified metadata", "provenance_sources": "openalex", "provenance_queries": "F01:primary", "metadata_verification_status": "metadata_verified"}
    registry, aliases = module.build_registry([seed], [open_record], {})
    assert len(registry) == 1
    assert registry[0]["candidate_ids"] == "SEED;OPEN"
    assert registry[0]["v3_screening_status"] == "not_screened"
    assert registry[0]["abstract"] == "verified metadata"
    assert sum(aliases.values()) == 1

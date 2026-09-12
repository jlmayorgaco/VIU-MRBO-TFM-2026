from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "stage3_code.py"
spec = importlib.util.spec_from_file_location("stage3_code", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_abstract_only_does_not_create_fulltext_evidence() -> None:
    row = {
        "candidate_id": "C1", "title": "Cooperative Transport", "authors": "A", "year": "2024", "venue": "V",
        "doi_norm": "10.1234/example", "document_type": "article", "screening_decision": "include_fulltext",
        "fulltext_status": "abstract_only", "abstract": "We study cooperative transport using consensus.",
        "fulltext_local_path": "", "fulltext_sha256": "",
    }
    coded = module.code_row(row, "hash")
    assert coded["evidence_strength"] == "abstract_only"
    assert coded["coding_status"] == "coded_abstract_limited"
    assert coded["physical_layer"] == ""
    assert coded["coordination_architecture"] == "consensus"


def test_metadata_only_has_no_detailed_fields() -> None:
    row = {"candidate_id": "C2", "title": "Multi-Robot Task Allocation", "fulltext_status": "unavailable_legally", "abstract": ""}
    coded = module.code_row(row, "hash")
    assert coded["evidence_strength"] == "metadata_only"
    assert coded["coding_status"] == "not_codeable_without_fulltext"
    assert coded["method"] == ""


def test_term_location_records_page_and_snippet() -> None:
    found = module.evidence_for_field(["Intro\nConsensus-based allocation reduces messages."], ["consensus-based"])
    assert found and found[0]["page"] == 1 and "allocation" in found[0]["snippet"].lower()


def test_role_assignment_keeps_survey_distinct() -> None:
    row = {"title": "A Survey of Multi-Robot Systems", "document_type": "review"}
    assert module.role_for(row, "", {name: [] for name in module.PATTERNS}) == "SURVEY"

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "stage5_finalize.py"
spec = importlib.util.spec_from_file_location("stage5_finalize", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_citation_never_invents_missing_doi() -> None:
    assert module.cite({"title": "Example", "year": "2024", "doi": ""}) == "Example (2024; DOI no disponible)"


def test_top_terms_drops_unclear_placeholder() -> None:
    rows = [{"x": "auction;unclear"}, {"x": "auction;consensus"}]
    assert module.top_terms(rows, "x") == [("auction", 2), ("consensus", 1)]


def test_claim_ledger_protocol_status_vocabulary_is_documented() -> None:
    allowed = {"supported", "partially_supported", "contradicted", "unclear", "not_tested"}
    assert allowed == set(module.CLAIM_SUPPORT_STATUSES)

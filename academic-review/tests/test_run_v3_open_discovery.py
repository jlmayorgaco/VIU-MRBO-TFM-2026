from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "run_v3_open_discovery.py"
spec = importlib.util.spec_from_file_location("run_v3_open_discovery", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_build_plan_uses_frozen_query_and_window() -> None:
    rows = [{"source": "web_of_science", "execution_id": "F01_primary", "query_id": "F01", "window_id": "primary", "exact_query": "multi-robot coalition formation", "from_year": "2000", "to_year": "2026"}]
    assert module.build_plan(rows) == [{"execution_id": "F01_primary", "query_id": "F01", "window_id": "primary", "query": "multi-robot coalition formation", "from_year": 2000, "to_year": 2026}]


def test_merged_records_retains_source_and_query_provenance() -> None:
    records = [
        {"candidate_id": "A", "doi_norm": "10.1/example", "title_norm": "one", "provenance_sources": "crossref", "provenance_queries": "F01:primary", "source_ids": "crossref:doi", "citation_count": "3", "abstract": "", "open_access_url": ""},
        {"candidate_id": "B", "doi_norm": "10.1/example", "title_norm": "one", "provenance_sources": "openalex", "provenance_queries": "F01:primary", "source_ids": "openalex:id", "citation_count": "7", "abstract": "abstract", "open_access_url": "https://oa.example"},
    ]
    merged = module.merged_records(records)
    assert len(merged) == 1
    assert merged[0]["citation_count"] == "7"
    assert merged[0]["provenance_sources"] == "crossref;openalex"
    assert merged[0]["abstract"] == "abstract"


def test_retain_other_sources_removes_only_refreshed_source(tmp_path: Path) -> None:
    path = tmp_path / "events.csv"
    path.write_text("source,status\ncrossref,ok\narxiv,failed\n", encoding="utf-8")
    assert module.retain_other_sources(path, ["crossref"]) == [{"source": "arxiv", "status": "failed"}]

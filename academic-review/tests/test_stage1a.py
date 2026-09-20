from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "bootstrap_literature.py"
spec = importlib.util.spec_from_file_location("bootstrap_literature", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_seed_record_preserves_evidence_boundary_and_raw_fields() -> None:
    module.INPUT = Path(__file__).parents[1] / "inputs"
    rows = module.load_seed()

    assert len(rows) == 32
    assert all(row["verification_status"] == "unverified_seed" for row in rows)
    assert all(row["evidence_status"] == "not_evidence" for row in rows)
    assert all(row["screening_status"] == "pending" for row in rows)
    assert all(row["seed_raw"] for row in rows)
    assert all(row["title_original"] == row["title"] for row in rows)


def test_doi_is_strong_match_but_ambiguous_non_doi_pair_is_retained() -> None:
    first = {
        "candidate_id": "C1",
        "title": "Cooperative Transport",
        "title_norm": module.norm_title("Cooperative Transport"),
        "authors": "A. Alpha",
        "year": "2020",
        "venue": "Robotics Journal",
        "doi_norm": "",
        "provenance_sources": "source_a",
        "provenance_queries": "q1",
        "verification_status": "metadata_verified",
        "metadata_verification_status": "metadata_verified",
        "evidence_status": "not_evidence",
        "screening_status": "pending",
        "duplicate_status": "unique",
        "dedup_status": "unique",
    }
    second = dict(first)
    second.update({"candidate_id": "C2", "authors": "B. Beta", "provenance_sources": "source_b"})

    canonical, edges = module.merge_records([first, second])

    assert len(canonical) == 2
    assert all(row["duplicate_status"] == "needs_review" for row in canonical)
    assert any(edge["relation"].startswith("possible_duplicate_") for edge in edges)


def test_request_hash_is_deterministic() -> None:
    params = {"b": 2, "a": "x"}
    assert module.request_hash("https://example.test", params) == module.request_hash("https://example.test", params)


def test_openalex_query_translation_preserves_terms_without_boolean_syntax() -> None:
    query = '("multi-robot" OR AMR) AND (transport* OR payload)'

    assert module.openalex_search_query(query) == "multi-robot AMR transport payload"


def test_crossref_missing_year_is_not_serialized_as_none() -> None:
    record = module.crossref_item_to_record(
        {
            "DOI": "10.1234/example",
            "title": ["Example"],
            "issued": {"date-parts": [[None]]},
        },
        "test",
    )

    assert record["year"] == ""


def test_seed_metadata_enrichment_does_not_promote_seed_verification() -> None:
    seed = module.load_seed()[0]

    class FakeHttp:
        def get_json(self, source, kind, url, params=None):
            return {
                "message": {
                    "DOI": seed["doi_norm"],
                    "title": [seed["title"]],
                    "author": [{"family": "Alpha", "given": "A."}],
                    "published": {"date-parts": [[int(seed["year"])]]},
                    "container-title": [seed["venue"]],
                    "type": "journal-article",
                    "is-referenced-by-count": 0,
                }
            }

    enriched = module.enrich_seeds([seed], FakeHttp(), "test@example.org")

    assert enriched[0]["verification_status"] == "unverified_seed"
    assert enriched[0]["metadata_verification_status"] == "metadata_verified"


def test_parse_wos_tagged_plaintext_preserves_multiline_metadata() -> None:
    text = """FN Clarivate Analytics Web of Science
VR 1.0
PT J
AU Doe, J
   Smith, A
AF Doe, Jane
   Smith, Alex
TI Distributed multi-robot
   coalition formation
SO JOURNAL OF ROBOTICS
AB A multiline abstract
   with a continuation.
DI 10.1234/EXAMPLE.1
PY 2024
TC 7
UT WOS:000000000000001
ER
"""

    records = module.parse_wos_tagged_plaintext(text)

    assert len(records) == 1
    assert records[0]["TI"] == "Distributed multi-robot coalition formation"
    assert records[0]["AF"] == "Doe, Jane; Smith, Alex"
    assert records[0]["AB"] == "A multiline abstract with a continuation."


def test_parse_wos_tagged_plaintext_uses_each_bare_er_as_a_record_boundary() -> None:
    records = module.parse_wos_tagged_plaintext("PT J\nTI First\nER\nPT C\nTI Second\nER\n")

    assert [record["TI"] for record in records] == ["First", "Second"]


def test_wos_tagged_record_is_metadata_only_and_keeps_query_provenance() -> None:
    values = {
        "title": "A field-tagged WoS record",
        "doi": "https://doi.org/10.1234/EXAMPLE",
        "year": "2024",
        "ut": "WOS:000000000000001",
        "authors": "Doe, Jane",
        "venue": "Journal of Tests",
        "abstract": "Metadata only.",
        "document_type": "Article",
        "citation_count": "3",
    }

    row = module.wos_record_from_values(values, Path("F03_primary_export.txt"))

    assert row is not None
    assert row["provenance_queries"] == "F03_primary"
    assert row["evidence_status"] == "not_evidence"
    assert row["screening_status"] == "pending"


def test_partial_wos_manifest_never_claims_complete_reconciliation(tmp_path) -> None:
    raw = tmp_path / "wos"
    raw.mkdir()
    export = raw / "F01_primary_wos.txt"
    export.write_text("PT J\nTI Example\nER\n", encoding="utf-8")
    manifest = raw / "wos_export_manifest.json"
    manifest.write_text(
        '{"exports":[{"file":"F01_primary_wos.txt","status":"partial"}]}',
        encoding="utf-8",
    )
    original_input, original_manifest = module.INPUT, module.WOS_EXPORT_MANIFEST
    try:
        module.INPUT = tmp_path
        module.WOS_EXPORT_MANIFEST = manifest
        assert module.wos_coverage_label(module.wos_raw_files()) == "wos_partially_reconciled"
    finally:
        module.INPUT, module.WOS_EXPORT_MANIFEST = original_input, original_manifest

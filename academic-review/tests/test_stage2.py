from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "stage2_acquire.py"
spec = importlib.util.spec_from_file_location("stage2_acquire", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def row(title: str = "Distributed Cooperative Transport of a Shared Payload", doi: str = "10.1234/example") -> dict[str, str]:
    return {"title": title, "doi_norm": doi}


def test_status_vocabulary_is_exactly_configured() -> None:
    assert module.ALLOWED_STATUSES == {
        "acquired_pdf", "acquired_html", "acquired_xml", "abstract_only", "unavailable_legally", "retrieval_error"
    }


def test_pdf_identity_accepts_matching_doi() -> None:
    payload = b"Distributed Cooperative Transport of a Shared Payload DOI: 10.1234/example Introduction Methods Results"
    status, _, score = module.identity_check(row(), payload, "html")
    assert status == "identity_verified_doi"
    assert score >= 1.0


def test_identity_rejects_conflicting_doi() -> None:
    payload = b"Distributed Cooperative Transport of a Shared Payload DOI: 10.9999/other Introduction Methods Results"
    status, _, _ = module.identity_check(row(), payload, "html")
    assert status == "identity_mismatch_doi"


def test_fulltext_structure_does_not_accept_abstract_landing_page() -> None:
    payload = b"<html><head><title>Distributed Cooperative Transport of a Shared Payload</title></head><body><article><h1>Distributed Cooperative Transport of a Shared Payload</h1><h2>Abstract</h2><p>Short abstract only.</p></article></body></html>"
    assert module.classify_body(payload, "text/html", "landing") == "html"
    assert not module.looks_like_fulltext(payload, "html")


def test_open_host_detection_is_conservative() -> None:
    assert module.host_is_open("pmc.ncbi.nlm.nih.gov")
    assert not module.host_is_open("example-paywall.invalid")

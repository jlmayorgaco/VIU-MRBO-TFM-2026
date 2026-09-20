from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "audit_v3_fulltexts.py"
spec = importlib.util.spec_from_file_location("audit_v3_fulltexts", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_substantive_html_requires_multiple_body_sections() -> None:
    text = "Abstract Introduction " + ("content " * 1600) + " Methods Results Conclusion References"
    result, markers = module.classify_text(Path("paper.html"), text, 1)
    assert result == "substantive_html_text"
    assert {"introduction", "methods", "results", "conclusion"}.issubset(markers)


def test_short_pdf_is_not_close_reading_eligible() -> None:
    result, _ = module.classify_text(Path("scan.pdf"), "Abstract", 1)
    assert result == "pdf_needs_ocr_or_alternative"


def test_paywalled_html_preview_is_not_eligible_even_with_navigation_text() -> None:
    text = "Abstract Introduction Methods Results " + ("navigation " * 1700) + " This is a preview of subscription content. Access this chapter."
    result, _ = module.classify_text(Path("preview.html"), text, 1)
    assert result == "landing_or_abstract_like_html"

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "analyze_v3_literature.py"
spec = importlib.util.spec_from_file_location("analyze_v3_literature", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_abstract_extraction_stops_before_introduction() -> None:
    text = "Header Abstract " + ("coalition evidence " * 60) + " Keywords robots Introduction unrelated"
    abstract = module.abstract_from_text(text)
    assert "coalition evidence" in abstract
    assert "unrelated" not in abstract


def test_abstract_extraction_rejects_late_reference_abstract() -> None:
    text = ("front matter " * 5000) + "Abstract machine learning reference entry"
    assert module.abstract_from_text(text) == ""


def test_abstract_extraction_stops_at_paywall_navigation() -> None:
    text = "Abstract " + ("formation control " * 45) + " This is a preview of subscription content. Suggested using machine learning."
    abstract = module.abstract_from_text(text)
    assert "formation control" in abstract
    assert "machine learning" not in abstract


def test_body_removes_late_reference_list() -> None:
    text = ("method content " * 100) + "References reinforcement learning citation"
    body = module.body_without_references(text)
    assert "method content" in body
    assert "reinforcement learning citation" not in body


def test_signals_are_multilabel_and_explicit() -> None:
    text = "A decentralized auction for coalition formation with packet loss"
    assert "SP1_coalition_allocation" in module.signals(text, module.THEMES)
    assert "TRANSVERSAL_resilience_communication" in module.signals(text, module.THEMES)
    assert "auction_market" in module.signals(text, module.METHODS)
    assert "distributed_decentralized" in module.signals(text, module.ARCHITECTURES)


def test_method_lifecycle_does_not_call_sparse_method_dead() -> None:
    rows = [{"year": "2025", "period": "2022-2026", "method_focus_title_abstract": "game_theoretic"}]
    lifecycle = {row["method"]: row for row in module.method_lifecycle(rows)}
    assert lifecycle["game_theoretic"]["descriptive_status"] == "sparse_or_indeterminate"
    assert "died" not in lifecycle["game_theoretic"]["descriptive_status"]


def test_canonical_venue_merges_case_and_html_variants() -> None:
    assert module.canonical_venue("IEEE ACCESS") == "IEEE Access"
    assert module.canonical_venue("Journal of Intelligent &amp; Robotic Systems") == "Journal of Intelligent & Robotic Systems"
    assert module.canonical_venue("arXiv (Cornell University)") == "arXiv"


def test_version_of_record_year_override_is_explicit() -> None:
    assert module.YEAR_OVERRIDES["CF7C60AFD9DE7"] == "2022"

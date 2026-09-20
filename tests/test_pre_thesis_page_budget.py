"""Regression tests for the conservative VIU page-budget interpretation."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPOSITORY_ROOT / "pre-thesis" / "scripts" / "verify_build.py"
SPEC = importlib.util.spec_from_file_location("pre_thesis_verify_build", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
VERIFY_BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY_BUILD)


def final_markers() -> dict[str, int]:
    """Return a synthetic marker layout for the binding 97-page budget."""

    return {
        "budget:body-start": 13,
        "budget:objectives-start": 17,
        "budget:hypotheses-start": 19,
        "budget:methodology-start": 21,
        "budget:theory-start": 29,
        "budget:body-end": 81,
        "budget:results-start": 39,
        "budget:results-end": 77,
        "budget:references-start": 82,
        "budget:references-end": 89,
        "budget:appendices-start": 90,
        "budget:appendices-end": 97,
        "budget:results-interface-start": 39,
        "budget:results-interface-end": 41,
        "budget:sp1-start": 42,
        "budget:sp1-end": 51,
        "budget:sp2-start": 52,
        "budget:sp2-end": 67,
        "budget:sp3-start": 68,
        "budget:sp3-end": 75,
        "budget:results-synthesis-start": 76,
        "budget:results-synthesis-end": 77,
        "budget:conclusions-start": 78,
    }


def test_final_budget_passes_both_body_interpretations() -> None:
    errors, metrics = VERIFY_BUILD.page_budget_errors(final_markers(), total=97)

    assert errors == []
    assert metrics["body"] == 69
    assert metrics["body_including_references"] == 77
    assert metrics["results"] == 39
    assert metrics["results_fraction_of_body"] == 39 / 69
    assert metrics["results_fraction_of_body_including_references"] == 39 / 77
    assert metrics["results_interface_and_protocol"] == 3
    assert metrics["results_sp1"] == 10
    assert metrics["results_sp2"] == 16
    assert metrics["results_sp3"] == 8
    assert metrics["results_synthesis"] == 2
    assert metrics["chapter_introduction"] == 4
    assert metrics["chapter_objectives"] == 2
    assert metrics["chapter_hypotheses"] == 2
    assert metrics["chapter_methodology"] == 8
    assert metrics["chapter_theoretical_framework"] == 10
    assert metrics["chapter_results_and_analysis"] == 39
    assert metrics["chapter_conclusions"] == 4


def test_conservative_results_fraction_is_enforced() -> None:
    markers = final_markers()
    markers["budget:results-start"] = 43

    errors, metrics = VERIFY_BUILD.page_budget_errors(markers, total=98)

    assert metrics["results_fraction_of_body"] > 0.50
    assert metrics["results_fraction_of_body_including_references"] < 0.50
    assert any(
        error.startswith("results_fraction_of_body_including_references=")
        for error in errors
    )


def test_conservative_body_limit_is_enforced() -> None:
    markers = final_markers()
    markers["budget:body-start"] = 9

    errors, metrics = VERIFY_BUILD.page_budget_errors(markers, total=98)

    assert metrics["body_including_references"] == 81
    assert "body_including_references=81 > máximo 80" in errors


def test_results_subsection_budget_is_binding() -> None:
    markers = final_markers()
    markers["budget:sp3-start"] = 67

    errors, metrics = VERIFY_BUILD.page_budget_errors(markers, total=98)

    assert metrics["results_sp2"] == 15
    assert "results_sp2=15 < mínimo 16" in errors


def test_subsection_span_counts_a_float_flushed_before_next_section() -> None:
    markers = final_markers()
    markers["budget:sp1-end"] = 50

    errors, metrics = VERIFY_BUILD.page_budget_errors(markers, total=97)

    assert errors == []
    assert metrics["results_sp1"] == 10


def test_chapter_budget_is_binding() -> None:
    markers = final_markers()
    markers["budget:theory-start"] = 28

    errors, metrics = VERIFY_BUILD.page_budget_errors(markers, total=97)

    assert metrics["chapter_methodology"] == 7
    assert metrics["chapter_theoretical_framework"] == 11
    assert "chapter_methodology=7 != objetivo 8" in errors
    assert "chapter_theoretical_framework=11 != objetivo 10" in errors

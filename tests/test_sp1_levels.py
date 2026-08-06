"""Regression tests for the four-level SP1 publication pipeline."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from PIL import Image
from pypdf import PdfReader


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from sp1_levels_common import (  # noqa: E402
    LEVELS_OUTPUT_ROOT,
    bool_to_float,
    fit_power_law,
    sha256_file,
)


def test_power_law_fit_recovers_known_exponent() -> None:
    x_values = np.array([2.0, 4.0, 8.0, 16.0])
    y_values = 3.5 * x_values**2.25
    fit = fit_power_law(x_values, y_values)
    assert fit.n_points == 4
    assert fit.exponent == pytest.approx(2.25, abs=1e-12)
    assert fit.scale == pytest.approx(3.5, abs=1e-12)
    assert fit.r_squared == pytest.approx(1.0, abs=1e-12)


def test_power_law_fit_ignores_invalid_points() -> None:
    fit = fit_power_law([0.0, 1.0, 2.0, math.nan], [4.0, 2.0, 8.0, 3.0])
    assert fit.n_points == 2
    assert fit.exponent == pytest.approx(2.0)


def test_bool_normalization_preserves_missing_values() -> None:
    values = pd.Series([True, False, "true", "0", None, 1])
    normalized = bool_to_float(values)
    assert normalized.iloc[:4].tolist() == [1.0, 0.0, 1.0, 0.0]
    assert math.isnan(float(normalized.iloc[4]))
    assert normalized.iloc[5] == 1.0


def test_level_manifests_reference_unchanged_sources() -> None:
    active_level_dirs = {
        "n1": "n1_v2",
        "n2": "n2",
        "n3": "n3",
        "n4": "n4",
    }
    for level, directory in active_level_dirs.items():
        manifest_path = LEVELS_OUTPUT_ROOT / directory / "manifest.json"
        assert manifest_path.is_file(), f"missing {manifest_path}"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["level"] == level.upper()
        assert manifest["row_counts"]
        for source in manifest["sources"]:
            source_path = REPOSITORY_ROOT / source["path"]
            assert source_path.is_file()
            assert source["sha256"] == sha256_file(source_path)


def test_comparison_scopes_are_not_conflated() -> None:
    comparison_dir = LEVELS_OUTPUT_ROOT / "comparison"
    n1_n2 = json.loads(
        (comparison_dir / "n1_n2_manifest.json").read_text(encoding="utf-8")
    )
    n3_n4 = json.loads(
        (comparison_dir / "n3_n4_manifest.json").read_text(encoding="utf-8")
    )
    assert "homogeneous" in n1_n2["scope"]
    assert "distributed" in n3_n4["scope"]
    assert n1_n2["metrics"]["controlled_rows"] > 0
    assert n3_n4["metrics"]["composite_passed"] == 0


def test_pdf_has_exact_requested_page_budget() -> None:
    pdf_path = (
        REPOSITORY_ROOT
        / "output"
        / "pdf"
        / "sp1_n1_10p"
        / "SP1_N1_10P.pdf"
    )
    assert pdf_path.is_file()
    reader = PdfReader(str(pdf_path))
    assert len(reader.pages) == 10
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "EXPERIMENTO E4" in text
    assert "NIVEL 2 DE 4" not in text


def test_n1_confirmatory_package_has_frozen_counts_and_invariants() -> None:
    n1_root = LEVELS_OUTPUT_ROOT / "n1_v2"
    metrics = json.loads((n1_root / "key_metrics.json").read_text(encoding="utf-8"))
    assert metrics["campaign_id"] == "SP1_N1_HUNGARIAN_CONFIRMATORY_v2"
    assert metrics["raw_rows"] == 12_630
    assert metrics["independent_worlds"] == 6_630
    assert metrics["quality_rows"] == 4_500
    assert metrics["scaling_rows"] == 630
    assert metrics["failure_rows"] == 6_000
    assert metrics["heterogeneity_rows"] == 1_500
    assert metrics["quality_feasibility_rate"] == pytest.approx(1.0)
    assert metrics["quality_constraint_violations"] == 0
    assert metrics["memory_formula_max_relative_error"] == pytest.approx(0.0)
    assert metrics["failure_theory_agreement_rate"] == pytest.approx(1.0)
    assert metrics["scaling_max_n"] == 2_048
    assert metrics["scaling_max_m"] == 2_048
    assert metrics["scaling_completed_count"] == 630
    assert metrics["scaling_failed_count"] == 0
    assert metrics["milp_audit_count"] == 1_500
    assert metrics["milp_feasible_incumbent_count"] == 1_500
    assert metrics["milp_certified_count"] == 1_495
    assert metrics["milp_uncertified_count"] == 5
    assert metrics["false_feasible_count"] == 900
    assert metrics["milp_rescue_count_among_false"] == 897
    assert metrics["milp_uncertified_false_count"] == 3
    assert metrics["milp_uncertified_gap_min"] > 0.0
    assert metrics["milp_uncertified_gap_max"] < 0.02


def test_n1_confirmatory_results_support_stated_validity_boundary() -> None:
    n1_root = LEVELS_OUTPUT_ROOT / "n1_v2"
    heterogeneity = pd.read_csv(
        n1_root / "processed" / "heterogeneity_summary.csv"
    )
    contrasts = pd.read_csv(
        n1_root / "processed" / "heterogeneity_contrasts.csv"
    )
    aggregate = (
        heterogeneity.groupby("capacity_mode", sort=False)
        .apply(
            lambda group: np.average(
                group["false_feasible_rate"], weights=group["n_worlds"]
            ),
            include_groups=False,
        )
        .to_dict()
    )
    assert aggregate["homogeneous"] == pytest.approx(0.0)
    assert aggregate["low"] > 0.0
    assert aggregate["extreme"] > aggregate["low"]
    assert len(contrasts) == 4
    assert contrasts["supported"].all()
    assert (contrasts["mcnemar_exact_p_holm"] < 0.05).all()


def test_n1_statistical_reporting_exposes_effects_intervals_and_denominators() -> None:
    n1_root = LEVELS_OUTPUT_ROOT / "n1_v2"
    quality = pd.read_csv(
        n1_root / "processed" / "quality_scenario_summary.csv"
    )
    failure = pd.read_csv(n1_root / "processed" / "failure_summary.csv")
    heterogeneity = pd.read_csv(
        n1_root / "processed" / "heterogeneity_summary.csv"
    )

    assert quality["rank_biserial_vs_5pct"].between(-1.0, 1.0).all()
    assert np.array_equal(
        quality["saving_over_5pct_supported"].to_numpy(bool),
        quality["sign_sensitivity_supported"].to_numpy(bool),
    )
    assert (quality["normalized_p95_cost_p05"] <= quality["normalized_p95_cost_q25"]).all()
    assert (quality["normalized_p95_cost_q25"] <= quality["normalized_p95_cost_median"]).all()
    assert (quality["normalized_p95_cost_median"] <= quality["normalized_p95_cost_q75"]).all()
    assert (quality["normalized_p95_cost_q75"] <= quality["normalized_p95_cost_p95"]).all()

    feasible_cost = failure.loc[failure["feasible_cost_n"] > 0]
    assert (
        feasible_cost["relative_cost_increase_ci_low"]
        <= feasible_cost["relative_cost_increase_median"]
    ).all()
    assert (
        feasible_cost["relative_cost_increase_median"]
        <= feasible_cost["relative_cost_increase_ci_high"]
    ).all()
    assert (failure["recovery_count"] <= failure["n_worlds"]).all()

    assert (heterogeneity["milp_certified_count"] <= heterogeneity["n_worlds"]).all()
    assert (
        heterogeneity["milp_rescue_count"]
        <= heterogeneity["false_feasible_count"]
    ).all()
    assert heterogeneity["milp_certification_ci_low"].between(0.0, 1.0).all()
    assert heterogeneity["milp_certification_ci_high"].between(0.0, 1.0).all()


def test_n1_confirmatory_figures_are_vector_and_source_ends_after_e4() -> None:
    n1_root = LEVELS_OUTPUT_ROOT / "n1_v2"
    for stem in (
        "n1_quality_scenarios",
        "n1_central_scaling",
        "n1_validity_boundary",
        "n1_operating_envelope",
        "n1_failure_recovery",
        "n1_heterogeneity_boundary",
    ):
        pdf_path = n1_root / "figures" / f"{stem}.pdf"
        png_path = n1_root / "figures" / f"{stem}.png"
        assert pdf_path.is_file()
        assert png_path.is_file()
        page = PdfReader(str(pdf_path)).pages[0]
        assert 500.0 <= float(page.mediabox.width) <= 540.0
        assert 215.0 <= float(page.mediabox.height) <= 245.0
        with Image.open(png_path) as image:
            dpi = image.info.get("dpi", (0.0, 0.0))
            assert dpi[0] >= 590.0
            assert dpi[1] >= 590.0

    manifest = json.loads(
        (n1_root / "manifest.json").read_text(encoding="utf-8")
    )
    source_paths = {record["path"] for record in manifest["sources"]}
    assert "scripts/sp1_n1.py" in source_paths
    assert "scripts/sp1_levels_common.py" in source_paths
    assert manifest["environment"]["scipy"]
    assert manifest["environment"]["logical_cpu_count"] >= 1
    assert len(manifest["environment"]["processor"].strip()) >= 3

    latex = (
        REPOSITORY_ROOT / "thesis" / "sp1_levels_23p" / "main.tex"
    ).read_text(encoding="utf-8")
    n1_model = latex.index(
        "SP1.N1: asignación exacta con robots homogéneos"
    )
    n1_design = latex.index("SP1.N1: campaña de validación")
    n1_quality = latex.index("SP1.N1: cuándo compensa el óptimo")
    n1_scaling = latex.index("SP1.N1 · E2: cuánto cuesta centralizar")
    n1_failure = latex.index("SP1.N1 · E3: qué ocurre tras una retirada")
    n1_validity = latex.index("SP1.N1 · E4: cuándo se rompe la reducción")
    document_end = latex.index(r"\end{document}")
    assert (
        n1_model
        < n1_design
        < n1_quality
        < n1_scaling
        < n1_failure
        < n1_validity
        < document_end
    )
    assert "Nivel 2: coaliciones con capacidad individual" not in latex
    assert (
        r"\input{sp1_levels_23p/figures/n1_experimental_design.tex}"
        in latex
    )


def test_latex_uses_canonical_payload_capacity_symbol() -> None:
    latex = (
        REPOSITORY_ROOT / "thesis" / "sp1_levels_23p" / "main.tex"
    ).read_text(encoding="utf-8")
    assert r"c_i^{\mathrm{pay}}" in latex
    assert r"conservar cada $c_i^{\mathrm{pay}}$" in latex.replace("\n", " ")


def test_latex_defines_level_and_branch_nomenclature() -> None:
    latex = (
        REPOSITORY_ROOT / "thesis" / "sp1_levels_23p" / "main.tex"
    ).read_text(encoding="utf-8")
    guide_index = latex.index("Mapa de niveles experimentales de SP1")
    n1_index = latex.index(
        "SP1.N1: asignación exacta con robots homogéneos"
    )
    assert guide_index < n1_index
    assert "SP1.N3.1" in latex
    assert "SP1.N3.2" in latex
    assert ".1/.2} = rama de método" in latex


def test_common_protocol_pages_precede_n1() -> None:
    latex = (
        REPOSITORY_ROOT / "thesis" / "sp1_levels_23p" / "main.tex"
    ).read_text(encoding="utf-8")
    protocol_latex = (
        REPOSITORY_ROOT
        / "thesis"
        / "sp1_levels_23p"
        / "figures"
        / "protocol_pipeline.tex"
    ).read_text(encoding="utf-8")
    protocol_source = latex + protocol_latex
    scenarios_index = latex.index(r"\section*{Escenarios}")
    statistics_index = latex.index("Protocolo experimental y análisis estadístico")
    n1_index = latex.index(
        "SP1.N1: asignación exacta con robots homogéneos"
    )
    assert scenarios_index < statistics_index < n1_index
    for scenario_name in (
        "Aleatorio",
        "Agrupado",
        "Separado",
        "Anillo",
        "Pasillo",
        "Fallo",
    ):
        assert scenario_name in latex
    assert r"\newcommand{\scenarioaxes}" in latex
    assert r"\draw[step=0.20,plotgrid]" in latex
    assert "coordenadas normalizadas" in latex
    assert "áreas coloreadas" in latex
    assert "robots uniformes; cargas en dos clústeres" in latex
    assert "cargas: banda ancha; robots: banda estrecha" in latex
    assert "fallo crítico de un robot asignado" in latex
    assert r"\tilde x\leq0{,}35" in latex
    assert r"\tilde x\geq0{,}65" in latex
    for generator_parameter in (
        "minimum size=9.52mm",
        "minimum size=32.64mm",
        "minimum size=24.48mm",
        "minimum size=14.96mm",
        "minimum size=28.56mm",
        "minimum size=8.84mm",
        "(0,0.34) rectangle (1,0.66)",
        "(0,0.42) rectangle (1,0.58)",
    ):
        assert generator_parameter in latex
    for obsolete_label in (
        "dos regiones de concentración espacial",
        "movimiento confinado",
        r"\rho(q,\mu)",
        r"t=t_f",
    ):
        assert obsolete_label not in latex
    assert "reducción homogénea equivalente" in latex
    assert r"\input{sp1_levels_23p/figures/protocol_pipeline.tex}" in latex
    prose = latex.replace("\n", " ")
    assert "Cada mundo--semilla es una réplica; los robots no lo son" in prose
    assert "Cada campaña se preespecifica" not in latex
    assert r"y=1.30cm" in protocol_latex
    for protocol_term in (
        "Protocolo Monte Carlo · campaña pareada",
        "mundo--semilla",
        r"\mathcal W=\mathcal C\times\Theta\times\mathcal S",
        "Bucle Monte Carlo pareado y registro RAW",
        "UNIDAD INDEPENDIENTE: MUNDO--SEMILLA",
        "3 · MÉTODOS",
        "4 · REGISTRO",
        "2 · MÉTRICAS",
        r"r<|\mathcal W|",
        "RAW cerrado",
        "Procesamiento reproducible",
        r"DECISIÓN $H_0/H_1$",
        r"no rechazar $H_0$",
        "McNemar exacto",
        "Friedman",
        "Kendall $W$",
        "Holm",
        "TIMEOUT",
    ):
        assert protocol_term in protocol_source

"""Regression tests for the four-level SP1 publication pipeline."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
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
    for level in ("n1", "n2", "n3", "n4"):
        manifest_path = LEVELS_OUTPUT_ROOT / level / "manifest.json"
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
        / "sp1_levels_26p"
        / "SP1_NIVELES_26P.pdf"
    )
    assert pdf_path.is_file()
    assert len(PdfReader(str(pdf_path)).pages) == 26


def test_n1_confirmatory_package_has_frozen_counts_and_invariants() -> None:
    n1_root = LEVELS_OUTPUT_ROOT / "n1"
    metrics = json.loads((n1_root / "key_metrics.json").read_text(encoding="utf-8"))
    assert metrics["campaign_id"] == "SP1_N1_HUNGARIAN_CONFIRMATORY_v1"
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


def test_n1_confirmatory_results_support_stated_validity_boundary() -> None:
    n1_root = LEVELS_OUTPUT_ROOT / "n1"
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
    assert aggregate["low"] == pytest.approx(0.4266666666666667)
    assert aggregate["extreme"] == pytest.approx(0.96)
    assert len(contrasts) == 4
    assert contrasts["supported"].all()
    assert (contrasts["mcnemar_exact_p_holm"] < 0.05).all()


def test_n1_confirmatory_figures_are_vector_and_pages_precede_n2() -> None:
    n1_root = LEVELS_OUTPUT_ROOT / "n1"
    for stem in (
        "n1_quality_scenarios",
        "n1_central_scaling",
        "n1_validity_boundary",
    ):
        assert (n1_root / "figures" / f"{stem}.pdf").is_file()
        assert (n1_root / "figures" / f"{stem}.png").is_file()

    latex = (
        REPOSITORY_ROOT / "thesis" / "sp1_levels_23p" / "main.tex"
    ).read_text(encoding="utf-8")
    n1_model = latex.index("SP1.N1: Homogeneous MRTA")
    n1_quality = latex.index("SP1.N1: beneficio práctico del óptimo global")
    n1_scaling = latex.index("SP1.N1: escalabilidad temporal y memoria global")
    n1_boundary = latex.index("SP1.N1: frontera de validez")
    n2 = latex.index("Nivel 2: capacidad individual y coaliciones indivisibles")
    assert n1_model < n1_quality < n1_scaling < n1_boundary < n2


def test_latex_uses_canonical_payload_capacity_symbol() -> None:
    latex = (
        REPOSITORY_ROOT / "thesis" / "sp1_levels_23p" / "main.tex"
    ).read_text(encoding="utf-8")
    assert r"c_i^{\mathrm{pay}}" in latex
    assert "precio dual explícito" in latex
    assert "no contiene un precio dual explícito" in latex


def test_latex_defines_level_and_branch_nomenclature() -> None:
    latex = (
        REPOSITORY_ROOT / "thesis" / "sp1_levels_23p" / "main.tex"
    ).read_text(encoding="utf-8")
    guide_index = latex.index("Mapa de niveles experimentales de SP1")
    n1_index = latex.index("SP1.N1: Homogeneous MRTA")
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
    n1_index = latex.index("SP1.N1: Homogeneous MRTA")
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
    assert "resume la campaña y su unidad" in latex.replace("\n", " ")
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

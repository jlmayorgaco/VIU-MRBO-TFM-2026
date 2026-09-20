"""Regression tests for the four-level SP1 publication pipeline."""

from __future__ import annotations

import json
import math
import re
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


def test_frozen_n1_raw_and_editorial_contract() -> None:
    """Editorial revisions may change prose, but never N1 RAW or E1--E4."""

    n1_root = LEVELS_OUTPUT_ROOT / "n1_v2"
    manifest = json.loads((n1_root / "manifest.json").read_text(encoding="utf-8"))
    for record in manifest["frozen_raw"].values():
        path = REPOSITORY_ROOT / record["path"]
        assert path.is_file()
        assert sha256_file(path) == record["sha256"]

    current = (
        REPOSITORY_ROOT / "thesis" / "sp1_levels_23p" / "main.tex"
    ).read_text(encoding="utf-8")
    headings = (
        "SP1.N1 · E1: método húngaro frente a asignación voraz",
        "SP1.N1 · E2: coste temporal del LSAP en el rango medido",
        "SP1.N1 · E3: qué ocurre tras una retirada",
        "SP1.N1 · E4: cuándo se rompe la reducción",
    )
    positions = [current.index(heading) for heading in headings]
    assert positions == sorted(positions)


def test_pdf_build_never_reruns_the_experimental_campaign() -> None:
    """The PDF must typeset a frozen campaign, not produce a new one.

    A build that could re-solve would let the document quote numbers nobody
    audited, and HiGHS certification near its time limit is wall-clock
    dependent, so a rebuild could silently change a reported count.
    """

    builder = (
        REPOSITORY_ROOT / "scripts" / "build_sp1_levels_pdf.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "import sp1_n1",
        "import sp1_a1_hungarian",
        "import sp1_a2_milp",
        "build_level",
        "linear_sum_assignment",
        "solve_heterogeneous_milp",
    ):
        assert forbidden not in builder
    # Only typesetting and rendering may be shelled out to.
    assert "lualatex" in builder and "biber" in builder and "pdftoppm" in builder


def test_frozen_raw_hashes_match_the_manifest() -> None:
    n1_root = LEVELS_OUTPUT_ROOT / "n1_v2"
    manifest = json.loads(
        (n1_root / "manifest.json").read_text(encoding="utf-8")
    )
    frozen = manifest["frozen_raw"]
    assert set(frozen) == {
        "quality",
        "scaling",
        "failure",
        "heterogeneity",
    }
    for record in frozen.values():
        path = REPOSITORY_ROOT / record["path"]
        assert path.is_file()
        assert sha256_file(path) == record["sha256"]
    assert manifest["environment"]["scipy"]
    assert "generated_at_utc" in manifest
    assert "git_commit" in manifest

    pdf_manifest = json.loads(
        (
            REPOSITORY_ROOT / "output" / "pdf" / "sp1_levels" / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert pdf_manifest["runs_solvers"] is False
    # The PDF records the very RAW digests the campaign registered.
    assert {record["sha256"] for record in frozen.values()} <= set(
        pdf_manifest["frozen_raw_sha256"].values()
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
        "n2": "n2_v1",
        "n3": "n3_v2",
        "n4": "n4_v2",
    }
    for level, directory in active_level_dirs.items():
        manifest_path = LEVELS_OUTPUT_ROOT / directory / "manifest.json"
        assert manifest_path.is_file(), f"missing {manifest_path}"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if "level" in manifest:
            assert manifest["level"] == level.upper()
        assert manifest.get("row_counts") or manifest.get("frozen_raw")
        for source in manifest.get("sources", []):
            source_path = REPOSITORY_ROOT / source["path"]
            assert source_path.is_file()
            assert source["sha256"] == sha256_file(source_path)
        for record in manifest.get("frozen_raw", {}).values():
            raw_path = REPOSITORY_ROOT / record["path"]
            assert raw_path.is_file()
            assert record["sha256"] == sha256_file(raw_path)


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
        / "sp1_levels"
        / "SP1_levels_N1_N2_N3_N4.pdf"
    )
    assert pdf_path.is_file()
    reader = PdfReader(str(pdf_path))
    assert len(reader.pages) == 48
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "EXPERIMENTO E4" in text
    # All four levels now share the same bounded artifact.
    assert "NIVEL 2 DE 4" in text
    assert "NIVEL 3 DE 4" in text
    assert "NIVEL 4 DE 4" in text


def test_sp1_narrative_freeze_contract_is_explicit() -> None:
    """The four levels must read as one causal argument, not four reports."""

    main = (
        REPOSITORY_ROOT / "thesis" / "sp1_levels_23p" / "main.tex"
    ).read_text(encoding="utf-8")
    n4 = (
        REPOSITORY_ROOT / "thesis" / "sp1_levels_23p" / "n4_v2.tex"
    ).read_text(encoding="utf-8")

    normalized_main = main.replace("\n", " ")
    for concept in (
        "N1 \\textbar\\ Cardinalidad",
        "N2 \\textbar\\ Atomicidad",
        "N3 \\textbar\\ Localidad informativa",
        "N4 \\textbar\\ Localidad estratégica",
        "elimina únicamente esa disponibilidad global de información",
        "la información reconstruida es un recurso",
    ):
        assert concept in main or concept in normalized_main

    for contract in (
        "constituye la contribución principal",
        "resultado central del nivel",
        "Resultados formales de F-I y alcance de cada enunciado",
        "entrada de SP2",
        "corresponden a SP2",
    ):
        assert contract in n4 or contract in (
            REPOSITORY_ROOT
            / "thesis"
            / "sp1_levels_23p"
            / "figures"
            / "n4"
            / "n4_taxonomy.tex"
        ).read_text(encoding="utf-8")


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
    assert metrics["false_feasible_count"] == 900
    # How many runs certify optimality depends on the wall-clock time limit,
    # so bound it instead of freezing a machine-specific count.
    assert (
        metrics["milp_certified_count"] + metrics["milp_uncertified_count"]
        == 1_500
    )
    assert metrics["milp_certified_count"] >= 1_480
    # A feasible incumbent exists for every false-feasible world; certifying
    # it optimal is a strictly stronger and strictly rarer event.
    assert metrics["milp_feasible_among_false_count"] == 900
    assert metrics["milp_repair_count_among_false"] == 900
    assert (
        metrics["milp_certified_among_false_count"]
        == metrics["milp_repair_certified_count_among_false"]
    )
    assert metrics["milp_certified_among_false_count"] >= 890
    assert (
        metrics["milp_certified_among_false_count"]
        + metrics["milp_uncertified_false_count"]
        == 900
    )
    assert metrics["milp_uncertified_gap_min"] > 0.0
    assert metrics["milp_uncertified_gap_max"] < 0.05
    # The cardinality window of Lemma 1 is sufficient: no world that satisfies
    # it on every load produced a false feasible.
    assert metrics["certificate_worlds_count"] == 300
    assert metrics["certificate_false_feasible_count"] == 0
    assert metrics["uncertified_worlds_count"] == 1_200
    assert metrics["uncertified_false_feasible_count"] == 900
    assert metrics["trend_slope"] > 0.0
    assert metrics["trend_ci_low"] > 0.0
    # E4 states the permuted-order verdict held in every run and that the
    # continuous sampling leaves no cross-load ties; both must stay exact.
    assert metrics["tiebreak_verdict_agreement"] == 1.0
    assert metrics["cross_load_cost_ties_total"] == 0


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
    diagnostic = pd.read_csv(
        n1_root / "processed" / "quality_cell_diagnostic.csv"
    )
    failure = pd.read_csv(n1_root / "processed" / "failure_summary.csv")
    heterogeneity = pd.read_csv(
        n1_root / "processed" / "heterogeneity_summary.csv"
    )

    assert quality["rank_biserial_vs_5pct"].between(-1.0, 1.0).all()
    # The confirmatory gate uses the exact sign test; Wilcoxon and the
    # randomized-order greedy are sensitivity analyses that must agree.
    assert np.array_equal(
        quality["saving_over_5pct_supported"].to_numpy(bool),
        quality["wilcoxon_sensitivity_supported"].to_numpy(bool),
    )
    assert np.array_equal(
        quality["saving_over_5pct_supported"].to_numpy(bool),
        quality["order_control_supported"].to_numpy(bool),
    )
    assert (quality["shuffled_order_median_shift"] < 0.0).all()
    assert quality["share_above_threshold"].between(0.0, 1.0).all()
    assert (quality["normalized_p95_cost_p05"] <= quality["normalized_p95_cost_q25"]).all()
    assert (quality["normalized_p95_cost_q25"] <= quality["normalized_p95_cost_median"]).all()
    assert (quality["normalized_p95_cost_median"] <= quality["normalized_p95_cost_q75"]).all()
    assert (quality["normalized_p95_cost_q75"] <= quality["normalized_p95_cost_p95"]).all()
    assert len(diagnostic) == 45
    assert (diagnostic.groupby("scenario").size() == 9).all()
    corridor_small_extreme = diagnostic.loc[
        (diagnostic["scenario"] == "corridor")
        & (diagnostic["M"] == 40)
        & (diagnostic["quota_mode"] == "extreme")
    ].iloc[0]
    assert corridor_small_extreme["relative_saving_median"] == pytest.approx(
        0.0475223680116618
    )
    assert not bool(
        corridor_small_extreme["cells_above_practical_threshold"]
    )

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
        heterogeneity["milp_repair_certified_count"]
        <= heterogeneity["milp_repair_count"]
    ).all()
    assert (
        heterogeneity["milp_repair_count"]
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
        # Drawn near the printed size (5.75 x 2.02 in) so LaTeX does not have
        # to scale them down past the legibility of their tick labels.
        assert 395.0 <= float(page.mediabox.width) <= 435.0
        assert 130.0 <= float(page.mediabox.height) <= 165.0
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
        "SP1.N1: asignación exacta bajo homogeneidad de capacidad"
    )
    n1_design = latex.index("SP1.N1: hasta dónde vale contar robots")
    n1_quality = latex.index(
        "SP1.N1 · E1: método húngaro frente a asignación voraz"
    )
    n1_scaling = latex.index(
        "SP1.N1 · E2: coste temporal del LSAP en el rango medido"
    )
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
    # The design page states pre-specified decision rules only; the observed
    # synthesis belongs to the result pages that follow it.
    design_table = latex[n1_design:n1_quality]
    assert r"\label{tab:n1-experimental-design}" in design_table
    assert r"\NOneScenarioGates" not in design_table
    assert r"\NOneHeteroContrastsSupported" not in design_table
    for rule in (
        r"\mathrm{LCB}_{95}",
        "descriptivo",
        "invariante",
        "McNemar exacto pareado",
    ):
        assert rule in design_table


def test_latex_uses_canonical_payload_capacity_symbol() -> None:
    latex = (
        REPOSITORY_ROOT / "thesis" / "sp1_levels_23p" / "main.tex"
    ).read_text(encoding="utf-8")
    assert r"c_i^{\mathrm{pay}}" in latex
    assert r"N2 conserva cada $c_i^{\mathrm{pay}}$" in latex.replace("\n", " ")


def test_latex_defines_level_and_branch_nomenclature() -> None:
    latex = (
        REPOSITORY_ROOT / "thesis" / "sp1_levels_23p" / "main.tex"
    ).read_text(encoding="utf-8")
    guide_index = latex.index("Mapa de niveles experimentales de SP1")
    n1_index = latex.index(
        "SP1.N1: asignación exacta bajo homogeneidad de capacidad"
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
        "SP1.N1: asignación exacta bajo homogeneidad de capacidad"
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
    # The 0,2 grid is a reading guide in the figure; the generators sample
    # continuously, so the text must not present it as a position lattice.
    assert "retícula de paso" not in latex
    assert "guía de lectura" in latex
    assert r"\label{tab:sp1-generators}" in latex
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
    # E4 evaluates the homogeneous slot model on heterogeneous worlds, so the
    # comparison scope must be stated where the result is discussed.
    assert "veredictos del modelo" in latex
    assert "cinco perfiles anidados sin cambiar robots" in latex
    assert r"\input{sp1_levels_23p/figures/protocol_pipeline.tex}" in latex
    prose = latex.replace("\n", " ")
    assert "cada mundo--semilla" in prose
    assert "robots y cargas quedan anidados en él y no inflan la muestra" in prose
    # The seed protocol must be stated without exposing implementation hashes:
    # one distinct seed per design cell and a bootstrap stratified by that cell.
    assert "La celda y el índice de réplica determinan una semilla distinta" in prose
    assert "SHA-256" not in prose
    assert "no hay números aleatorios comunes" in prose
    assert "dentro de cada celda" in prose
    assert "Cada campaña se preespecifica" not in latex
    assert r"y=1.03cm" in protocol_latex
    for protocol_term in (
        "Protocolo Monte Carlo · campaña pareada",
        "mundo--semilla",
        r"\mathcal W=\mathcal C\times\Theta\times\mathcal S",
        "Bucle Monte Carlo pareado",
        "UNIDAD INDEPENDIENTE: MUNDO--SEMILLA",
        "3 · MÉTODOS",
        "4 · REGISTRO",
        "2 · MÉTRICAS",
        r"r<|\mathcal W|",
        "campaña completa",
        "Cálculo de métricas y diferencias por mundo",
            r"decisión $H_0/H_1$",
        r"no rechazar $H_0$",
        "McNemar exacto",
        "Friedman",
        "Kendall $W$",
        "Holm",
        "FALLO/LÍMITE",
    ):
        assert protocol_term in protocol_source

"""Build and validate the autonomous 26-page VIU SP1 levels PDF."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader

from sp1_levels_common import (
    LEVELS_OUTPUT_ROOT,
    REPOSITORY_ROOT,
    sha256_file,
    write_json,
)


SOURCE_DIR = REPOSITORY_ROOT / "thesis" / "sp1_levels_23p"
DEFAULT_OUTPUT_DIR = REPOSITORY_ROOT / "output" / "pdf" / "sp1_levels_26p"


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _tex_integer(value: object) -> str:
    return f"{int(value):,}".replace(",", r"\,")


def _tex_float(value: object, decimals: int = 3) -> str:
    return f"{float(value):.{decimals}f}"


def _tex_bool(value: object) -> str:
    return "sí" if bool(value) else "no"


def generate_metrics_tex() -> Path:
    """Generate every quantitative macro from processed JSON artifacts."""

    n1 = _read_json(LEVELS_OUTPUT_ROOT / "n1" / "key_metrics.json")
    n2 = _read_json(LEVELS_OUTPUT_ROOT / "n2" / "key_metrics.json")
    n3 = _read_json(LEVELS_OUTPUT_ROOT / "n3" / "key_metrics.json")
    n4 = _read_json(LEVELS_OUTPUT_ROOT / "n4" / "key_metrics.json")
    n1_n2 = _read_json(
        LEVELS_OUTPUT_ROOT / "comparison" / "n1_n2_metrics.json"
    )
    n3_n4 = _read_json(
        LEVELS_OUTPUT_ROOT / "comparison" / "n3_n4_metrics.json"
    )

    macros = {
        "NOneRows": _tex_integer(n1["raw_rows"]),
        "NOneMaxN": _tex_integer(n1["max_n"]),
        "NOneExponent": _tex_float(n1["solver_power_exponent"], 2),
        "NOneRSquared": _tex_float(n1["solver_power_r_squared"], 2),
        "NOneGreedyRatio": _tex_float(
            n1["median_greedy_to_hungarian_ratio"], 3
        ),
        "NOneWorlds": _tex_integer(n1["independent_worlds"]),
        "NOneQualityRows": _tex_integer(n1["quality_rows"]),
        "NOneSavingPct": _tex_float(
            100.0 * n1["overall_saving_median"], 2
        ),
        "NOneSavingLowPct": _tex_float(
            100.0 * n1["overall_saving_ci_low"], 2
        ),
        "NOneSavingHighPct": _tex_float(
            100.0 * n1["overall_saving_ci_high"], 2
        ),
        "NOneScenarioGates": _tex_integer(n1["scenario_gates_passed"]),
        "NOneUniformSavingPct": _tex_float(
            100.0 * n1["saving_uniform_median"], 2
        ),
        "NOneClusteredSavingPct": _tex_float(
            100.0 * n1["saving_clustered_median"], 2
        ),
        "NOneSeparatedSavingPct": _tex_float(
            100.0 * n1["saving_separated_median"], 2
        ),
        "NOneRingSavingPct": _tex_float(
            100.0 * n1["saving_ring_median"], 2
        ),
        "NOneCorridorSavingPct": _tex_float(
            100.0 * n1["saving_corridor_median"], 2
        ),
        "NOneExponentLow": _tex_float(n1["solver_power_ci_low"], 2),
        "NOneExponentHigh": _tex_float(n1["solver_power_ci_high"], 2),
        "NOneScalingPninetyfiveMs": _tex_float(
            n1["balanced_p95_solver_ms_at_max_n"], 1
        ),
        "NOneFailureRows": _tex_integer(n1["failure_rows"]),
        "NOneFailureWorlds": _tex_integer(n1["failure_independent_worlds"]),
        "NOneFailureAgreementPct": _tex_float(
            100.0 * n1["failure_theory_agreement_rate"], 1
        ),
        "NOneHeteroRows": _tex_integer(n1["heterogeneity_rows"]),
        "NOneHeteroWorlds": _tex_integer(
            n1["heterogeneity_independent_worlds"]
        ),
        "NOneLowFalsePct": _tex_float(
            100.0 * n1["false_feasible_low_rate"], 1
        ),
        "NOneModerateFalsePct": _tex_float(
            100.0 * n1["false_feasible_moderate_rate"], 1
        ),
        "NOneHighFalsePct": _tex_float(
            100.0 * n1["false_feasible_high_rate"], 1
        ),
        "NOneExtremeFalsePct": _tex_float(
            100.0 * n1["extreme_false_feasible_rate"], 1
        ),
        "NOneMilpCertifiedPct": _tex_float(
            100.0 * n1["milp_certification_rate"], 2
        ),
        "NOneMilpRescuePct": _tex_float(
            100.0 * n1["milp_rescue_rate_among_false"], 2
        ),
        "NTwoRows": _tex_integer(n2["raw_rows"]),
        "NTwoAuditRows": _tex_integer(n2["saturation_rows"]),
        "NTwoCensored": _tex_integer(n2["saturation_censored"]),
        "NTwoOptimal": _tex_integer(n2["saturation_optimal_certified"]),
        "NTwoMaxN": _tex_integer(n2["saturation_max_n"]),
        "NTwoMaxK": _tex_integer(n2["saturation_max_k"]),
        "NTwoVariableExponent": _tex_float(
            n2["binary_variable_growth_exponent"], 2
        ),
        "NOneNTwoPairs": _tex_integer(n1_n2["controlled_rows"]),
        "NOneNTwoDistanceRatio": _tex_float(
            n1_n2["median_distance_ratio"], 3
        ),
        "NOneNTwoSolverRatio": _tex_float(
            n1_n2["median_solver_ratio"], 2
        ),
        "NThreeWorlds": _tex_integer(n3["paired_worlds"]),
        "NThreeRows": _tex_integer(n3["raw_level_rows"]),
        "NThreeRecovered": _tex_integer(n3["recovered_rows"]),
        "NThreeGapRows": _tex_integer(n3["certified_gap_rows"]),
        "NThreeMaxN": _tex_integer(n3["max_n"]),
        "NFourWorlds": _tex_integer(n4["confirmatory_worlds"]),
        "NFourCampaignRows": _tex_integer(n4["campaign_rows_all_methods"]),
        "NFourRows": _tex_integer(n4["n4_level_rows"]),
        "NFourMaxN": _tex_integer(n4["max_n"]),
        "NFourHtwoEffect": _tex_float(n4["h2_closure_effect"], 3),
        "NFourHfourEffect": _tex_float(n4["h4_quality_effect"], 3),
        "NFourHfourPassed": _tex_bool(n4["h4_gate_passed"]),
        "NFourHfiveEffect": _tex_float(
            n4["h5_coverage_equivalence_effect"], 3
        ),
        "NFourHfivePassed": _tex_bool(
            n4["h5_coverage_equivalence_passed"]
        ),
        "NFourHsevenRatio": _tex_float(
            n4["h7_static_recourse_ratio"], 3
        ),
        "NFourGateCells": _tex_integer(n4["composite_cells"]),
        "NFourGatePassed": _tex_integer(n4["composite_cells_passed"]),
        "NFourBytesFailed": _tex_integer(n4["bytes_gates_failed"]),
        "NThreeNFourRuntimeRatio": _tex_float(
            n3_n4["median_runtime_ratio"], 2
        ),
        "NThreeNFourBytesRatio": _tex_float(
            n3_n4["median_bytes_ratio"], 2
        ),
    }
    lines = [
        "% Generated by scripts/build_sp1_levels_pdf.py; do not edit.",
    ]
    lines.extend(
        rf"\newcommand{{\{name}}}{{{value}}}" for name, value in macros.items()
    )
    path = SOURCE_DIR / "generated" / "metrics.tex"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _run_lualatex(output_dir: Path) -> Path:
    executable = shutil.which("lualatex")
    if executable is None:
        raise RuntimeError("lualatex is required to build the VIU artifact.")
    command = [
        executable,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-jobname=SP1_NIVELES_26P",
        f"-output-directory={output_dir}",
        "sp1_levels_23p/main.tex",
    ]
    logs: list[str] = []
    for pass_index in (1, 2):
        completed = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT / "thesis",
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        logs.append(
            f"===== LuaLaTeX pass {pass_index} =====\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
        if completed.returncode != 0:
            (output_dir / "build.log").write_text(
                "\n".join(logs),
                encoding="utf-8",
            )
            raise RuntimeError(
                f"LuaLaTeX pass {pass_index} failed; see "
                f"{output_dir / 'build.log'}."
            )
    (output_dir / "build.log").write_text(
        "\n".join(logs),
        encoding="utf-8",
    )
    built = output_dir / "SP1_NIVELES_26P.pdf"
    if not built.is_file():
        raise RuntimeError(
            "LuaLaTeX completed without producing SP1_NIVELES_26P.pdf."
        )
    return built


def _render_pdf(pdf_path: Path, render_dir: Path) -> int:
    renderer = shutil.which("pdftoppm")
    if renderer is None:
        raise RuntimeError("pdftoppm is required for visual PDF validation.")
    renderer_path = Path(renderer)
    if renderer_path.suffix.lower() == ".cmd":
        dependency_root = renderer_path.parents[2]
        native_renderer = (
            dependency_root
            / "native"
            / "poppler"
            / "Library"
            / "bin"
            / "pdftoppm.exe"
        )
        if native_renderer.is_file():
            renderer = str(native_renderer)
    render_dir.mkdir(parents=True, exist_ok=True)
    for stale_page in render_dir.glob("page-*.png"):
        stale_page.unlink()
    prefix = render_dir / "page"
    completed = subprocess.run(
        [
            renderer,
            "-png",
            "-r",
            "130",
            str(pdf_path),
            str(prefix),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"pdftoppm failed: {completed.stdout}\n{completed.stderr}"
        )
    return len(list(render_dir.glob("page-*.png")))


def build_pdf(output_dir: Path) -> dict[str, object]:
    """Compile, enforce the page budget and render all pages."""

    required = [
        LEVELS_OUTPUT_ROOT / level / "manifest.json"
        for level in ("n1", "n2", "n3", "n4")
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Run sp1_n1.py through sp1_n4.py first. Missing: "
            + ", ".join(missing)
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = generate_metrics_tex()
    built = _run_lualatex(output_dir)
    final_pdf = output_dir / "SP1_NIVELES_26P.pdf"
    if built.resolve() != final_pdf.resolve():
        shutil.copy2(built, final_pdf)
    reader = PdfReader(str(final_pdf))
    page_count = len(reader.pages)
    if page_count != 26:
        raise RuntimeError(
            f"Expected exactly 26 pages, but the PDF has {page_count}."
        )
    rendered_pages = _render_pdf(final_pdf, output_dir / "rendered")
    if rendered_pages != page_count:
        raise RuntimeError(
            f"Rendered {rendered_pages} pages for a {page_count}-page PDF."
        )
    manifest = {
        "schema_version": "sp1-levels-pdf-v2",
        "pdf": {
            "path": final_pdf.relative_to(REPOSITORY_ROOT).as_posix(),
            "bytes": final_pdf.stat().st_size,
            "sha256": sha256_file(final_pdf),
            "pages": page_count,
            "rendered_pages": rendered_pages,
        },
        "page_budget": {
            "introduction": 1,
            "nomenclature_guide": 1,
            "common_scenarios": 1,
            "common_metrics_statistics": 1,
            "N1": 4,
            "N2": 2,
            "N3": 2,
            "N4": 14,
        },
        "style": {
            "paper": "A4",
            "font": "Arial 12 pt",
            "line_spacing": 1.5,
            "margins_cm": {
                "top": 2.5,
                "bottom": 2.5,
                "left": 3.0,
                "right": 3.0,
            },
            "source_style": "thesis/viu-mrob-thesis.sty",
        },
        "metrics_tex": {
            "path": metrics_path.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": sha256_file(metrics_path),
        },
        "level_manifests": {
            level.upper(): sha256_file(
                LEVELS_OUTPUT_ROOT / level / "manifest.json"
            )
            for level in ("n1", "n2", "n3", "n4")
        },
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the exact 23-page VIU SP1 levels PDF."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_pdf(args.output_dir)
    print(
        "SP1 levels PDF: "
        f"{(REPOSITORY_ROOT / manifest['pdf']['path']).resolve()} "
        f"({manifest['pdf']['pages']} pages)"
    )


if __name__ == "__main__":
    main()

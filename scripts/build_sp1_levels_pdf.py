"""Build and validate the 10-page VIU SP1.N1 working document."""

from __future__ import annotations

import argparse
import json
import math
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
DEFAULT_OUTPUT_DIR = REPOSITORY_ROOT / "output" / "pdf" / "sp1_n1_10p"
ACTIVE_LEVEL_DIRS = {
    "n1": "n1_v2",
}


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _tex_integer(value: object) -> str:
    return f"{int(value):,}".replace(",", r"\,")


def _tex_float(value: object, decimals: int = 3) -> str:
    return f"{float(value):.{decimals}f}".replace(".", r"{,}")


def _tex_scientific(value: object, decimals: int = 2) -> str:
    numeric = float(value)
    if numeric == 0.0:
        return "0"
    exponent = int(math.floor(math.log10(abs(numeric))))
    mantissa = numeric / (10**exponent)
    formatted = f"{mantissa:.{decimals}f}".replace(".", r"{,}")
    return rf"{formatted}\times10^{{{exponent}}}"


def _tex_text(value: object) -> str:
    text = str(value)
    for source, replacement in (
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("#", r"\#"),
        ("_", r"\_"),
    ):
        text = text.replace(source, replacement)
    return text


def generate_metrics_tex() -> Path:
    """Generate the N1 quantitative macros from processed artifacts."""

    n1 = _read_json(LEVELS_OUTPUT_ROOT / "n1_v2" / "key_metrics.json")
    n1_manifest = _read_json(LEVELS_OUTPUT_ROOT / "n1_v2" / "manifest.json")
    environment = n1_manifest["environment"]

    macros = {
        "NOneRows": _tex_integer(n1["raw_rows"]),
        "NOneMaxN": _tex_integer(n1["max_n"]),
        "NOneExponent": _tex_float(n1["solver_power_exponent"], 2),
        "NOneRSquared": _tex_float(n1["solver_power_r_squared"], 3),
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
        "NOneCellsPerScenario": _tex_integer(
            n1["quality_cells_per_scenario"]
        ),
        "NOneUniformCellsAbove": _tex_integer(
            n1["quality_uniform_cells_above_threshold"]
        ),
        "NOneClusteredCellsAbove": _tex_integer(
            n1["quality_clustered_cells_above_threshold"]
        ),
        "NOneSeparatedCellsAbove": _tex_integer(
            n1["quality_separated_cells_above_threshold"]
        ),
        "NOneRingCellsAbove": _tex_integer(
            n1["quality_ring_cells_above_threshold"]
        ),
        "NOneCorridorCellsAbove": _tex_integer(
            n1["quality_corridor_cells_above_threshold"]
        ),
        "NOneCorridorSmallExtremePct": _tex_float(
            100.0 * n1["corridor_small_extreme_saving_median"], 2
        ),
        "NOneQualityPHolmBound": _tex_scientific(
            n1["quality_supported_max_p_holm"]
        ),
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
        "NOneScalingCompleted": _tex_integer(n1["scaling_completed_count"]),
        "NOneScalingFailed": _tex_integer(n1["scaling_failed_count"]),
        "NOneProcessor": _tex_text(environment["processor"]),
        "NOneLogicalCPU": _tex_integer(environment["logical_cpu_count"]),
        "NOnePythonVersion": _tex_text(environment["python"]),
        "NOneSciPyVersion": _tex_text(environment["scipy"]),
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
        "NOneMilpAudits": _tex_integer(n1["milp_audit_count"]),
        "NOneMilpFeasibleIncumbents": _tex_integer(
            n1["milp_feasible_incumbent_count"]
        ),
        "NOneMilpCertifiedCount": _tex_integer(n1["milp_certified_count"]),
        "NOneMilpUncertifiedCount": _tex_integer(
            n1["milp_uncertified_count"]
        ),
        "NOneFalseFeasibleCount": _tex_integer(n1["false_feasible_count"]),
        "NOneMilpRescueCount": _tex_integer(
            n1["milp_rescue_count_among_false"]
        ),
        "NOneMilpUncertifiedFalseCount": _tex_integer(
            n1["milp_uncertified_false_count"]
        ),
        "NOneMilpGapMinPct": _tex_float(
            100.0 * n1["milp_uncertified_gap_min"], 2
        ),
        "NOneMilpGapMaxPct": _tex_float(
            100.0 * n1["milp_uncertified_gap_max"], 2
        ),
        "NOneMilpTimeLimitSec": _tex_float(n1["milp_time_limit_s"], 0),
        "NOneHeteroPHolmBound": _tex_scientific(
            n1["heterogeneity_supported_max_p_holm"]
        ),
        "NOneHeteroContrastsSupported": _tex_integer(
            n1["heterogeneity_contrasts_supported"]
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
    biber = shutil.which("biber")
    if biber is None:
        raise RuntimeError("biber is required to resolve the SP1 citations.")
    command = [
        executable,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-jobname=SP1_N1_10P",
        f"-output-directory={output_dir}",
        "sp1_levels_23p/main.tex",
    ]
    logs: list[str] = []

    def run_latex(pass_index: int) -> None:
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
    run_latex(1)

    biber_command = [
        biber,
        "--input-directory",
        str(output_dir),
        "--output-directory",
        str(output_dir),
        "SP1_N1_10P",
    ]
    completed = subprocess.run(
        biber_command,
        cwd=REPOSITORY_ROOT / "thesis",
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    logs.append(
        "===== Biber =====\n"
        f"{completed.stdout}\n{completed.stderr}"
    )
    if completed.returncode != 0:
        (output_dir / "build.log").write_text(
            "\n".join(logs),
            encoding="utf-8",
        )
        raise RuntimeError(
            f"Biber failed; see {output_dir / 'build.log'}."
        )

    run_latex(2)
    run_latex(3)
    (output_dir / "build.log").write_text(
        "\n".join(logs),
        encoding="utf-8",
    )
    built = output_dir / "SP1_N1_10P.pdf"
    if not built.is_file():
        raise RuntimeError(
            "LuaLaTeX completed without producing SP1_N1_10P.pdf."
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
        LEVELS_OUTPUT_ROOT / directory / "manifest.json"
        for directory in ACTIVE_LEVEL_DIRS.values()
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Run sp1_n1.py first. Missing: "
            + ", ".join(missing)
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = generate_metrics_tex()
    built = _run_lualatex(output_dir)
    final_pdf = output_dir / "SP1_N1_10P.pdf"
    if built.resolve() != final_pdf.resolve():
        shutil.copy2(built, final_pdf)
    reader = PdfReader(str(final_pdf))
    page_count = len(reader.pages)
    if page_count != 10:
        raise RuntimeError(
            f"Expected exactly 10 pages, but the PDF has {page_count}."
        )
    rendered_pages = _render_pdf(final_pdf, output_dir / "rendered")
    if rendered_pages != page_count:
        raise RuntimeError(
            f"Rendered {rendered_pages} pages for a {page_count}-page PDF."
        )
    manifest = {
        "schema_version": "sp1-n1-pdf-v1",
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
            "N1": 6,
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
                LEVELS_OUTPUT_ROOT / directory / "manifest.json"
            )
            for level, directory in ACTIVE_LEVEL_DIRS.items()
        },
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the exact 10-page VIU SP1.N1 working PDF."
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

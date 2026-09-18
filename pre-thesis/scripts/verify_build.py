"""Verify LaTeX diagnostics, A4 geometry and the VIU page budget."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
MARKER_RE = re.compile(
    r"\\zref@newlabel\{(?P<name>budget:[^}]+)\}\{(?:(?!\\zref@newlabel).)*?"
    r"\\abspage\{(?P<page>\d+)\}",
    re.DOTALL,
)
ABSOLUTE_WINDOWS_RE = re.compile(r"(?i)(?:^|[\"'(\s])(?:[a-z]:[\\/])")
PARENT_PATH_RE = re.compile(r"(?:^|[{'\"(\s])\.\.[\\/]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("thesis", "monograph"), required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--aux", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def latex_errors(log_text: str) -> list[str]:
    checks = {
        "referencias indefinidas": r"There were undefined references|Reference .+ undefined",
        "citas indefinidas": r"undefined citations|Citation .+ undefined",
        "etiquetas duplicadas": r"multiply defined|There were multiply-defined labels",
        "caja horizontal desbordada": r"Overfull \\hbox",
        "caja vertical desbordada": r"Overfull \\vbox",
        "artefacto ausente": r"LaTeX Error: File .+ not found|Package .* Error: File .+ not found",
        "bibliografía inestable": r"Please \(re\)run Biber|Please rerun LaTeX",
        "glifo ausente": r"Missing character:",
        "destino PDF duplicado": r"ignoring duplicate destination",
    }
    return [name for name, pattern in checks.items() if re.search(pattern, log_text)]


def source_path_errors() -> list[str]:
    errors: list[str] = []
    suffixes = {".tex", ".sty", ".bib", ".ps1", ".json", ".yaml", ".yml"}
    ignored_parts = {"build", "evidence"}
    for source in ROOT.rglob("*"):
        if not source.is_file() or source.suffix.lower() not in suffixes:
            continue
        if any(part in ignored_parts for part in source.relative_to(ROOT).parts):
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), start=1):
            if ABSOLUTE_WINDOWS_RE.search(line) or PARENT_PATH_RE.search(line):
                errors.append(f"{source.relative_to(ROOT)}:{number}: ruta externa")
    return errors


def page_geometry_errors(reader: PdfReader) -> list[str]:
    errors: list[str] = []
    a4 = (595.276, 841.890)
    for index, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        dimensions = sorted((width, height))
        expected = sorted(a4)
        if any(abs(actual - target) > 1.0 for actual, target in zip(dimensions, expected)):
            errors.append(
                f"página {index}: {width:.2f} x {height:.2f} pt, se esperaba A4"
            )
    return errors


def parse_markers(aux_text: str) -> dict[str, int]:
    return {match.group("name"): int(match.group("page")) for match in MARKER_RE.finditer(aux_text)}


def inclusive(markers: dict[str, int], start: str, end: str) -> int:
    return markers[end] - markers[start] + 1


def page_budget_errors(markers: dict[str, int], total: int) -> tuple[list[str], dict[str, float]]:
    required = {
        "budget:body-start",
        "budget:objectives-start",
        "budget:hypotheses-start",
        "budget:methodology-start",
        "budget:theory-start",
        "budget:body-end",
        "budget:results-start",
        "budget:results-end",
        "budget:references-start",
        "budget:references-end",
        "budget:appendices-start",
        "budget:appendices-end",
        "budget:results-interface-start",
        "budget:results-interface-end",
        "budget:sp1-start",
        "budget:sp1-end",
        "budget:sp2-start",
        "budget:sp2-end",
        "budget:sp3-start",
        "budget:sp3-end",
        "budget:results-synthesis-start",
        "budget:results-synthesis-end",
        "budget:conclusions-start",
    }
    missing = sorted(required - markers.keys())
    if missing:
        return ([f"marcadores de presupuesto ausentes: {', '.join(missing)}"], {})

    metrics: dict[str, float] = {
        "preliminaries": markers["budget:body-start"] - 1,
        "body": inclusive(markers, "budget:body-start", "budget:body-end"),
        "results": markers["budget:conclusions-start"] - markers["budget:results-start"],
        "references": inclusive(markers, "budget:references-start", "budget:references-end"),
        "appendices": inclusive(markers, "budget:appendices-start", "budget:appendices-end"),
        "total": total,
        "chapter_introduction": (
            markers["budget:objectives-start"] - markers["budget:body-start"]
        ),
        "chapter_objectives": (
            markers["budget:hypotheses-start"] - markers["budget:objectives-start"]
        ),
        "chapter_hypotheses": (
            markers["budget:methodology-start"] - markers["budget:hypotheses-start"]
        ),
        "chapter_methodology": (
            markers["budget:theory-start"] - markers["budget:methodology-start"]
        ),
        "chapter_theoretical_framework": (
            markers["budget:results-start"] - markers["budget:theory-start"]
        ),
        "chapter_results_and_analysis": (
            markers["budget:conclusions-start"] - markers["budget:results-start"]
        ),
        "chapter_conclusions": (
            markers["budget:references-start"] - markers["budget:conclusions-start"]
        ),
        "results_interface_and_protocol": (
            markers["budget:sp1-start"] - markers["budget:results-interface-start"]
        ),
        "results_sp1": markers["budget:sp2-start"] - markers["budget:sp1-start"],
        "results_sp2": markers["budget:sp3-start"] - markers["budget:sp2-start"],
        "results_sp3": (
            markers["budget:results-synthesis-start"] - markers["budget:sp3-start"]
        ),
        "results_synthesis": (
            markers["budget:conclusions-start"]
            - markers["budget:results-synthesis-start"]
        ),
    }
    metrics["body_including_references"] = metrics["body"] + metrics["references"]
    metrics["results_fraction_of_body"] = metrics["results"] / metrics["body"]
    metrics["results_fraction_of_body_including_references"] = (
        metrics["results"] / metrics["body_including_references"]
    )

    config = yaml.safe_load((ROOT / "config" / "page-budget.yaml").read_text(encoding="utf-8"))
    limits = config["limits"]
    errors: list[str] = []

    for name, target in config["chapter_targets"].items():
        metric_name = f"chapter_{name}"
        value = metrics[metric_name]
        if value != target:
            errors.append(f"{metric_name}={value:g} != objetivo {target}")

    for name in (
        "preliminaries",
        "body",
        "body_including_references",
        "references",
        "appendices",
        "total",
    ):
        value = metrics[name]
        minimum = limits[name].get("minimum")
        maximum = limits[name].get("maximum")
        if minimum is not None and value < minimum:
            errors.append(f"{name}={value:g} < mínimo {minimum}")
        if maximum is not None and value > maximum:
            errors.append(f"{name}={value:g} > máximo {maximum}")

    subsection_metric_names = {
        "interface_and_protocol": "results_interface_and_protocol",
        "sp1": "results_sp1",
        "sp2": "results_sp2",
        "sp3": "results_sp3",
        "synthesis": "results_synthesis",
    }
    for name, metric_name in subsection_metric_names.items():
        value = metrics[metric_name]
        subsection_limit = config["results_subsections"][name]
        minimum = subsection_limit.get("minimum")
        maximum = subsection_limit.get("maximum")
        if minimum is not None and value < minimum:
            errors.append(f"{metric_name}={value:g} < mínimo {minimum}")
        if maximum is not None and value > maximum:
            errors.append(f"{metric_name}={value:g} > máximo {maximum}")

    minimum_fraction = float(limits["results"]["minimum_fraction_of_body"])
    if metrics["results_fraction_of_body"] < minimum_fraction:
        errors.append(
            "results_fraction_of_body="
            f"{metrics['results_fraction_of_body']:.3f} < mínimo {minimum_fraction:.3f}"
        )
    conservative_fraction = float(
        limits["results"]["minimum_fraction_of_body_including_references"]
    )
    if metrics["results_fraction_of_body_including_references"] < conservative_fraction:
        errors.append(
            "results_fraction_of_body_including_references="
            f"{metrics['results_fraction_of_body_including_references']:.3f} "
            f"< mínimo {conservative_fraction:.3f}"
        )
    return errors, metrics


def main() -> None:
    args = parse_args()
    pdf_path = args.pdf.resolve()
    aux_path = args.aux.resolve()
    log_path = args.log.resolve()
    errors: list[str] = []

    for path in (pdf_path, aux_path, log_path):
        if not path.is_file():
            errors.append(f"artefacto de build ausente: {path}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)

    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    errors.extend(latex_errors(log_text))
    errors.extend(source_path_errors())

    reader = PdfReader(str(pdf_path))
    total = len(reader.pages)
    errors.extend(page_geometry_errors(reader))
    metrics: dict[str, float] = {"total": total}
    if args.target == "thesis":
        aux_text = aux_path.read_text(encoding="utf-8", errors="replace")
        budget_errors, metrics = page_budget_errors(parse_markers(aux_text), total)
        errors.extend(budget_errors)

    report = {
        "schema_version": 1,
        "target": args.target,
        "pdf": pdf_path.relative_to(ROOT).as_posix(),
        "metrics": metrics,
        "errors": errors,
        "status": "passed" if not errors else "failed",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if errors:
        print("Verificación fallida:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

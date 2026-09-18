"""Reparto de páginas de la versión 2, medido sobre las etiquetas zref del .aux.

Mismo criterio que `scripts/verify_build.py`: páginas físicas del PDF, cuerpo
sin preliminares, referencias ni anexos. Aquí solo se informa; no se falla,
porque el presupuesto de `config/page-budget.yaml` describe la v1 congelada.

Uso:
    python pre-thesis/scripts/report_pages_v2.py pre-thesis/build-v2/main-v2.aux
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

LABEL = re.compile(
    r"\\zref@newlabel\{(?P<name>budget:[^}]+)\}\{(?:(?!\\zref@newlabel).)*?"
    r"\\abspage\{(?P<page>\d+)\}",
    re.DOTALL,
)

# Límites literales de las Instrucciones VIU, para contrastar el reparto.
VIU_BODY_MIN, VIU_BODY_MAX = 50, 80
VIU_APPENDIX_MAX = 20
VIU_RESULTS_MIN_FRACTION = 0.50


def markers(aux_path: Path) -> dict[str, int]:
    text = aux_path.read_text(encoding="utf-8", errors="replace")
    return {m.group("name"): int(m.group("page")) for m in LABEL.finditer(text)}


def main() -> int:
    aux_path = Path(sys.argv[1] if len(sys.argv) > 1 else "pre-thesis/build-v2/main-v2.aux")
    if not aux_path.is_file():
        print(f"No existe el .aux: {aux_path}")
        return 2

    m = markers(aux_path)
    missing = [
        k
        for k in ("budget:body-start", "budget:body-end", "budget:results-start")
        if k not in m
    ]
    if missing:
        print("Faltan etiquetas zref (¿compilación incompleta?): " + ", ".join(missing))
        return 2

    span = lambda a, b: m[b] - m[a]  # noqa: E731

    preliminaries = m["budget:body-start"] - 1
    body = m["budget:body-end"] - m["budget:body-start"] + 1
    references = span("budget:references-start", "budget:references-end") + 1
    appendices = span("budget:appendices-start", "budget:appendices-end") + 1
    results = span("budget:results-start", "budget:conclusions-start")

    chapters = [
        ("1. Introducción", span("budget:body-start", "budget:objectives-start")),
        ("2. Objetivos", span("budget:objectives-start", "budget:hypotheses-start")),
        ("3. Hipótesis", span("budget:hypotheses-start", "budget:methodology-start")),
        ("4. Metodología", span("budget:methodology-start", "budget:theory-start")),
        ("5. Marco teórico", span("budget:theory-start", "budget:results-start")),
        ("6. Resultados", results),
        ("7. Conclusiones", span("budget:conclusions-start", "budget:references-start")),
    ]

    print(f"{'Bloque':<34}{'Páginas':>8}")
    print("-" * 42)
    for name, pages in chapters:
        print(f"{name:<34}{pages:>8}")
    print("-" * 42)
    print(f"{'Preliminares':<34}{preliminaries:>8}")
    print(f"{'Cuerpo (caps. 1-7)':<34}{body:>8}")
    print(f"{'Referencias':<34}{references:>8}")
    print(f"{'Anexos':<34}{appendices:>8}")
    print(f"{'Total físico':<34}{m['budget:appendices-end']:>8}")

    if "budget:review-start" in m and "budget:review-end" in m:
        review = span("budget:review-start", "budget:review-end") + 1
        print(f"\nBloque de revisión dentro de Resultados: {review} páginas")

    print("\nContraste con las Instrucciones VIU")
    fraction = results / body if body else 0.0
    checks = [
        (f"cuerpo en [{VIU_BODY_MIN}, {VIU_BODY_MAX}]", VIU_BODY_MIN <= body <= VIU_BODY_MAX, body),
        (f"anexos <= {VIU_APPENDIX_MAX}", appendices <= VIU_APPENDIX_MAX, appendices),
        ("resultados >= 50 % del cuerpo", fraction >= VIU_RESULTS_MIN_FRACTION, f"{fraction:.1%}"),
    ]
    failed = 0
    for label, ok, value in checks:
        print(f"  [{'OK ' if ok else 'NO '}] {label}: {value}")
        failed += 0 if ok else 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

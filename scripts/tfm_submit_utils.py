"""Utilities for the TFM submit-ready automation scripts.

The helpers in this file are intentionally small and dependency-light.  They
read existing canonical artifacts and generate documentation; they do not
rerun SP1-SP8 experiments or mutate canonical result directories.
"""

from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DOCS_GENERATED = ROOT / "docs" / "generated"
THEORY_ROOT = ROOT / "results" / "theory_validation"


@dataclass(frozen=True)
class CanonicalSP:
    sp: str
    title: str
    config: Path
    result_dir: Path
    primary_metric_hint: str


CANONICAL_SPS: dict[str, CanonicalSP] = {
    "SP1": CanonicalSP(
        "SP1",
        "Reclutamiento por quorum",
        Path("configs/experiments/sp1/SP1_MC_recruitment_comparison.yaml"),
        Path("results/sp1/SP1_MC_recruitment_comparison"),
        "optimality_gap_vs_oracle",
    ),
    "SP2": CanonicalSP(
        "SP2",
        "Capacidad efectiva heterogenea",
        Path("configs/experiments/sp2/SP2_MC_capacity_comparison.yaml"),
        Path("results/sp2/SP2_MC_capacity_comparison"),
        "performance_gap_vs_reference",
    ),
    "SP3": CanonicalSP(
        "SP3",
        "Factibilidad wrench planar",
        Path("configs/experiments/sp3/SP3_MC_wrench_comparison_high_power.yaml"),
        Path("results/sp3/SP3_MC_wrench_comparison_high_power"),
        "optimality_gap_vs_wrench_oracle",
    ),
    "SP4": CanonicalSP(
        "SP4",
        "Movimiento y llegada segura",
        Path("configs/experiments/sp4/SP4_MC_motion_comparison_high_power.yaml"),
        Path("results/sp4/SP4_MC_motion_comparison_high_power"),
        "performance_gap_vs_reference",
    ),
    "SP5": CanonicalSP(
        "SP5",
        "Transporte cooperativo con obstaculos",
        Path("configs/experiments/sp5/SP5_MC_cooperative_transport_high_power.yaml"),
        Path("results/sp5/SP5_MC_cooperative_transport_high_power"),
        "performance_gap_vs_reference",
    ),
    "SP6": CanonicalSP(
        "SP6",
        "Robustez operativa",
        Path("configs/experiments/sp6/SP6_MC_robustness_comparison_high_power.yaml"),
        Path("results/sp6/SP6_MC_robustness_comparison_high_power"),
        "performance_gap_vs_reference",
    ),
    "SP7": CanonicalSP(
        "SP7",
        "Grafo endogeno y comunicacion",
        Path("configs/experiments/sp7/SP7_MC_communication_robustness_high_power.yaml"),
        Path("results/sp7/SP7_MC_communication_robustness_high_power"),
        "transport_success_rate",
    ),
    "SP8": CanonicalSP(
        "SP8",
        "Escala warehouse e intratabilidad",
        Path("configs/experiments/sp8/SP8_MC_fleet_ladder_high_power.yaml"),
        Path("results/sp8/SP8_MC_fleet_ladder_high_power"),
        "task_completion_rate",
    ),
}


FAMILY_LABELS = {
    "classic": "Clasicas locales",
    "classic_local": "Clasicas locales",
    "model_based_oracle": "Referencias centralizadas",
    "model_based_reference": "Referencias centralizadas",
    "reference": "Referencias centralizadas",
    "market": "Mercado/subasta",
    "auction": "Mercado/subasta",
    "population": "Dinamicas poblacionales",
    "model_based": "Modelo / poblacional / primal-dual",
    "nash_seeking": "Primal-dual / Nash seeking",
    "data_driven": "Aprendidas",
    "learned": "Aprendidas",
    "control": "Control/safety",
    "safety": "Control/safety",
}


REGIME_ROWS = [
    {
        "restriction": "Quorum entero",
        "family": "Poblacionales con cierre entero y referencias centralizadas",
        "sp": "SP1",
        "claim": "El reclutamiento se evalua por brecha contra oraculo, exito y coste.",
    },
    {
        "restriction": "Heterogeneidad de capacidad",
        "family": "Capacity-aware, payoff marginal y comparadores aprendidos",
        "sp": "SP2",
        "claim": "La cardinalidad deja de ser proxy suficiente de servicio.",
    },
    {
        "restriction": "Wrench vectorial",
        "family": "Verificacion explicita de contactos y residual wrench",
        "sp": "SP3",
        "claim": "El criterio escalar puede producir falsos positivos fisicos.",
    },
    {
        "restriction": "Movimiento seguro",
        "family": "CBF, campos con barrera y referencias temporales",
        "sp": "SP4",
        "claim": "La llegada debe leerse junto con colision, despeje, energia y tiempo.",
    },
    {
        "restriction": "Transporte con formacion",
        "family": "Cargo/caging/control de pose",
        "sp": "SP5",
        "claim": "Mover robots no equivale a transportar una carga extendida.",
    },
    {
        "restriction": "Fallos, bateria e inviabilidad",
        "family": "Recovery-aware y guarded/wrench-market",
        "sp": "SP6",
        "claim": "La robustez se mide por recuperacion y perdida de carga.",
    },
    {
        "restriction": "Comunicacion degradada",
        "family": "Connectivity-aware, relay y topologia temporal",
        "sp": "SP7",
        "claim": "La conectividad temporal condiciona el transporte cooperativo.",
    },
    {
        "restriction": "Escala e intratabilidad",
        "family": "Distribuidas, jerarquicas y tensor/market",
        "sp": "SP8",
        "claim": "La escala cambia la utilidad practica de las familias.",
    },
    {
        "restriction": "Brecha teoria-implementacion",
        "family": "Predicho-vs-medido en CoppeliaSim/Pioneer",
        "sp": "SP9",
        "claim": "Solo se reporta si existen CSV, figuras y manifest reales.",
    },
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def latex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def write_latex_table(
    path: Path,
    headers: list[str],
    rows: list[list[object]],
    caption: str,
    label: str,
) -> None:
    ensure_dir(path.parent)
    colspec = "l" * len(headers)
    lines = [
        "% Auto-generated. Do not edit by hand.",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\scriptsize",
        "\\resizebox{\\textwidth}{!}{%",
        f"\\begin{{tabular}}{{{colspec}}}",
        "\\toprule",
        " & ".join(latex_escape(h) for h in headers) + r" \\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(latex_escape(cell) for cell in row) + r" \\")
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "}%",
            f"\\caption{{{latex_escape(caption)}}}",
            f"\\label{{{label}}}",
            "\\end{table}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_markdown_table(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    ensure_dir(path.parent)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def canonical_file(sp: str, filename: str) -> Path:
    return ROOT / CANONICAL_SPS[sp].result_dir / "tables" / filename


def audit_file(sp: str) -> Path:
    return ROOT / CANONICAL_SPS[sp].result_dir / "theory_audit.json"


def failed_checks_from_audit(path: Path) -> int | str:
    if not path.exists():
        return "missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "invalid-json"
    if isinstance(data.get("failed_checks"), int):
        return data["failed_checks"]
    if isinstance(data.get("failed_checks"), list):
        return len(data["failed_checks"])
    if isinstance(data.get("summary"), dict) and "failed_checks" in data["summary"]:
        return data["summary"]["failed_checks"]
    if "failed" in data and isinstance(data["failed"], list):
        return len(data["failed"])
    return 0


def normalize_family(row: dict[str, str]) -> str:
    raw = (row.get("method_family") or row.get("family") or "").strip()
    variant = (row.get("method_variant") or row.get("method") or "").lower()
    group = (row.get("method_comparison_group") or "").lower()
    if "oracle" in raw or "oracle" in variant or "reference" in group:
        return "Referencias centralizadas"
    if "mappo" in variant or "neural" in variant or "imitation" in variant:
        return "Aprendidas"
    if "cbf" in variant or "hocbf" in variant or "safety" in variant:
        return "Control/safety"
    if "market" in variant or "cbba" in variant or "auction" in variant:
        return "Mercado/subasta"
    if any(token in variant for token in ("smith", "replicator", "logit", "bnn", "brown")):
        return "Dinamicas poblacionales"
    if any(token in variant for token in ("primal", "dual", "vgne", "tensor")):
        return "Primal-dual / Nash seeking"
    if raw in FAMILY_LABELS:
        return FAMILY_LABELS[raw]
    if "classic" in raw or "greedy" in variant or "apf" in variant:
        return "Clasicas locales"
    if raw:
        return raw
    return "Familia no clasificada"


def best_metric_column(rows: list[dict[str, str]], hint: str | None = None) -> str:
    if hint and rows and hint in rows[0]:
        return hint
    preferred = [
        "performance_gap_vs_reference_mean",
        "optimality_gap_vs_wrench_oracle_mean",
        "optimality_gap_vs_oracle_mean",
        "task_completion_rate_mean",
        "transport_success_rate_mean",
        "wrench_feasible_rate_mean",
        "score_value_mean",
        "served_load_rate_mean",
    ]
    if rows:
        for column in preferred:
            if column in rows[0]:
                return column
    return "rank"


def float_or_nan(value: object) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return math.nan


def short_sci(value: object) -> str:
    number = float_or_nan(value)
    if math.isnan(number):
        return str(value) if value not in (None, "") else ""
    if number == 0:
        return "0"
    if abs(number) < 0.001 or abs(number) >= 10000:
        return f"{number:.2e}"
    return f"{number:.4g}"


def slugify(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text.strip().lower())
    return text.strip("_") or "item"

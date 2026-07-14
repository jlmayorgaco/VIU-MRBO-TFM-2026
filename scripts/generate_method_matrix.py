"""Generate method-family by SP matrix from canonical ranking CSV files."""

from __future__ import annotations

from collections import defaultdict

from tfm_submit_utils import (
    CANONICAL_SPS,
    DOCS_GENERATED,
    ROOT,
    best_metric_column,
    canonical_file,
    ensure_dir,
    normalize_family,
    read_csv,
    write_csv,
    write_latex_table,
    write_markdown_table,
)


FAMILY_ORDER = [
    "Clasicas locales",
    "Referencias centralizadas",
    "Mercado/subasta",
    "Dinamicas poblacionales",
    "Primal-dual / Nash seeking",
    "Aprendidas",
    "Control/safety",
    "Modelo / poblacional / primal-dual",
    "Familia no clasificada",
]


def cell_for_family(rows: list[dict[str, str]], family: str, metric: str) -> tuple[str, str]:
    family_rows = [row for row in rows if normalize_family(row) == family]
    if not family_rows:
        return "--", ""
    best = sorted(family_rows, key=lambda row: float(row.get("rank", "999999") or 999999))[0]
    method = best.get("method_label") or best.get("method") or "unknown"
    value = best.get(metric, best.get("rank", ""))
    marker = f"star: {method}"
    if family == "Referencias centralizadas" or "oracle" in (best.get("method", "") + best.get("method_variant", "")).lower():
        marker = f"ref: {method}"
    return marker, str(value)


def _lower_is_better(metric: str) -> bool:
    return any(token in metric.lower() for token in (
        "regret", "gap", "collision", "timeout", "error", "residual",
        "runtime", "messages", "energy", "lost", "violation",
    ))


def load_canonical_ranking(sp: str) -> tuple[list[dict[str, str]], str, str | None]:
    """Load a promoted ranking or derive one transparently from its summary table."""
    meta = CANONICAL_SPS[sp]
    ranking_path = canonical_file(sp, "performance_ranking.csv")
    if ranking_path.exists():
        rows = read_csv(ranking_path)
        return rows, best_metric_column(rows, meta.primary_metric_hint + "_mean"), None

    summary_path = canonical_file(sp, "summary.csv")
    if not summary_path.exists():
        return [], "rank", str(summary_path.relative_to(ROOT))
    rows = read_csv(summary_path)
    if not rows:
        return [], "rank", str(summary_path.relative_to(ROOT))
    candidates = (meta.primary_metric_hint, meta.primary_metric_hint + "_mean")
    metric = next((item for item in candidates if item in rows[0]), best_metric_column(rows))
    ordered = sorted(
        rows,
        key=lambda row: float(row.get(metric, "nan") or "nan"),
        reverse=not _lower_is_better(metric),
    )
    for rank, row in enumerate(ordered, start=1):
        row["rank"] = str(rank)
        row.setdefault("method_variant", row.get("method", ""))
    return ordered, metric, None


def main() -> int:
    ensure_dir(DOCS_GENERATED)
    rankings: dict[str, list[dict[str, str]]] = {}
    metrics: dict[str, str] = {}
    families = set(FAMILY_ORDER)
    missing: list[str] = []
    for sp in CANONICAL_SPS:
        rows, metric, missing_path = load_canonical_ranking(sp)
        if missing_path:
            missing.append(missing_path)
            continue
        rankings[sp] = rows
        metrics[sp] = metric
        for row in rows:
            families.add(normalize_family(row))
    if missing:
        raise FileNotFoundError("Missing canonical ranking and summary files: " + ", ".join(missing))

    ordered_families = [family for family in FAMILY_ORDER if family in families]
    ordered_families.extend(sorted(families - set(ordered_families)))
    csv_rows: list[dict[str, object]] = []
    tex_rows: list[list[object]] = []
    headers = ["Familia"] + list(CANONICAL_SPS.keys())

    for family in ordered_families:
        row: dict[str, object] = {"family": family}
        tex_row: list[object] = [family]
        for sp in CANONICAL_SPS:
            cell, value = cell_for_family(rankings[sp], family, metrics[sp])
            row[sp] = cell
            row[f"{sp}_metric"] = metrics[sp]
            row[f"{sp}_value"] = value
            if cell == "--":
                tex_cell = "--"
            elif cell.startswith("ref:"):
                tex_cell = "ref: " + cell[5:]
            else:
                tex_cell = "star: " + cell[6:]
            tex_row.append(tex_cell)
        csv_rows.append(row)
        tex_rows.append(tex_row)

    fieldnames = ["family"]
    for sp in CANONICAL_SPS:
        fieldnames.extend([sp, f"{sp}_metric", f"{sp}_value"])
    write_csv(DOCS_GENERATED / "method_matrix.csv", csv_rows, fieldnames)
    write_latex_table(
        DOCS_GENERATED / "method_matrix.tex",
        headers,
        tex_rows,
        "Matriz metodo por SP generada desde rankings canonicos o, cuando no existe ranking separado, desde la tabla summary promovida.",
        "tab:method-matrix-generated",
    )
    write_markdown_table(DOCS_GENERATED / "method_matrix.md", headers, tex_rows)
    print("Wrote docs/generated/method_matrix.{csv,md,tex}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build a consolidated statistics annex from canonical hypothesis tables."""

from __future__ import annotations

from tfm_submit_utils import CANONICAL_SPS, DOCS_GENERATED, ROOT, canonical_file, read_csv, short_sci, write_csv, write_latex_table, write_markdown_table


def normalize_row(sp: str, row: dict[str, str]) -> dict[str, object]:
    p_holm = row.get("p_value_holm") or row.get("p_holm") or row.get("p_value") or ""
    effect = row.get("effect_size") or row.get("effect") or ""
    verdict = "rechaza H0" if str(row.get("reject_holm") or row.get("reject")).lower() == "true" else "no rechaza H0"
    return {
        "SP": sp,
        "campaign": str(CANONICAL_SPS[sp].result_dir),
        "hypothesis": row.get("id", ""),
        "comparison": row.get("methods", ""),
        "metric": row.get("metric", ""),
        "test": row.get("test", row.get("class", "")),
        "n": row.get("n_pairs", row.get("n", "")),
        "p_raw": row.get("p_value_raw", row.get("p_value", "")),
        "p_holm": p_holm,
        "effect": effect,
        "effect_name": row.get("effect_size_name", row.get("effect_name", "")),
        "ci95_low": row.get("ci95_low", ""),
        "ci95_high": row.get("ci95_high", ""),
        "verdict": verdict,
        "source_csv": str(canonical_file(sp, "hypothesis_results.csv").relative_to(ROOT)),
    }


def main() -> int:
    rows: list[dict[str, object]] = []
    missing: list[str] = []
    for sp in CANONICAL_SPS:
        path = canonical_file(sp, "hypothesis_results.csv")
        if not path.exists():
            missing.append(str(path.relative_to(ROOT)))
            continue
        for row in read_csv(path):
            rows.append(normalize_row(sp, row))
    if missing:
        raise FileNotFoundError("Missing hypothesis CSV files: " + ", ".join(missing))

    fieldnames = [
        "SP",
        "campaign",
        "hypothesis",
        "comparison",
        "metric",
        "test",
        "n",
        "p_raw",
        "p_holm",
        "effect",
        "effect_name",
        "ci95_low",
        "ci95_high",
        "verdict",
        "source_csv",
    ]
    write_csv(DOCS_GENERATED / "stats_master_table.csv", rows, fieldnames)
    display_rows = [
        [
            row["SP"],
            row["hypothesis"],
            row["metric"],
            row["n"],
            short_sci(row["p_holm"]),
            short_sci(row["effect"]),
            row["verdict"],
        ]
        for row in rows[:45]
    ]
    headers = ["SP", "Hipotesis", "Metrica", "n", "p-Holm", "Efecto", "Veredicto"]
    write_latex_table(
        DOCS_GENERATED / "stats_master_table.tex",
        headers,
        display_rows,
        "Tabla estadistica consolidada generada desde hypothesis_results.csv canonicos.",
        "tab:stats-master-generated",
    )
    write_markdown_table(DOCS_GENERATED / "stats_master_table.md", headers, display_rows)
    print(f"Wrote docs/generated/stats_master_table.* with {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

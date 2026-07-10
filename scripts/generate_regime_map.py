"""Generate the thesis regime map from canonical hypothesis CSV files."""

from __future__ import annotations

from tfm_submit_utils import (
    DOCS_GENERATED,
    REGIME_ROWS,
    ROOT,
    canonical_file,
    ensure_dir,
    read_csv,
    short_sci,
    write_csv,
    write_latex_table,
    write_markdown_table,
)


def evidence_for_sp(sp: str) -> tuple[str, str, str]:
    if sp == "SP9":
        return "pending", "", "results/sp9 only if promoted"
    path = canonical_file(sp, "hypothesis_results.csv")
    if not path.exists():
        return "missing", "", str(path.relative_to(ROOT))
    rows = read_csv(path)
    rejected = [row for row in rows if str(row.get("reject_holm") or row.get("reject")).lower() == "true"]
    row = rejected[0] if rejected else (rows[0] if rows else {})
    hypothesis = row.get("id", "")
    p_holm = row.get("p_value_holm") or row.get("p_holm") or row.get("p_value") or ""
    metric = row.get("metric", "")
    evidence = f"{hypothesis}; metric={metric}; p-Holm={short_sci(p_holm)}"
    return evidence, p_holm, str(path.relative_to(ROOT))


def main() -> int:
    ensure_dir(DOCS_GENERATED)
    rows: list[dict[str, object]] = []
    tex_rows: list[list[object]] = []
    for item in REGIME_ROWS:
        evidence, p_holm, source = evidence_for_sp(item["sp"])
        row = {
            "restriction": item["restriction"],
            "family": item["family"],
            "sp": item["sp"],
            "evidence": evidence,
            "p_holm": p_holm,
            "safe_claim": item["claim"],
            "source_csv": source,
        }
        rows.append(row)
        tex_rows.append([row["restriction"], row["family"], row["sp"], row["evidence"], row["safe_claim"]])
    write_csv(
        DOCS_GENERATED / "regime_map.csv",
        rows,
        ["restriction", "family", "sp", "evidence", "p_holm", "safe_claim", "source_csv"],
    )
    headers = ["Restriccion", "Familia", "SP", "Evidencia", "Claim seguro"]
    write_latex_table(
        DOCS_GENERATED / "regime_map.tex",
        headers,
        tex_rows,
        "Mapa de regimenes generado desde hipotesis canonicas.",
        "tab:regime-map-generated",
    )
    write_markdown_table(DOCS_GENERATED / "regime_map.md", headers, tex_rows)
    print("Wrote docs/generated/regime_map.{csv,md,tex}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Stage 4: derive analysis tables, figures, and an adversarial novelty audit.

All counts and plots are generated from the frozen Stage 3 evidence matrix and
the Stage 2 candidate derivative. No result value is entered by hand. The
novelty document separates observations supported by the review dataset from
hypotheses that still require close reading, Web of Science comparison, or new
experiments.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


BASE = Path(__file__).resolve().parents[1]
PROCESSED = BASE / "data" / "processed"
MATRIX = PROCESSED / "fulltext_evidence_matrix.csv"
CORPUS = PROCESSED / "candidate_corpus_stage2.csv"
TABLES = BASE / "tables"
FIGURES = BASE / "figures"
REPORTS = BASE / "reports"
FINAL = BASE / "final"
for directory in [TABLES, FIGURES, REPORTS, FINAL]:
    directory.mkdir(parents=True, exist_ok=True)


def load_bootstrap_module():
    path = BASE / "scripts" / "bootstrap_literature.py"
    spec = importlib.util.spec_from_file_location("bootstrap_for_stage4", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load WoS coverage helpers from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BOOT = load_bootstrap_module()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return str(value or "").strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def split_terms(value: Any) -> list[str]:
    return [item.strip() for item in clean(value).split(";") if item.strip() and item.strip().lower() != "unclear"]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def plot_counts(data: dict[str, int], title: str, xlabel: str, output: Path, *, horizontal: bool = True) -> None:
    labels = list(data)
    values = [data[label] for label in labels]
    fig, ax = plt.subplots(figsize=(8.5, max(3.4, 0.36 * len(labels) + 1.2)))
    if horizontal:
        ax.barh(labels[::-1], values[::-1], color="#2b6cb0")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("")
        for index, value in enumerate(values[::-1]):
            ax.text(value, index, f" {value}", va="center", fontsize=8)
    else:
        ax.bar(labels, values, color="#2b6cb0")
        ax.set_ylabel(xlabel)
        ax.tick_params(axis="x", rotation=45)
    ax.set_title(title)
    ax.grid(axis="x" if horizontal else "y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def field_counts(df: pd.DataFrame, field: str, limit: int = 12) -> dict[str, int]:
    counts = Counter()
    for value in df[field].fillna(""):
        for term in split_terms(value):
            counts[term] += 1
    return dict(counts.most_common(limit))


def presence_counts(df: pd.DataFrame, field: str) -> dict[str, int]:
    return {"observed": int(df[field].fillna("").astype(str).str.strip().ne("").sum()), "not_observed": int(df[field].fillna("").astype(str).str.strip().eq("").sum())}


def make_analysis(number: int, slug: str, title: str, data: dict[str, int], description: str) -> dict[str, Any]:
    table_rows = [{"category": key, "count": value} for key, value in data.items()]
    table_path = TABLES / f"analysis_{number:02d}_{slug}.csv"
    figure_path = FIGURES / f"analysis_{number:02d}_{slug}.png"
    write_csv(table_path, table_rows)
    plot_counts(data, title, "records", figure_path)
    return {
        "analysis_id": f"A{number:02d}", "slug": slug, "title": title,
        "table": str(table_path.relative_to(BASE)), "figure": str(figure_path.relative_to(BASE)),
        "description": description, "categories": len(data), "records_counted": sum(data.values()),
    }


def multi_value_crosstab(df: pd.DataFrame, row_field: str, column_field: str, row_limit: int = 12, column_limit: int = 12) -> pd.DataFrame:
    pairs = Counter()
    row_counts = Counter()
    column_counts = Counter()
    for _, record in df.iterrows():
        rows = split_terms(record.get(row_field, ""))
        columns = split_terms(record.get(column_field, ""))
        for value in rows:
            row_counts[value] += 1
        for value in columns:
            column_counts[value] += 1
        for row_value in rows:
            for column_value in columns:
                pairs[(row_value, column_value)] += 1
    selected_rows = {value for value, _ in row_counts.most_common(row_limit)}
    selected_columns = {value for value, _ in column_counts.most_common(column_limit)}
    table = pd.DataFrame(0, index=sorted(selected_rows), columns=sorted(selected_columns), dtype=int)
    for (row_value, column_value), count in pairs.items():
        if row_value in selected_rows and column_value in selected_columns:
            table.loc[row_value, column_value] = count
    return table


def make_heatmap_analysis(number: int, slug: str, title: str, table: pd.DataFrame, description: str) -> dict[str, Any]:
    table_path = TABLES / f"analysis_{number:02d}_{slug}.csv"
    figure_path = FIGURES / f"analysis_{number:02d}_{slug}.png"
    table.reset_index(names="row_category").to_csv(table_path, index=False, encoding="utf-8")
    height = max(4.0, 0.42 * max(1, len(table.index)) + 1.5)
    width = max(6.5, 0.55 * max(1, len(table.columns)) + 3.0)
    fig, ax = plt.subplots(figsize=(width, height))
    values = table.to_numpy(dtype=float) if not table.empty else [[0]]
    image = ax.imshow(values, aspect="auto", cmap="Blues")
    if table.empty:
        ax.set_xticks([0], ["no observed pair"])
        ax.set_yticks([0], ["no observed pair"])
    else:
        ax.set_xticks(range(len(table.columns)), table.columns, rotation=45, ha="right")
        ax.set_yticks(range(len(table.index)), table.index)
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                ax.text(j, i, int(values[i, j]), ha="center", va="center", fontsize=8)
    ax.set_title(title)
    ax.set_xlabel("column category")
    ax.set_ylabel("row category")
    fig.colorbar(image, ax=ax, label="records")
    fig.tight_layout()
    fig.savefig(figure_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return {
        "analysis_id": f"A{number:02d}", "slug": slug, "title": title,
        "table": str(table_path.relative_to(BASE)), "figure": str(figure_path.relative_to(BASE)),
        "description": description, "categories": int(table.size), "records_counted": int(table.to_numpy().sum()) if not table.empty else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="reserved for reproducible reruns; all outputs are regenerated")
    parser.parse_args()
    if not MATRIX.exists() or not CORPUS.exists():
        raise FileNotFoundError("Stage 3 matrix and Stage 2 corpus are required before Stage 4")
    # Stage 4 owns only its generated analysis namespace. Remove stale outputs
    # from an earlier code version so the committed index matches the current
    # 16 required analyses plus the explicitly documented extras.
    for folder in [TABLES, FIGURES]:
        for generated in folder.glob("analysis_*"):
            generated.unlink()
        for generated in [folder / "stage4_analysis_summary.json", folder / "stage4_analysis_index.csv"]:
            if generated.exists():
                generated.unlink()
    matrix = pd.read_csv(MATRIX, dtype=str, keep_default_na=False)
    corpus = pd.read_csv(CORPUS, dtype=str, keep_default_na=False)
    wos_coverage = BOOT.wos_coverage_label(BOOT.wos_raw_files())
    wos_note = (
        "Web of Science is partially reconciled from declared exports; F01 and F02 remain incomplete."
        if wos_coverage == "wos_partially_reconciled"
        else "No complete Web of Science reconciliation is available."
    )
    if matrix["candidate_id"].duplicated().any() or corpus["candidate_id"].duplicated().any():
        raise RuntimeError("Stage 4 input invariant failure: duplicate candidate IDs")
    merged = matrix.merge(corpus[["candidate_id", "industrial_context", "heterogeneity", "coalition_or_team", "physical_transport", "contact_or_wrench", "local_communication", "robustness_or_failures", "problem_family", "method_family", "robot_type", "screening_decision"]], on="candidate_id", how="left", suffixes=("", "_screening"))
    analyses: list[dict[str, Any]] = []

    queue_count = int(len(corpus[corpus["screening_decision"].isin(["include_fulltext", "maybe_fulltext"])]))
    analyses.append(make_analysis(1, "selection_flow", "Study-selection and evidence flow", {
        "Stage 1C candidates": int(len(corpus)), "full-text queue": queue_count,
        "verified full text": int((matrix["evidence_strength"] == "fulltext_verified").sum()),
    }, "Corpus, acquisition queue, and verified full-text counts."))
    years = Counter(clean(value) if clean(value) else "unknown" for value in corpus["year"])
    analyses.append(make_analysis(2, "publication_year", "Temporal publication distribution", dict(sorted(years.items(), key=lambda item: (item[0] == "unknown", item[0]))), "Descriptive publication-year distribution."))
    analyses.append(make_analysis(3, "method_families", "Method-family distribution", field_counts(matrix, "method"), "Method terms located in extracted text; no performance claim is implied."))
    analyses.append(make_analysis(4, "coordination_architecture", "Coordination-architecture distribution", field_counts(matrix, "coordination_architecture"), "Architecture terms observed in extracted text."))
    robot_application = field_counts(merged, "robot_type")
    for term, count in field_counts(merged, "industrial_context").items():
        robot_application[f"application:{term}"] = count
    analyses.append(make_analysis(5, "robot_application", "Robot and application distribution", dict(sorted(robot_application.items(), key=lambda item: -item[1])[:14]), "Robot/application screening axes; `unclear` is excluded."))
    analyses.append(make_analysis(6, "heterogeneous_capabilities", "Heterogeneous-capability coverage", field_counts(merged, "heterogeneity"), "Heterogeneity and capability screening axes."))
    analyses.append(make_analysis(7, "coalition_team", "Coalition/team-formation coverage", field_counts(merged, "coalition_or_team"), "Coalition and team screening axes."))
    physical = field_counts(matrix, "physical_layer")
    for term, count in field_counts(merged, "physical_transport").items():
        physical[f"screening:{term}"] = count
    analyses.append(make_analysis(8, "physical_feasibility", "Physical-feasibility coverage", dict(sorted(physical.items(), key=lambda item: -item[1])[:14]), "Physical-layer terms and transport screening axes."))
    analyses.append(make_analysis(9, "contact_wrench", "Contact and wrench coverage", field_counts(merged, "contact_or_wrench"), "Contact/wrench screening axes; occurrence does not verify a mechanics proof."))
    analyses.append(make_analysis(10, "communication_assumptions", "Communication-assumption coverage", field_counts(matrix, "information_assumptions"), "Information assumptions located in actual text where full text was available."))
    failure_terms = {term: count for term, count in field_counts(matrix, "execution").items() if any(key in term.lower() for key in ["failure", "fault", "recovery", "replacement", "reconfiguration", "packet", "delay"])}
    for term, count in field_counts(merged, "robustness_or_failures").items():
        failure_terms[f"screening:{term}"] = count
    analyses.append(make_analysis(11, "failure_recovery", "Failure and recovery coverage", failure_terms, "Failure/recovery terms observed in text and screening."))
    experiment_levels = {
        "verified full text": int((matrix["evidence_strength"] == "fulltext_verified").sum()),
        "full text with simulation terms": int(((matrix["evidence_strength"] == "fulltext_verified") & matrix["experiments"].str.contains("simulation|simulated", case=False, regex=True, na=False)).sum()),
        "full text with hardware terms": int(((matrix["evidence_strength"] == "fulltext_verified") & matrix["experiments"].str.contains("hardware|real robot|robot platform", case=False, regex=True, na=False)).sum()),
        "full text with benchmark/ablation terms": int(((matrix["evidence_strength"] == "fulltext_verified") & matrix["experiments"].str.contains("benchmark|ablation", case=False, regex=True, na=False)).sum()),
        "abstract-only": int((matrix["evidence_strength"] == "abstract_only").sum()),
    }
    analyses.append(make_analysis(12, "experimental_validation", "Experimental validation level", experiment_levels, "Evidence availability and observed validation vocabulary."))

    method_capability = multi_value_crosstab(matrix[matrix["evidence_strength"] == "fulltext_verified"], "method", "physical_layer")
    analyses.append(make_heatmap_analysis(13, "method_x_capability", "Method x physical capability evidence map", method_capability, "Co-occurrence of method and physical-layer terms in verified full text."))
    problem_family = multi_value_crosstab(merged, "problem_family", "method_family")
    analyses.append(make_heatmap_analysis(14, "problem_stage_literature_family", "Problem-stage x literature-family matrix", problem_family, "Co-occurrence of Stage 1C problem-family and method-family screening tags."))

    def observed(column: str) -> pd.Series:
        return merged[column].map(lambda value: bool(split_terms(value)))

    sp_masks = {
        "SP1": merged["problem_family"].str.contains("allocation|coalition", case=False, regex=True, na=False),
        "SP2": observed("physical_transport") | observed("contact_or_wrench"),
        "SP3": merged["problem_family"].str.contains("planning|navigation|industrial|logistics|safety", case=False, regex=True, na=False),
    }
    sp_rows = []
    evidence_order = ["fulltext_verified", "abstract_only", "metadata_only", "retrieval_error"]
    for sp, mask in sp_masks.items():
        for evidence in evidence_order:
            sp_rows.append({"subproblem": sp, "evidence_strength": evidence, "records": int((mask & (merged["evidence_strength"] == evidence)).sum())})
    write_csv(TABLES / "analysis_15_evidence_map_tfm_architecture_detail.csv", sp_rows)
    evidence_map = pd.DataFrame(0, index=list(sp_masks), columns=evidence_order, dtype=int)
    for item in sp_rows:
        evidence_map.loc[item["subproblem"], item["evidence_strength"]] = item["records"]
    analyses.append(make_heatmap_analysis(15, "evidence_map_tfm_architecture", "Evidence map for the TFM architecture", evidence_map, "SP1-SP3 screening interfaces crossed with evidence strength."))
    # Preserve the compact interface summary used by Stage 5 and expose it as
    # a separate machine-readable detail table.
    interface_rows = []
    for sp, mask in sp_masks.items():
        interface_rows.append({"subproblem": sp, "all_queue_records": int(mask.sum()), "verified_fulltext_records": int((mask & (merged["evidence_strength"] == "fulltext_verified")).sum())})
    write_csv(TABLES / "analysis_16_tfm_interface_coverage_detail.csv", interface_rows)

    gap_specs = [
        ("assignment", merged["problem_family"].str.contains("allocation", case=False, na=False)),
        ("coalition closure", observed("coalition_or_team")),
        ("physical feasibility", observed("contact_or_wrench") | observed("physical_transport")),
        ("cooperative transport", observed("physical_transport")),
        ("safety", merged["problem_family"].str.contains("safety|navigation", case=False, regex=True, na=False)),
        ("failure recovery", observed("robustness_or_failures")),
        ("traffic/safety navigation", merged["problem_family"].str.contains("safety_navigation|planning|logistics", case=False, regex=True, na=False)),
        ("communication degradation", merged["information_assumptions"].str.contains("limited|packet|delay|switching", case=False, regex=True, na=False)),
    ]
    gap_rows = []
    gap_plot = {}
    for label, mask in gap_specs:
        queue_signal = int(mask.sum())
        full_signal = int((mask & (merged["evidence_strength"] == "fulltext_verified")).sum())
        gap_status = "present_in_verified_text" if full_signal else ("screening_signal_only" if queue_signal else "not_observed_in_review")
        gap_rows.append({"capability": label, "queue_signal": queue_signal, "verified_fulltext": full_signal, "coverage_status": gap_status})
        gap_plot[f"{label}: queue"] = queue_signal
        gap_plot[f"{label}: full text"] = full_signal
    write_csv(TABLES / "analysis_16_explicit_gap_map_detail.csv", gap_rows)
    analyses.append(make_analysis(16, "explicit_gap_map", "Explicit gap map", gap_plot, "Coverage indicators for capabilities required by the TFM; low counts are not proof of absence."))

    # Additional descriptive analyses are generated after the 16 required
    # analyses so evidence strength, provisional roles, theory, and execution
    # remain directly inspectable without displacing the required map set.
    analyses.append(make_analysis(17, "evidence_strength", "Evidence strength", dict(Counter(matrix["evidence_strength"])), "Separates verified full text from abstract and metadata-only records."))
    analyses.append(make_analysis(18, "scientific_role", "Provisional scientific role", dict(Counter(matrix["scientific_role"])), "Role labels are structural first-pass labels and not a claim of influence."))
    analyses.append(make_analysis(19, "theory_terms", "Theory and guarantee terms", field_counts(matrix, "theory"), "Observed theory vocabulary; presence does not verify a theorem or proof."))
    analyses.append(make_analysis(20, "execution_terms", "Execution and motion terms", field_counts(matrix, "execution"), "Motion, docking, navigation, and recovery terms located in text."))

    summary = {
        "generated_at_utc": utc_now(),
        "matrix_sha256": sha256(MATRIX),
        "corpus_sha256": sha256(CORPUS),
        "analysis_count": len(analyses),
        "analyses": analyses,
    }
    (TABLES / "stage4_analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(TABLES / "stage4_analysis_index.csv", analyses)

    ranked = []
    for _, row in merged.iterrows():
        signal_count = sum(bool(clean(row.get(field))) for field in ["problem_formulation", "coordination_architecture", "method", "physical_layer", "execution", "theory", "experiments"])
        score = signal_count * 2 + (3 if row["evidence_strength"] == "fulltext_verified" else 1 if row["evidence_strength"] == "abstract_only" else 0)
        if row["scientific_role"] in {"CORE", "ENABLING", "FOUNDATIONAL"}:
            score += 2
        ranked.append({"score": score, **row.to_dict()})
    ranked = sorted(ranked, key=lambda item: (-int(item["score"]), clean(item.get("title"))))
    core = [row for row in ranked if row.get("scientific_role") == "CORE"][:100]
    enabling = [row for row in ranked if row.get("scientific_role") == "ENABLING"][:150]
    selected_fields = ["candidate_id", "title", "authors", "year", "venue", "doi", "evidence_strength", "scientific_role", "coding_status", "score", "selection_reason"]
    for target, rows, reason in [(FINAL / "core_papers.csv", core, "CORE structural role plus highest observed evidence signal"), (FINAL / "enabling_papers.csv", enabling, "ENABLING structural role plus observed method/physical/theory signal")]:
        output = []
        for row in rows:
            output.append({key: row.get(key, "") for key in selected_fields[:-1]} | {"selection_reason": reason})
        write_csv(target, output)
    excluded = corpus[corpus["screening_decision"] == "exclude"].copy()
    excluded.to_csv(FINAL / "excluded_papers.csv", index=False, encoding="utf-8")

    novelty_lines = [
        "# Adversarial novelty audit",
        "",
        f"Generated UTC: {utc_now()}",
        "",
        "## Status",
        "",
        f"This is a review-dataset audit, not a novelty determination. {wos_note} The coding is a deterministic structural first pass. No statement below should be read as proof that the TFM contribution is new.",
        "",
        "## Strong prior-art candidates for close reading",
        "",
        "The following records were ranked by observed scope signals and evidence availability. Ranking is a triage aid, not a quality or priority judgment.",
        "",
    ]
    for index, row in enumerate(ranked[:30], start=1):
        doi = clean(row.get("doi"))
        citation = f"[DOI](https://doi.org/{doi})" if doi else "DOI unavailable"
        novelty_lines.append(f"{index}. **{clean(row.get('title'))}** — {clean(row.get('year')) or 'year n/a'}; role `{clean(row.get('scientific_role'))}`; evidence `{clean(row.get('evidence_strength'))}`; signals {row.get('score')}; {citation}.")
    novelty_lines += [
        "",
        "## TFM axis-by-axis challenge",
        "",
        "- SP1 coalition formation: prior-art candidates are present in the corpus; the remaining question is whether a white-box local potential/population-game mechanism adds a verified capability beyond existing coalition, auction, consensus, or distributed-optimization methods.",
        "- SP2 rigid/prehensile transport: payload, contact, wrench, formation, and manipulation terms occur in the corpus; close reading must test whether mechanical feasibility and wrench distribution are jointly modeled rather than merely mentioned.",
        "- SP3 multi-coalition traffic: planning, safety, warehouse, and logistics signals occur, but their coupling to active transport coalitions must be coded from full text before any gap claim.",
        "- Cross-interface claim: the dataset does not establish that the complete SP1-SP3 combination is absent. Treat integration as a hypothesis to test against the ranked prior-art records and complete WoS reconciliation.",
        "",
        "## Prohibited conclusions at this stage",
        "",
        "Do not write that the TFM is the first, optimal, convergent, stable, robust, scalable, or state of the art. Do not infer physical feasibility from a Nash equilibrium, or safety from a task-allocation result. Do not treat abstract-only or metadata-only records as detailed methodological evidence.",
    ]
    (REPORTS / "adversarial_novelty_audit.md").write_text("\n".join(novelty_lines) + "\n", encoding="utf-8")

    qa = f"""# Stage 4 synthesis QA

Run UTC: {utc_now()}

- Stage 3 matrix SHA-256: `{sha256(MATRIX)}`
- Stage 2 corpus SHA-256: `{sha256(CORPUS)}`
- Records in matrix: **{len(matrix)}**
- Analyses generated: **{len(analyses)}**
- Tables generated: **{len(list(TABLES.glob('analysis_*.csv')))}** plus summary/index
- Figures generated: **{len(list(FIGURES.glob('analysis_*.png')))}**
- Core triage rows: **{len(core)}**; enabling triage rows: **{len(enabling)}**; excluded rows: **{len(excluded)}**

All counts and figures are derived from CSV inputs at run time. The novelty
audit is adversarial by design: it reports strong prior-art candidates and
explicitly withholds a final novelty conclusion until close reading and
complete Web of Science reconciliation are available. Current WoS coverage:
`{wos_coverage}`.
"""
    (REPORTS / "stage4_synthesis_qa.md").write_text(qa, encoding="utf-8")
    print(qa)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

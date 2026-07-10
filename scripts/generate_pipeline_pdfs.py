"""Generate SP1-SP8 methodology and results PDFs from pipeline artifacts.

Run with a Python that has reportlab installed. The bundled Codex runtime works:

    C:\\Users\\walla\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe scripts\\generate_pipeline_pdfs.py
"""

from __future__ import annotations

import csv
import html
import json
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except ModuleNotFoundError as exc:  # pragma: no cover - operational guard
    raise SystemExit(
        "Missing reportlab. Use the bundled Codex Python runtime documented in this script header."
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = ROOT / "configs" / "experiments"
RESULTS_ROOT = ROOT / "results"
OUT_DIR = ROOT / "output" / "pdf"

SP_INFO = {
    "sp1": {
        "title": "SP1 - Recruitment and Coalition Allocation",
        "question": "Which AMRs should be recruited for each load under homogeneous robots and heterogeneous load demand?",
        "model": "Assignment and coalition feasibility with travel, communication, under/over-assignment, and oracle-gap metrics.",
    },
    "sp2": {
        "title": "SP2 - Capacity-Aware Heterogeneous Loads",
        "question": "Does the allocation satisfy heterogeneous load capacities while controlling shortage, waste, travel, and communication cost?",
        "model": "Capacity-aware coalition allocation with model-based tuning, marginal-payoff ablations, and capacity diagnostics.",
    },
    "sp3": {
        "title": "SP3 - Roles, Slots, and Wrench Feasibility",
        "question": "Can the recruited coalition generate the planar wrench required by each payload, not only scalar capacity?",
        "model": "Planar quasi-static wrench model with slots, residual wrench, false positives of scalar criteria, and pose transport extensions.",
    },
    "sp4": {
        "title": "SP4 - Motion, Safety, and Communication-Limited Navigation",
        "question": "Can selected AMRs reach assigned targets safely under obstacles, communication limits, and trajectory costs?",
        "model": "AMR motion fields, APF/VO/CBF baselines, Smith-style motion fields, and communication-radius degradation.",
    },
    "sp5": {
        "title": "SP5 - Cooperative Payload Transport",
        "question": "Can AMR coalitions pick, carry or push/drag payloads to target pose while avoiding obstacles and other robot groups?",
        "model": "Euler-Lagrange payload pose transport with wrench slots, formation preservation, push/drag and cargo modes.",
    },
    "sp6": {
        "title": "SP6 - Operational Robustness and Replacement",
        "question": "What happens when robots lose battery, fail, slow down, or obstacles appear during payload transport?",
        "model": "Event-driven recovery with slot handover, replacement AMRs, degraded-speed support, wrench margin, and task completion.",
    },
    "sp7": {
        "title": "SP7 - Communication, Sensing, and Temporal Connectivity",
        "question": "How do communication radius, packet loss, delay, jitter and sensing degradation affect cooperative payload transport across multiple AMR groups?",
        "model": "Temporal unit-disk communication graphs over SP5 transport worlds, with packet delivery, relay connectivity, sensing coverage, obstacle avoidance and transport success metrics.",
    },
    "sp8": {
        "title": "SP8 - Warehouse-Scale Scalability and Intractability",
        "question": "When many AMRs and many simultaneous loads are present, which centralized methods become computationally impractical and which distributed/hierarchical methods still provide useful wrench-aware transport decisions?",
        "model": "Mesoscopic vectorized warehouse-scale model with hundreds to thousands of AMRs, moving loads, wrench/torque checks, static/mobile obstacles, timeout declarations, complexity proxies and resource-normalized rankings.",
    },
}

METHOD_FIELD_ORDER = [
    "sp",
    "method",
    "method_label",
    "method_ownership",
    "method_family",
    "method_scope",
    "method_variant",
    "method_comparison_group",
    "method_training_type",
    "method_execution_model",
    "method_communication_pattern",
    "method_trainable_parameters",
    "method_tuned_parameters",
    "method_training_episodes",
    "method_uses_neural_policy",
    "method_uses_decoder",
]

PREFERRED_METRICS = [
    "coalition_success_rate_mean",
    "served_load_rate_mean",
    "demand_satisfaction_ratio_mean",
    "load_success_rate_mean",
    "capacity_satisfaction_ratio_mean",
    "capacity_success_rate_mean",
    "wrench_feasible_rate_mean",
    "false_positive_rate_mean",
    "mean_wrench_residual_norm_mean",
    "arrival_success_rate_mean",
    "collision_rate_mean",
    "transport_success_mean",
    "target_reached_mean",
    "formation_integrity_rate_mean",
    "recovery_success_mean",
    "task_completion_rate_mean",
    "solved_rate_mean",
    "timeout_rate_mean",
    "throughput_tasks_per_min_mean",
    "lost_load_rate_mean",
    "optimality_gap_vs_oracle_mean",
    "optimality_gap_vs_reference_mean",
    "performance_gap_vs_reference_mean",
    "runtime_ms_mean",
    "estimated_memory_mb_mean",
    "complexity_score_mean",
    "communication_messages_mean",
    "messages_per_robot_mean",
    "energy_proxy_wh_mean",
]

FIGURE_PREFERENCES = {
    "sp1": ["sp1_taxonomy_scope_family_ownership.png", "sp1_quality_resource_pareto.png", "sp1_best_method_by_scenario.png"],
    "sp2": ["sp2_performance_matrix.png", "sp2_quality_resource_pareto.png", "sp2_capacity_success_by_method.png"],
    "sp3": ["sp3_scalar_vs_wrench_success_by_method.png", "sp3_residual_wrench_by_method.png", "sp3_quality_resource_pareto.png"],
    "sp4": ["sp4_arrival_success_by_method.png", "sp4_time_energy_pareto.png", "sp4_communication_radius_degradation.png"],
    "sp5": ["sp5_transport_success_by_method.png", "sp5_final_pose_error_by_method.png", "sp5_quality_resource_pareto.png"],
    "sp6": ["sp6_recovery_success_by_method.png", "sp6_completion_vs_reassignment.png", "sp6_quality_resource_pareto.png"],
    "sp7": ["sp7_connectivity_vs_radius_by_method.png", "sp7_transport_success_under_network_stress.png", "sp7_relay_temporal_connectivity.png"],
    "sp8": ["sp8_runtime_scaling_loglog.png", "sp8_timeout_boundary.png", "sp8_wrench_success_by_scale.png", "sp8_quality_complexity_pareto.png"],
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    method_rows = collect_method_rows()
    hypothesis_rows = collect_hypothesis_registry()
    write_h0_registry_csv(hypothesis_rows, OUT_DIR / "H0_STATISTICAL_REGISTER_SP1_SP8.csv")
    build_method_catalog(method_rows, OUT_DIR / "METHODS_CATALOG_SP1_SP8.pdf")
    build_h0_catalog(hypothesis_rows, OUT_DIR / "H0_STATISTICAL_REGISTER_SP1_SP8.pdf")
    for sp in SP_INFO:
        build_sp_report(sp, method_rows, OUT_DIR / f"{sp.upper()}_pipeline_report.pdf")
    write_index()
    print(f"Generated PDFs in {OUT_DIR}")


def collect_method_rows() -> list[dict[str, str]]:
    collected: dict[tuple[str, str], dict[str, str]] = {}
    for sp in SP_INFO:
        for result_dir in result_dirs(sp):
            for csv_name in ["summary.csv", "performance_ranking.csv", "runs.csv"]:
                path = result_dir / "tables" / csv_name
                if not path.exists():
                    continue
                for row in read_csv(path):
                    method = clean(row.get("method", ""))
                    if not method:
                        continue
                    key = (sp, method)
                    if key not in collected:
                        collected[key] = {"sp": sp.upper(), **normalize_method_row(row)}
                    else:
                        collected[key].update({k: v for k, v in normalize_method_row(row).items() if v and not collected[key].get(k)})
    return sorted(collected.values(), key=lambda r: (r["sp"], r.get("method_ownership", ""), r.get("method_family", ""), r["method"]))


def collect_hypothesis_registry(sp_filter: str | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for sp in SP_INFO:
        if sp_filter and sp != sp_filter:
            continue
        for result_dir in result_dirs(sp):
            for row in read_csv(result_dir / "tables" / "hypothesis_results.csv"):
                hypothesis_id = first_nonempty(row.get("id"), row.get("hypothesis_id"))
                if not clean(hypothesis_id):
                    continue
                enriched = enrich_hypothesis_row(sp, result_dir.name, row)
                rows.append(enriched)
    return rows


def enrich_hypothesis_row(sp: str, experiment_id: str, row: dict[str, Any]) -> dict[str, str]:
    p_raw = first_nonempty(row.get("p_value_raw"), row.get("p_value"))
    p_adj = first_nonempty(row.get("p_value_holm"), row.get("p_value"))
    effect = format_number(row.get("effect", ""))
    ci_low = format_number(row.get("ci95_low", ""))
    ci_high = format_number(row.get("ci95_high", ""))
    ci = f"[{ci_low}, {ci_high}]" if ci_low and ci_high and ci_low.lower() != "nan" and ci_high.lower() != "nan" else ""
    reject = first_nonempty(row.get("reject_holm"), row.get("reject"), row.get("reject_raw"))
    decision = "Reject H0" if truthy(reject) else "Do not reject H0"
    if clean(row.get("status", "")) and clean(row.get("status", "")).lower() != "ok":
        decision = f"{decision}; status={clean(row.get('status'))}"
    return {
        "sp": sp.upper(),
        "experiment_id": experiment_id,
        "is_mc": "yes" if "_MC_" in experiment_id.upper() else "no",
        "id": clean(first_nonempty(row.get("id"), row.get("hypothesis_id"))),
        "metric": clean(row.get("metric", "")),
        "methods": clean(first_nonempty(row.get("methods"), paired_methods_label(row))),
        "test": clean(first_nonempty(row.get("test"), row.get("class", ""))),
        "n_pairs": format_number(first_nonempty(row.get("n_pairs"), row.get("n_blocks"))),
        "p_value_raw": format_number(p_raw),
        "p_value_adjusted": format_number(p_adj),
        "effect": effect,
        "effect_name": clean(row.get("effect_name", "")),
        "effect_size": format_number(row.get("effect_size", "")),
        "effect_size_name": clean(row.get("effect_size_name", "")),
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "alpha": format_number(row.get("alpha", "0.05")),
        "decision": decision,
        "h0": h0_statement(row),
        "h1": h1_statement(row),
        "effect_with_ci": f"{effect} {ci}".strip(),
    }


def h0_statement(row: dict[str, Any]) -> str:
    explicit = clean(row.get("null_hypothesis", ""))
    if explicit:
        return explicit
    metric = clean(row.get("metric", "metric"))
    methods = clean(row.get("methods", ""))
    test = clean(row.get("test", "")).lower()
    if "friedman" in test:
        return f"All compared methods have equal paired ranks/distributions for {metric} over matched blocks."
    if "one_sample" in test:
        return f"The sample/paired median difference from the configured threshold for {metric} is zero."
    if "wilcoxon" in test:
        if methods:
            return f"The paired median difference for {metric} between {methods} is zero."
        return f"The paired median difference for {metric} is zero."
    if "ttest" in test or "t_test" in test:
        return f"The mean tested margin or difference for {metric} is zero."
    return f"No statistically significant effect is present for {metric} under the emitted test."


def h1_statement(row: dict[str, Any]) -> str:
    explicit = clean(row.get("alternative", ""))
    if explicit:
        return explicit
    hid = clean(first_nonempty(row.get("id"), row.get("hypothesis_id")))
    metric = clean(row.get("metric", "metric"))
    claim = readable_hypothesis_id(hid)
    methods = clean(row.get("methods", ""))
    if claim:
        return f"{claim}."
    if methods:
        return f"A directional or distributional difference exists for {metric}: {methods}."
    return f"A non-zero effect exists for {metric}."


def paired_methods_label(row: dict[str, Any]) -> str:
    method_a = clean(row.get("method_a", ""))
    method_b = clean(row.get("method_b", ""))
    if method_a and method_b:
        return f"{method_a} vs {method_b}"
    return ""


def readable_hypothesis_id(hypothesis_id: str) -> str:
    text = clean(hypothesis_id)
    if not text:
        return ""
    patterns = [
        r"^H_DIAG_SP\d+_",
        r"^H_SP\d+_",
        r"^H\d+(?:[._]\d+)?_",
        r"^H\d+_DEBUG_",
        r"^H3_DEBUG_",
        r"^H4_DEBUG_",
        r"^H5_DEBUG_",
        r"^H6_DEBUG_",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:1].upper() + text[1:] if text else ""


def write_h0_registry_csv(rows: list[dict[str, str]], path: Path) -> None:
    columns = [
        "sp",
        "experiment_id",
        "is_mc",
        "id",
        "metric",
        "methods",
        "h0",
        "h1",
        "test",
        "n_pairs",
        "p_value_raw",
        "p_value_adjusted",
        "effect",
        "effect_name",
        "effect_size",
        "effect_size_name",
        "ci95_low",
        "ci95_high",
        "alpha",
        "decision",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_method_catalog(method_rows: list[dict[str, str]], path: Path) -> None:
    story = document_header(
        "Methods Catalog SP1-SP8",
        "Taxonomy, fairness controls, and method families used across the current AMR pipeline.",
    )
    story += [
        heading("Taxonomy Contract"),
        paragraph(
            "Every method is classified by ownership (baseline, proposed/ours, or reference), family "
            "(classic, SOTA, model-based, data-driven, or model-based reference), scope "
            "(centralized or decentralized), training/tuning type, execution model, and communication pattern. "
            "This prevents comparing a trained neural policy, an oracle, and a two-parameter distributed rule as if "
            "they had the same resource budget."
        ),
        bullet("reference/oracle methods are upper bounds or diagnostic baselines; they are not claimed as deployable controllers."),
        bullet("baseline methods are classic or SOTA comparators implemented with the same scenario seeds and metrics as proposed methods."),
        bullet("proposed/ours contains Smith-QR variants plus replicator, logit/Brown-style, primal-dual, tensor-field, Hamiltonian, and guarded wrench-market controllers where applicable."),
        bullet("data-driven entries report training type, parameters, episodes, seed splits, and decoder usage when those columns are available."),
        Spacer(1, 0.25 * cm),
    ]
    for sp in SP_INFO:
        rows = [r for r in method_rows if r["sp"].lower() == sp]
        story.append(heading(SP_INFO[sp]["title"]))
        if not rows:
            story.append(paragraph("No method rows found in current result tables."))
            continue
        story.append(method_table(rows, compact=True))
        story.append(Spacer(1, 0.2 * cm))
    build_pdf(path, story, landscape(A4))


def build_h0_catalog(hypothesis_rows: list[dict[str, str]], path: Path) -> None:
    story = document_header(
        "H0 Statistical Register SP1-SP8",
        "Null hypotheses, alternatives, Monte Carlo sample sizes, p-values, effects, confidence intervals, and decisions emitted by the current pipeline.",
    )
    story += [
        heading("Statistical Contract"),
        paragraph(
            "Each row is generated from `tables/hypothesis_results.csv`. Paired tests use matched Monte Carlo blocks "
            "(same scenario variant and seed where available). Multi-method tests use complete blocks across the listed methods. "
            "Holm-adjusted p-values are reported when the runner emitted them; otherwise the raw p-value is shown."
        ),
        bullet("H0 for paired Wilcoxon tests: paired median difference on the metric is zero between the listed methods."),
        bullet("H0 for Friedman tests: all compared methods have equal paired ranks/distributions on the metric."),
        bullet("H0 for one-sample Wilcoxon tests: the sample/paired metric difference from the configured threshold is zero."),
        Spacer(1, 0.25 * cm),
    ]
    for sp in SP_INFO:
        rows = [row for row in hypothesis_rows if row["sp"].lower() == sp]
        story.append(heading(SP_INFO[sp]["title"]))
        if rows:
            story.append(h0_table(rows, compact=True))
        else:
            story.append(paragraph("No statistical hypotheses were emitted for this SP."))
        story.append(Spacer(1, 0.2 * cm))
    build_pdf(path, story, landscape(A4))


def build_sp_report(sp: str, all_methods: list[dict[str, str]], path: Path) -> None:
    info = SP_INFO[sp]
    story = document_header(info["title"], info["question"])
    story += [
        heading("Methodological Scope"),
        paragraph(info["model"]),
        paragraph(
            "The report is generated from versioned configs and existing result artifacts. Tables therefore reflect the current pipeline state, "
            "not a hand-edited narrative. Missing cells mean the corresponding metric was not emitted by that SP runner."
        ),
        heading("Experiment Configs"),
        config_table(sp),
        heading("Method Taxonomy"),
    ]
    methods = [r for r in all_methods if r["sp"].lower() == sp]
    story.append(method_table(methods, compact=False) if methods else paragraph("No methods found in result tables."))
    story += [
        heading("Scenarios and Result Sets"),
        result_set_table(sp),
        heading("Performance Ranking"),
        ranking_table(sp),
        heading("Theory and Statistical Audit"),
        audit_table(sp),
        heading("Monte Carlo H0 / H1 Hypotheses"),
        h0_table(collect_hypothesis_registry(sp), compact=False),
        heading("Figures and Videos"),
        artifact_table(sp),
    ]
    for fig_path in selected_figures(sp):
        story.extend([Spacer(1, 0.15 * cm), figure_block(fig_path)])
    build_pdf(path, story, landscape(A4))


def document_header(title: str, subtitle: str) -> list[Any]:
    return [
        Paragraph(escape(title), STYLES["Title"]),
        Paragraph(escape(subtitle), STYLES["Subtitle"]),
        Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Source: configs/experiments and results/sp1..sp7", STYLES["Small"]),
        Spacer(1, 0.35 * cm),
    ]


def config_table(sp: str) -> Table:
    rows = [["Config", "Experiment ID", "Declared output", "Key settings observed"]]
    for path in sorted((CONFIG_ROOT / sp).glob("*.yaml")):
        text = path.read_text(encoding="utf-8", errors="replace")
        rows.append(
            [
                path.name,
                first_yaml_value(text, "experiment_id") or path.stem,
                first_yaml_value(text, "output_dir") or "",
                summarize_config_text(text),
            ]
        )
    if len(rows) == 1:
        rows.append(["-", "-", "-", "No config files found."])
    return make_table(rows, [4.3 * cm, 4.0 * cm, 5.0 * cm, 5.0 * cm], font_size=6.5)


def result_set_table(sp: str) -> Table:
    rows = [["Result set", "Runs", "Scenarios", "Methods", "Figures", "Videos", "Theory failures"]]
    for result_dir in result_dirs(sp):
        runs = read_csv(result_dir / "tables" / "runs.csv")
        summary = read_csv(result_dir / "tables" / "summary.csv")
        source = runs or summary
        scenarios = sorted({clean(r.get("scenario_generator", "")) for r in source if clean(r.get("scenario_generator", ""))})
        methods = sorted({clean(r.get("method", "")) for r in source if clean(r.get("method", ""))})
        audit = read_json(result_dir / "theory_audit.json")
        rows.append(
            [
                result_dir.name,
                str(len(runs) if runs else sum(int(float(r.get("n", 0) or 0)) for r in summary)),
                str(len(scenarios)),
                str(len(methods)),
                str(count_files(result_dir / "figures", "*.png")),
                str(count_files(result_dir / "videos", "*.mp4")),
                str(audit.get("failed_checks", "n/a") if isinstance(audit, dict) else "n/a"),
            ]
        )
    if len(rows) == 1:
        rows.append(["-", "0", "0", "0", "0", "0", "n/a"])
    return make_table(rows, [5.0 * cm, 1.5 * cm, 1.8 * cm, 1.8 * cm, 1.6 * cm, 1.6 * cm, 2.3 * cm], font_size=7)


def ranking_table(sp: str) -> Table:
    rows = [["Result set", "Rank", "Method", "Owner", "Family", "Scope"]]
    metric_columns: list[str] = []
    rankings = []
    for result_dir in result_dirs(sp):
        ranking = read_csv(result_dir / "tables" / "performance_ranking.csv")
        if not ranking:
            continue
        overall = [r for r in ranking if clean(r.get("scenario_generator", "")).upper() in {"ALL_SCENARIOS", "OVERALL"}]
        selected = (overall or ranking)[:8]
        rankings.extend((result_dir.name, r) for r in selected)
        for col in PREFERRED_METRICS:
            if col in selected[0] and col not in metric_columns:
                metric_columns.append(col)
            if len(metric_columns) >= 4:
                break
    rows[0].extend(short_metric(c) for c in metric_columns)
    for result_name, row in rankings:
        values = [
            result_name,
            clean(row.get("rank", "")),
            clean(row.get("method", "")),
            owner_label(row.get("method_ownership", "")),
            family_label(row.get("method_family", "")),
            scope_label(row.get("method_scope", "")),
        ]
        values.extend(format_number(row.get(c, "")) for c in metric_columns)
        rows.append(values)
    if len(rows) == 1:
        rows.append(["-", "-", "-", "-", "-", "-"] + ["-" for _ in metric_columns])
    widths = [3.4 * cm, 1.0 * cm, 4.0 * cm, 1.6 * cm, 2.0 * cm, 1.8 * cm] + [2.0 * cm for _ in metric_columns]
    return make_table(rows, widths, font_size=6.2)


def audit_table(sp: str) -> Table:
    rows = [["Result set", "Theory status", "Hypothesis rows", "Notes"]]
    for result_dir in result_dirs(sp):
        audit = read_json(result_dir / "theory_audit.json")
        failed = audit.get("failed_checks", "n/a") if isinstance(audit, dict) else "n/a"
        status = "PASS" if str(failed) == "0" else f"CHECK failed={failed}"
        hyp_rows = len(read_csv(result_dir / "tables" / "hypothesis_results.csv"))
        notes = []
        if isinstance(audit, dict):
            if audit.get("warnings"):
                notes.append(f"warnings={len(audit.get('warnings', []))}")
            if audit.get("checks"):
                checks = audit.get("checks", [])
                notes.append(f"checks={len(checks) if isinstance(checks, list) else checks}")
        rows.append([result_dir.name, status, str(hyp_rows), ", ".join(notes) or "No extra audit notes emitted."])
    if len(rows) == 1:
        rows.append(["-", "n/a", "0", "No result dirs found."])
    return make_table(rows, [5.0 * cm, 3.0 * cm, 2.6 * cm, 6.5 * cm], font_size=7)


def h0_table(rows: list[dict[str, str]], compact: bool) -> Table:
    if not rows:
        return make_table([["Experiment", "H0", "Decision"], ["-", "No hypothesis_results.csv rows found.", "-"]], [4.0 * cm, 14.0 * cm, 3.0 * cm], font_size=7)
    if compact:
        table_rows = [["SP", "Experiment", "MC", "ID", "H0", "H1 / claim", "Test", "n", "p adj", "Effect", "Decision"]]
        for row in rows:
            table_rows.append(
                [
                    row["sp"],
                    row["experiment_id"],
                    row["is_mc"],
                    row["id"],
                    row["h0"],
                    row["h1"],
                    row["test"],
                    row["n_pairs"],
                    row["p_value_adjusted"],
                    row["effect"],
                    row["decision"],
                ]
            )
        return make_table(table_rows, [0.9 * cm, 3.0 * cm, 0.8 * cm, 3.2 * cm, 5.5 * cm, 4.5 * cm, 2.5 * cm, 1.0 * cm, 1.2 * cm, 1.2 * cm, 1.4 * cm], font_size=4.8)
    table_rows = [["Experiment", "MC", "Hypothesis ID", "H0", "H1 / claim", "Test", "n", "p raw", "p Holm", "Effect [CI95]", "Decision"]]
    for row in rows:
        table_rows.append(
            [
                row["experiment_id"],
                row["is_mc"],
                row["id"],
                row["h0"],
                row["h1"],
                row["test"],
                row["n_pairs"],
                row["p_value_raw"],
                row["p_value_adjusted"],
                row["effect_with_ci"],
                row["decision"],
            ]
        )
    return make_table(table_rows, [3.2 * cm, 0.9 * cm, 3.8 * cm, 6.4 * cm, 5.0 * cm, 2.3 * cm, 0.9 * cm, 1.1 * cm, 1.1 * cm, 2.5 * cm, 1.3 * cm], font_size=4.9)


def artifact_table(sp: str) -> Table:
    rows = [["Result set", "Primary figures", "Video catalog"]]
    for result_dir in result_dirs(sp):
        figures = [p.name for p in sorted((result_dir / "figures").glob("*.png"))[:8]] if (result_dir / "figures").exists() else []
        video_index = result_dir / "videos" / "VIDEO_INDEX.md"
        catalog = result_dir / "tables" / "video_catalog.csv"
        video_text = []
        if video_index.exists():
            video_text.append(relative(video_index))
        if catalog.exists():
            video_text.append(f"{relative(catalog)} ({max(0, len(read_csv(catalog)))} rows)")
        if not video_text:
            mp4_count = count_files(result_dir / "videos", "*.mp4")
            video_text.append(f"{mp4_count} mp4 files")
        rows.append([result_dir.name, "\n".join(figures) or "No figures", "\n".join(video_text)])
    if len(rows) == 1:
        rows.append(["-", "No figures", "No videos"])
    return make_table(rows, [4.5 * cm, 6.2 * cm, 6.0 * cm], font_size=6.4)


def method_table(rows: list[dict[str, str]], compact: bool) -> Table:
    if compact:
        headers = ["SP", "Method", "Owner", "Family", "Scope", "Training/Tuning", "Exec/Comm"]
        data = [headers]
        for row in rows:
            data.append(
                [
                    row.get("sp", ""),
                    row.get("method_label") or row.get("method", ""),
                    owner_label(row.get("method_ownership", "")),
                    family_label(row.get("method_family", "")),
                    scope_label(row.get("method_scope", "")),
                    row.get("method_training_type", ""),
                    join_nonempty(row.get("method_execution_model", ""), row.get("method_communication_pattern", ""), sep=" / "),
                ]
            )
        return make_table(data, [1.0 * cm, 5.0 * cm, 1.6 * cm, 2.2 * cm, 2.0 * cm, 4.0 * cm, 5.0 * cm], font_size=5.8)
    headers = ["Method", "Label", "Owner", "Family", "Scope", "Variant", "Training/Tuning"]
    data = [headers]
    for row in rows:
        data.append(
            [
                row.get("method", ""),
                row.get("method_label", ""),
                owner_label(row.get("method_ownership", "")),
                family_label(row.get("method_family", "")),
                scope_label(row.get("method_scope", "")),
                row.get("method_variant", ""),
                row.get("method_training_type", ""),
            ]
        )
    return make_table(data, [3.4 * cm, 3.8 * cm, 1.5 * cm, 2.0 * cm, 1.8 * cm, 3.2 * cm, 3.0 * cm], font_size=6.2)


def selected_figures(sp: str) -> list[Path]:
    candidates: list[Path] = []
    for result_dir in reversed(result_dirs(sp)):
        fig_dir = result_dir / "figures"
        if not fig_dir.exists():
            continue
        for preferred in FIGURE_PREFERENCES.get(sp, []):
            fig = fig_dir / preferred
            if fig.exists() and fig not in candidates:
                candidates.append(fig)
        if len(candidates) >= 2:
            return candidates[:2]
    return candidates[:2]


def figure_block(path: Path) -> Any:
    caption = Paragraph(f"Figure: {escape(relative(path))}", STYLES["Small"])
    image = Image(str(path))
    max_width = 16.5 * cm
    max_height = 10.0 * cm
    scale = min(max_width / image.drawWidth, max_height / image.drawHeight, 1.0)
    image.drawWidth *= scale
    image.drawHeight *= scale
    return Table([[image], [caption]], colWidths=[max_width], style=[("ALIGN", (0, 0), (-1, -1), "CENTER")])


def build_pdf(path: Path, story: list[Any], pagesize: tuple[float, float]) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=pagesize,
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.3 * cm,
        bottomMargin=1.2 * cm,
        title=path.stem,
        author="VIU-MRBO-TFM-2026 pipeline",
    )
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)


def page_footer(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawString(doc.leftMargin, 0.55 * cm, "VIU-MRBO-TFM-2026 methodology artifact")
    canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 0.55 * cm, f"Page {doc.page}")
    canvas.restoreState()


def make_table(rows: list[list[Any]], widths: list[float], font_size: float = 7.0) -> Table:
    wrapped = [[cell(c, font_size) for c in row] for row in rows]
    table = Table(wrapped, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def cell(value: Any, font_size: float) -> Paragraph:
    style = ParagraphStyle("table_cell", parent=STYLES["Small"], fontSize=font_size, leading=font_size + 1.5)
    return Paragraph(escape(str(value)), style)


def heading(text: str) -> Paragraph:
    return Paragraph(escape(text), STYLES["Heading"])


def paragraph(text: str) -> Paragraph:
    return Paragraph(escape(text), STYLES["Body"])


def bullet(text: str) -> Paragraph:
    return Paragraph(f"- {escape(text)}", STYLES["Body"])


def escape(text: str) -> str:
    return html.escape(str(text)).replace("\n", "<br/>")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {}


def result_dirs(sp: str) -> list[Path]:
    root = RESULTS_ROOT / sp
    if not root.exists():
        return []
    return sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name)


def count_files(path: Path, pattern: str) -> int:
    return len(list(path.glob(pattern))) if path.exists() else 0


def normalize_method_row(row: dict[str, Any]) -> dict[str, str]:
    output = {}
    for key in METHOD_FIELD_ORDER:
        if key == "sp":
            continue
        output[key] = clean(row.get(key, ""))
    if not output.get("method_label"):
        output["method_label"] = output.get("method", "")
    return output


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def first_nonempty(*values: Any) -> str:
    for value in values:
        text = clean(value)
        if text and text.lower() != "nan":
            return text
    return ""


def truthy(value: Any) -> bool:
    text = clean(value).lower()
    return text in {"true", "1", "yes", "y", "reject", "rejected"}


def first_yaml_value(text: str, key: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", text)
    return match.group(1).strip().strip('"').strip("'") if match else ""


def summarize_config_text(text: str) -> str:
    keys = ["mode", "n_seeds", "seeds", "methods", "scenarios", "scenario_generators", "monte_carlo", "video", "artifacts"]
    found = []
    for key in keys:
        value = first_yaml_value(text, key)
        if value:
            found.append(f"{key}: {value}")
    if not found:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                found.append(stripped)
            if len(found) >= 5:
                break
    return "; ".join(found[:6])


def short_metric(col: str) -> str:
    return col.replace("_mean", "").replace("_", " ")


def format_number(value: Any) -> str:
    text = clean(value)
    if not text:
        return ""
    try:
        number = float(text)
    except ValueError:
        return text
    if not math.isfinite(number):
        return text
    if abs(number) >= 1000:
        return f"{number:.1f}"
    if abs(number) >= 10:
        return f"{number:.2f}"
    return f"{number:.3f}"


def owner_label(value: Any) -> str:
    text = clean(value)
    return {"proposed": "ours", "baseline": "baseline", "reference": "reference"}.get(text, text)


def family_label(value: Any) -> str:
    return clean(value).replace("_", "-")


def scope_label(value: Any) -> str:
    return clean(value).replace("_", "-")


def join_nonempty(*values: str, sep: str) -> str:
    return sep.join([v for v in values if v])


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def write_index() -> None:
    lines = [
        "# Pipeline PDF Index",
        "",
        "Generated from current configs and results artifacts.",
        "",
        "- METHODS_CATALOG_SP1_SP8.pdf",
        "- H0_STATISTICAL_REGISTER_SP1_SP8.pdf",
        "- H0_STATISTICAL_REGISTER_SP1_SP8.csv",
    ]
    for sp in SP_INFO:
        lines.append(f"- {sp.upper()}_pipeline_report.pdf")
    (OUT_DIR / "PDF_INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


BASE_STYLES = getSampleStyleSheet()
STYLES = {
    "Title": ParagraphStyle(
        "CustomTitle",
        parent=BASE_STYLES["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8,
    ),
    "Subtitle": ParagraphStyle(
        "CustomSubtitle",
        parent=BASE_STYLES["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8,
    ),
    "Heading": ParagraphStyle(
        "CustomHeading",
        parent=BASE_STYLES["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=8,
        spaceAfter=5,
    ),
    "Body": ParagraphStyle(
        "CustomBody",
        parent=BASE_STYLES["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#111827"),
        spaceAfter=5,
    ),
    "Small": ParagraphStyle(
        "CustomSmall",
        parent=BASE_STYLES["BodyText"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#334155"),
    ),
}


if __name__ == "__main__":
    main()

"""Run a small treatment matrix and export CSV/JSON plus an extended report."""

from __future__ import annotations

import argparse
import csv
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.config.schema import ExperimentConfig
from viu_mrob_tfm.controllers.nominal_consensus import NominalConsensusController
from viu_mrob_tfm.experiments.runner import _compute_summary_metrics
from viu_mrob_tfm.simulations import SimulationScenario, Simulator
from viu_mrob_tfm.utils.io import ensure_directory, load_yaml, save_json


DEFAULT_TREATMENTS = [
    "t1_greedy",
    "t2_dac_greedy",
    "t3_replicator",
    "t4_smith",
    "t5_centralized",
    "t6_single_clock",
]

METRIC_COLUMNS = [
    "completed_tasks",
    "task_count",
    "completion_rate",
    "ever_feasible_tasks",
    "ever_feasible_rate",
    "time_feasible_rate",
    "mean_coalition_time_s",
    "mean_completion_time_s",
    "throughput_tasks_per_min",
    "assignment_change_rate",
    "total_distance_m",
    "control_effort",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        action="append",
        required=True,
        help="Experiment config YAML. Pass multiple times for a matrix.",
    )
    parser.add_argument(
        "--treatment",
        action="append",
        default=None,
        help="Treatment to run. Defaults to T1-T5.",
    )
    parser.add_argument(
        "--batch-name",
        default="smoke-ab-t1-t6",
        help="Name for results/batch/<batch-name>.",
    )
    parser.add_argument(
        "--results-root",
        default="results/batch",
        help="Root directory for machine-readable batch outputs.",
    )
    parser.add_argument(
        "--docs-root",
        default="docs/doc-02-mid-report/extended-results",
        help="Directory for extended documentation outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    treatments = args.treatment or DEFAULT_TREATMENTS
    results_dir = ensure_directory(Path(args.results_root) / args.batch_name)
    docs_dir = ensure_directory(Path(args.docs_root) / args.batch_name)

    rows: list[dict[str, Any]] = []
    for config_path in [Path(item) for item in args.config]:
        rows.extend(run_config_matrix(config_path, treatments, results_dir))

    csv_path = write_csv(results_dir / "batch_results.csv", rows)
    json_path = save_json(results_dir / "batch_results.json", {"rows": rows})
    docs_csv = write_csv(docs_dir / "batch_results.csv", rows)
    report_path = write_report(docs_dir / "README.md", rows, args.batch_name)

    print(f"Batch rows: {len(rows)}")
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")
    print(f"Docs CSV: {docs_csv}")
    print(f"Docs report: {report_path}")
    return 0


def run_config_matrix(
    config_path: Path,
    treatments: list[str],
    results_dir: Path,
) -> list[dict[str, Any]]:
    base_data = load_yaml(config_path)
    rows: list[dict[str, Any]] = []
    for treatment in treatments:
        data = deepcopy(base_data)
        data.setdefault("controller", {})
        data["controller"]["type"] = treatment
        config = ExperimentConfig.from_dict(data)
        scenario = SimulationScenario.from_config(config)
        controller = NominalConsensusController(graph=scenario.graph)
        controller.treatment = treatment
        controller.parameters = dict(config.controller.parameters)
        results = Simulator(scenario=scenario, controller=controller).run()
        metrics = _compute_summary_metrics(results)

        run_name = f"{config.name}__{treatment}"
        output_dir = ensure_directory(results_dir / run_name)
        arrays = {key: value for key, value in results.items() if isinstance(value, np.ndarray)}
        np.savez_compressed(output_dir / "results.npz", **arrays)
        summary = {
            "experiment": config.name,
            "config": str(config_path),
            "treatment": treatment,
            "output_dir": str(output_dir),
            "metrics": metrics,
        }
        save_json(output_dir / "summary.json", summary)

        row = {
            "scenario": config.name,
            "config": str(config_path),
            "treatment": treatment,
            **metrics,
        }
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    ensure_directory(path.parent)
    fieldnames = ["scenario", "config", "treatment", *METRIC_COLUMNS]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def write_report(path: Path, rows: list[dict[str, Any]], batch_name: str) -> Path:
    ensure_directory(path.parent)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Extended Results: {batch_name}",
        "",
        f"Generated: {now}",
        "",
        "This document is an extended result artifact for the mid-report. It does not replace the submitted mid-report PDF; it records a reproducible treatment matrix used to validate the Python simulator.",
        "",
        "## Summary Table",
        "",
        "| Scenario | Treatment | Completed | Ever feasible | T coal (s) | T delivery (s) | Throughput | Changes | Distance |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {scenario} | {treatment} | {completed_tasks}/{task_count} | {ever_feasible_tasks}/{task_count} | {coal} | {delivery} | {throughput:.2f} | {changes:.4f} | {distance:.2f} |".format(
                scenario=row["scenario"],
                treatment=row["treatment"],
                completed_tasks=row["completed_tasks"],
                task_count=row["task_count"],
                ever_feasible_tasks=row["ever_feasible_tasks"],
                coal=_fmt(row["mean_coalition_time_s"]),
                delivery=_fmt(row["mean_completion_time_s"]),
                throughput=row["throughput_tasks_per_min"],
                changes=row["assignment_change_rate"],
                distance=row["total_distance_m"],
            )
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- `completion_rate` measures delivered tasks.",
            "- `ever_feasible_rate` measures whether each task formed a sufficient coalition at least once.",
            "- `time_feasible_rate` measures the fraction of all task-time samples that were feasible; this is expected to be lower because it includes recruitment and post-delivery periods.",
            "- `t6_single_clock` is the adaptive-price Smith extension. In these smoke scenarios it validates integration, not final superiority.",
            "- These are smoke results. They verify the pipeline and expose calibration needs; they are not the final experimental campaign.",
            "",
            "Machine-readable copy: `batch_results.csv`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _fmt(value: Any) -> str:
    if value is None:
        return "nan"
    try:
        if np.isnan(float(value)):
            return "nan"
    except (TypeError, ValueError):
        return str(value)
    return f"{float(value):.2f}"


if __name__ == "__main__":
    raise SystemExit(main())

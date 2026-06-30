"""Generate benchmark v2 figures from ``summary.csv``."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")


def generate_figures(summary_csv: str | Path, output_dir: str | Path) -> list[Path]:
    rows = _read_rows(Path(summary_csv))
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    figures = [
        _fig_throughput_vs_rho(rows, output / "fig_throughput_vs_rho.png"),
        _fig_recovery(rows, output / "fig_recovery.png"),
        _fig_comm_degradation(rows, output / "fig_comm_degradation.png"),
        _fig_pareto(rows, output / "fig_pareto.png"),
        _fig_theory_validation(Path(summary_csv).parent, output / "fig_theory_validation.png"),
        _fig_ablation(rows, output / "fig_ablation.png"),
    ]
    return figures


def _read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _fig_throughput_vs_rho(rows: list[dict[str, Any]], path: Path) -> Path:
    data = [row for row in rows if row["scenario"] == "load_sweep"]
    figure, axes = plt.subplots(1, 2, figsize=(13, 5))
    for metric, axis, ylabel in [
        ("throughput_steady", axes[0], "Throughput steady [deliveries/min]"),
        ("reward_capture_ratio", axes[1], "Reward capture"),
    ]:
        grouped = _group(data, ["method", "label", "rho"], metric)
        for (method, label), rho_values in _by_method(grouped).items():
            rhos = sorted(rho_values)
            means = [np.mean(rho_values[rho]) for rho in rhos]
            lows = [np.quantile(rho_values[rho], 0.025) for rho in rhos]
            highs = [np.quantile(rho_values[rho], 0.975) for rho in rhos]
            axis.plot(rhos, means, marker="o", label=label if metric == "throughput_steady" else None)
            axis.fill_between(rhos, lows, highs, alpha=0.12)
            if method == "smith_full" and metric == "throughput_steady":
                axis.plot(rhos, np.minimum(rhos, 1.0) * max(means + [1.0]), "k--", alpha=0.35, label="water-filling cap")
        axis.set_xlabel("rho")
        axis.set_ylabel(ylabel)
        axis.grid(True, alpha=0.3)
    axes[0].legend(fontsize=7, ncol=2)
    figure.suptitle("Throughput and reward capture vs load factor")
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)
    return path


def _fig_recovery(rows: list[dict[str, Any]], path: Path) -> Path:
    data = [row for row in rows if row["scenario"] == "robot_failures"]
    grouped = _group(data, ["label"], "recovery_time_s")
    labels = list(grouped)
    values = [np.nanmean(grouped[label]) for label in labels]
    figure, axis = plt.subplots(figsize=(11, 5))
    axis.bar(np.arange(len(labels)), values, color="#2563eb")
    axis.set_xticks(np.arange(len(labels)))
    axis.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    axis.set_ylabel("Recovery time [s]")
    axis.set_title("Recovery after 4 robot failures")
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)
    return path


def _fig_comm_degradation(rows: list[dict[str, Any]], path: Path) -> Path:
    data = [row for row in rows if row["scenario"] == "comm_degradation"]
    figure, axis = plt.subplots(figsize=(11, 5))
    local = [row for row in data if row["info_requirement"] == "local"]
    global_rows = [row for row in data if row["info_requirement"] == "global"]
    grouped = _group(local, ["label", "scenario_case"], "reward_capture_ratio")
    by_label: dict[str, dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (label, case), values in grouped.items():
        r_com = _case_r(case)
        by_label[label][r_com].extend(values)
    for label, values_by_r in by_label.items():
        xs = sorted(values_by_r)
        ys = [np.mean(values_by_r[x]) for x in xs]
        axis.plot(xs, ys, marker="o", label=label)
    if global_rows:
        global_mean = np.nanmean([_f(row["reward_capture_ratio"]) for row in global_rows])
        axis.axhline(global_mean, color="black", linestyle="--", label="global-info methods")
    axis.set_xlabel("R_com [m]")
    axis.set_ylabel("Reward capture")
    axis.set_title("Communication degradation")
    axis.grid(True, alpha=0.3)
    axis.legend(fontsize=7, ncol=2)
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)
    return path


def _fig_pareto(rows: list[dict[str, Any]], path: Path) -> Path:
    figure, axes = plt.subplots(1, 2, figsize=(13, 5))
    for row in rows:
        label = row["label"]
        axes[0].scatter(_f(row["mean_completion_time"]), _f(row["switches_per_delivery"]), s=16, alpha=0.35, label=label)
        axes[1].scatter(_f(row["total_robot_distance"]), _f(row["reward_capture_ratio"]), s=16, alpha=0.35)
    axes[0].set_xlabel("Mean completion time [s]")
    axes[0].set_ylabel("Switches / delivery")
    axes[1].set_xlabel("Total robot distance [m]")
    axes[1].set_ylabel("Reward capture")
    for axis in axes:
        axis.grid(True, alpha=0.3)
    handles, labels = axes[0].get_legend_handles_labels()
    dedup = dict(zip(labels, handles))
    axes[0].legend(dedup.values(), dedup.keys(), fontsize=7, ncol=2)
    figure.suptitle("Pareto diagnostics")
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)
    return path


def _fig_theory_validation(root: Path, path: Path) -> Path:
    theory_files = list(root.glob("*/*smith*_theory.csv"))
    figure, axis = plt.subplots(figsize=(6, 6))
    plotted = False
    for file in theory_files[:120]:
        rows = _read_rows(file)
        if not rows:
            continue
        observed = np.array([_f(row["z_observed"]) for row in rows], dtype=float)
        theory = np.array([_f(row["z_theory"]) for row in rows], dtype=float)
        if observed.size:
            axis.scatter(theory, observed, s=4, alpha=0.08)
            plotted = True
    if plotted:
        lim = axis.get_xlim()[1]
        axis.plot([0, lim], [0, lim], "k--", linewidth=1)
    axis.set_xlabel("z* theoretical")
    axis.set_ylabel("z observed")
    axis.set_title("Smith theory validation")
    axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)
    return path


def _fig_ablation(rows: list[dict[str, Any]], path: Path) -> Path:
    ablations = {"smith_full", "smith_no_prices", "smith_no_integer", "smith_raw_occupancy"}
    data = [row for row in rows if row["method"] in ablations]
    grouped = _group(data, ["scenario", "label"], "reward_capture_ratio")
    scenarios = sorted({row["scenario"] for row in data})
    labels = sorted({row["label"] for row in data})
    x = np.arange(len(scenarios))
    width = 0.18
    figure, axis = plt.subplots(figsize=(12, 5))
    for idx, label in enumerate(labels):
        values = [np.nanmean(grouped.get((scenario, label), [np.nan])) for scenario in scenarios]
        axis.bar(x + (idx - 1.5) * width, values, width=width, label=label)
    axis.set_xticks(x)
    axis.set_xticklabels(scenarios, rotation=25, ha="right")
    axis.set_ylabel("Reward capture")
    axis.set_title("Smith ablations")
    axis.grid(axis="y", alpha=0.3)
    axis.legend(fontsize=8)
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)
    return path


def _group(rows: list[dict[str, Any]], keys: list[str], metric: str) -> dict[Any, list[float]]:
    grouped: dict[Any, list[float]] = defaultdict(list)
    for row in rows:
        key_values = tuple(row[key] for key in keys)
        key: Any = key_values[0] if len(key_values) == 1 else key_values
        value = _f(row.get(metric))
        if math.isfinite(value):
            grouped[key].append(value)
    return grouped


def _by_method(grouped: dict[tuple[str, str, str], list[float]]) -> dict[tuple[str, str], dict[float, list[float]]]:
    output: dict[tuple[str, str], dict[float, list[float]]] = defaultdict(dict)
    for (method, label, rho), values in grouped.items():
        output[(method, label)][float(rho)] = values
    return output


def _case_r(case: str) -> float:
    try:
        return float(case.split("_", maxsplit=1)[0].removeprefix("R"))
    except ValueError:
        return math.nan


def _f(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary_csv", type=Path)
    parser.add_argument("--out", type=Path, default=Path("figures"))
    args = parser.parse_args()
    for figure in generate_figures(args.summary_csv, args.out):
        print(figure)

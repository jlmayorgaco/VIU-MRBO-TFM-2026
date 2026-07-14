"""SP0 compact plots for smoke and campaign reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def plot_method_quality(rows: list[dict[str, Any]], path: Path) -> None:
    grouped = _group(rows, "method")
    methods = sorted(grouped)
    success = [_mean(grouped[method], "success") for method in methods]
    regret = [_mean(grouped[method], "normalized_regret") for method in methods]
    fig, axes = plt.subplots(1, 2, figsize=(max(8.0, 0.55 * len(methods)), 4.2))
    x = np.arange(len(methods))
    axes[0].bar(x, success, color="#2a9d8f")
    axes[0].set_ylim(0.0, 1.05)
    axes[0].set_ylabel("Success")
    axes[0].set_title("SP0 max-cardinality success")
    axes[1].bar(x, regret, color="#9b5de5")
    axes[1].set_ylabel("Normalized regret")
    axes[1].set_title("SP0 normalized regret")
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels([_short(method) for method in methods], rotation=35, ha="right", fontsize=8)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_dynamic_fitness_heatmap(rows: list[dict[str, Any]], path: Path, *, metric: str = "normalized_regret") -> None:
    selected = [row for row in rows if row.get("dynamic_id") and row.get("fitness_id")]
    if not selected:
        _blank(path, "No dynamic-fitness rows")
        return
    dynamics = sorted({str(row["dynamic_id"]) for row in selected})
    fitness = sorted({str(row["fitness_id"]) for row in selected})
    matrix = np.full((len(dynamics), len(fitness)), np.nan, dtype=float)
    for i, dynamic in enumerate(dynamics):
        for j, fit in enumerate(fitness):
            matrix[i, j] = _mean([row for row in selected if row["dynamic_id"] == dynamic and row["fitness_id"] == fit], metric)
    fig, ax = plt.subplots(figsize=(max(6.0, 0.65 * len(fitness)), max(4.8, 0.42 * len(dynamics))))
    image = ax.imshow(matrix, cmap="viridis_r" if metric != "success" else "viridis", aspect="auto")
    ax.set_xticks(np.arange(len(fitness)))
    ax.set_xticklabels(fitness)
    ax.set_yticks(np.arange(len(dynamics)))
    ax.set_yticklabels(dynamics)
    ax.set_title(f"SP0 dynamic x fitness: {metric}")
    fig.colorbar(image, ax=ax, shrink=0.82)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_quality_communication_pareto(rows: list[dict[str, Any]], path: Path) -> None:
    _plot_pareto(rows, path, x_key="bytes", y_key="normalized_regret", title="SP0 quality-communication Pareto", xlabel="Bytes")


def plot_quality_runtime_pareto(rows: list[dict[str, Any]], path: Path) -> None:
    _plot_pareto(rows, path, x_key="runtime_wall_s", y_key="normalized_regret", title="SP0 quality-runtime Pareto", xlabel="Runtime [s]")


def plot_scalability(rows: list[dict[str, Any]], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    for method, selected in _group(rows, "method").items():
        by_n = _group(selected, "N")
        xs = sorted(int(value) for value in by_n)
        ys = [_mean(by_n[str(x)] if str(x) in by_n else by_n[x], "runtime_wall_s") for x in xs]
        if xs:
            ax.plot(xs, ys, marker="o", linewidth=1.6, label=_short(method))
    ax.set_xlabel("N")
    ax.set_ylabel("Runtime [ms]")
    ax.set_title("SP0 runtime scaling")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_pareto(rows: list[dict[str, Any]], path: Path, *, x_key: str, y_key: str, title: str, xlabel: str) -> None:
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    for method, selected in _group(rows, "method").items():
        x = _mean(selected, x_key)
        y = _mean(selected, y_key)
        ax.scatter(max(x, 1.0e-9), y, s=72, edgecolors="black", linewidths=0.45)
        ax.annotate(_short(method), (max(x, 1.0e-9), y), xytext=(4, 3), textcoords="offset points", fontsize=8)
    ax.set_xscale("log")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Normalized regret")
    ax.set_title(title)
    ax.grid(alpha=0.25, which="both")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _blank(path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    ax.text(0.5, 0.5, title, ha="center", va="center")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _group(rows: list[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
    grouped: dict[Any, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row.get(key, ""), []).append(row)
    return grouped


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    values = []
    for row in rows:
        value = row.get(key, np.nan)
        if isinstance(value, bool):
            value = 1.0 if value else 0.0
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            pass
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    return float(np.mean(array)) if array.size else np.nan


def _short(method: str) -> str:
    return {
        "HUN": "HUN",
        "GRD": "GRD",
        "DA": "DA",
        "REP": "REP",
        "SMI": "SMI",
        "BNN": "BNN",
        "LOG": "LOG",
        "PROJ": "PROJ",
        "HYB": "HYB",
        "IPPO-GNN": "IPPO",
        "MAPPO-GNN": "MAPPO",
    }.get(str(method), str(method).replace("_", "\n"))

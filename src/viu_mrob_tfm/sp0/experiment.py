"""Reproducible SP0 campaign, post-processing and paper figures."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import asdict
from math import factorial, sqrt
from pathlib import Path
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import yaml
from scipy.stats import binomtest

from .theory import (
    AllocationResult,
    auction_assignment,
    enumerate_pure_nash,
    greedy_assignment,
    hungarian_assignment,
    marginal_payoff,
    pairwise_exchange,
    potential_best_response,
    profile_metrics,
)


METHOD_LABELS = {
    "hungarian": "Hungarian (oráculo)",
    "auction_eps": r"Subasta $\varepsilon$",
    "greedy": "Greedy",
    "potential_br": "Mejor respuesta",
    "potential_exchange": "Mejor respuesta + 2-intercambio",
    "no_exclusion": "Ablación sin exclusión",
}


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    required = {
        "experiment_id",
        "output_dir",
        "seed_base",
        "number_seeds",
        "fleet_sizes",
        "task_ratios",
    }
    missing = required.difference(config)
    if missing:
        raise ValueError(f"missing configuration keys: {sorted(missing)}")
    return config


def generate_geometric_instance(
    n_robots: int, n_tasks: int, seed: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return paired positions and normalized Euclidean assignment costs."""

    rng = np.random.default_rng(seed)
    robot_positions = rng.uniform(0.0, 1.0, size=(n_robots, 2))
    task_positions = rng.uniform(0.0, 1.0, size=(n_tasks, 2))
    costs = (
        np.linalg.norm(robot_positions[:, None, :] - task_positions[None, :, :], axis=2)
        / sqrt(2.0)
    )
    return robot_positions, task_positions, costs


def generate_geometric_costs(n_robots: int, n_tasks: int, seed: int) -> np.ndarray:
    """Uniform positions in the unit square; Euclidean costs normalized to [0,1]."""

    return generate_geometric_instance(n_robots, n_tasks, seed)[2]


def _evaluate(
    method: str,
    result: AllocationResult,
    costs: np.ndarray,
    penalty: float,
    optimum_cost: float,
    welfare_offset: float,
    instance_id: str,
    seed: int,
) -> dict[str, Any]:
    metrics = profile_metrics(costs, result.assignment, penalty)
    feasible = bool(metrics["feasible"])
    cost = float(metrics["social_cost"])
    regret = cost - optimum_cost if feasible else np.nan
    welfare = welfare_offset * costs.shape[1] - float(metrics["penalized_cost"])
    optimum_welfare = welfare_offset * costs.shape[1] - optimum_cost
    return {
        "instance_id": instance_id,
        "seed": seed,
        "n_robots": costs.shape[0],
        "n_tasks": costs.shape[1],
        "task_ratio": costs.shape[1] / costs.shape[0],
        "method": method,
        "feasible": feasible,
        "deficit": int(metrics["deficit"]),
        "excess": int(metrics["excess"]),
        "social_cost": cost,
        "optimum_cost": optimum_cost,
        "regret": regret,
        "regret_per_task": regret / costs.shape[1] if feasible else np.nan,
        "social_welfare": welfare,
        "welfare_efficiency": welfare / optimum_welfare,
        "iterations": result.iterations,
        "evaluations": result.evaluations,
        "runtime_s": result.runtime_s,
        "converged": result.converged,
        "epsilon_cs_violation": result.epsilon_cs_violation,
    }


def run_campaign(config: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    seed_base = int(config["seed_base"])
    for n_robots in map(int, config["fleet_sizes"]):
        for ratio_index, ratio in enumerate(map(float, config["task_ratios"])):
            n_tasks = max(1, min(n_robots, int(round(n_robots * ratio))))
            for repetition in range(int(config["number_seeds"])):
                seed = seed_base + n_robots * 100_000 + ratio_index * 10_000 + repetition
                instance_id = f"N{n_robots:03d}_K{n_tasks:03d}_S{seed}"
                costs = generate_geometric_costs(n_robots, n_tasks, seed)
                penalty = float(np.max(costs)) + float(config["penalty_margin"])
                welfare_offset = 1.0 + float(config["penalty_margin"])
                oracle = hungarian_assignment(costs)
                optimum_cost = float(profile_metrics(costs, oracle.assignment, penalty)["social_cost"])
                rng = np.random.default_rng(seed + 1)
                potential = potential_best_response(
                    costs,
                    penalty=penalty,
                    rng=rng,
                    max_sweeps=int(config["max_best_response_sweeps"]),
                )
                exchange = pairwise_exchange(
                    costs,
                    initial=potential.assignment,
                    max_events=int(config["max_exchange_events"]),
                )
                exchange = AllocationResult(
                    assignment=exchange.assignment,
                    iterations=potential.iterations + exchange.iterations,
                    evaluations=potential.evaluations + exchange.evaluations,
                    runtime_s=potential.runtime_s + exchange.runtime_s,
                    converged=potential.converged and exchange.converged,
                    history=(potential.history or ()) + (exchange.history or ())[1:],
                )
                methods: dict[str, AllocationResult] = {
                    "hungarian": oracle,
                    "auction_eps": auction_assignment(costs, float(config["auction_epsilon"])),
                    "greedy": greedy_assignment(costs),
                    "potential_br": potential,
                    "potential_exchange": exchange,
                    "no_exclusion": potential_best_response(
                        costs,
                        penalty=0.0,
                        rng=np.random.default_rng(seed + 2),
                        max_sweeps=int(config["max_best_response_sweeps"]),
                    ),
                }
                for method, result in methods.items():
                    rows.append(
                        _evaluate(
                            method,
                            result,
                            costs,
                            penalty,
                            optimum_cost,
                            welfare_offset,
                            instance_id,
                            seed,
                        )
                    )
    return pd.DataFrame(rows)


def run_exact_audit(config: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    seed_base = int(config["seed_base"]) + 90_000_000
    for n_robots, n_tasks in config["exact_pairs"]:
        for repetition in range(int(config["exact_seeds"])):
            seed = seed_base + int(n_robots) * 1000 + int(n_tasks) * 100 + repetition
            costs = generate_geometric_costs(int(n_robots), int(n_tasks), seed)
            penalty = float(np.max(costs)) + float(config["penalty_margin"])
            audit = enumerate_pure_nash(costs, penalty)
            rows.append(
                {
                    "seed": seed,
                    "n_robots": int(n_robots),
                    "n_tasks": int(n_tasks),
                    "action_profiles": int(audit["profiles"]),
                    "feasible_profiles": int(audit["feasible_profiles"]),
                    "theoretical_matchings": factorial(int(n_robots))
                    // factorial(int(n_robots) - int(n_tasks)),
                    "nash_count": int(audit["nash_count"]),
                    "optimal_nash_count": int(audit["optimal_nash_count"]),
                    "optimal_nash_fraction": float(audit["optimal_nash_count"])
                    / float(audit["nash_count"]),
                    "optimum_cost": float(audit["optimum_cost"]),
                    "worst_nash_cost": float(audit["worst_nash_cost"]),
                    "worst_cost_ratio": float(audit["worst_nash_cost"])
                    / max(float(audit["optimum_cost"]), 1e-12),
                }
            )
    return pd.DataFrame(rows)


def summarize(runs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    grouped = runs.groupby(["method", "n_robots", "n_tasks"], sort=False)
    summary = grouped.agg(
        runs=("seed", "size"),
        feasible_rate=("feasible", "mean"),
        median_regret_per_task=("regret_per_task", "median"),
        q25_regret_per_task=("regret_per_task", lambda x: x.quantile(0.25)),
        q75_regret_per_task=("regret_per_task", lambda x: x.quantile(0.75)),
        median_welfare_efficiency=("welfare_efficiency", "median"),
        median_iterations=("iterations", "median"),
        median_evaluations=("evaluations", "median"),
        median_runtime_s=("runtime_s", "median"),
    ).reset_index()
    aggregate = runs.groupby("method", sort=False).agg(
        runs=("seed", "size"),
        feasible_rate=("feasible", "mean"),
        median_regret_per_task=("regret_per_task", "median"),
        q25_regret_per_task=("regret_per_task", lambda x: x.quantile(0.25)),
        q75_regret_per_task=("regret_per_task", lambda x: x.quantile(0.75)),
        median_welfare_efficiency=("welfare_efficiency", "median"),
        median_iterations=("iterations", "median"),
        median_evaluations=("evaluations", "median"),
        median_runtime_s=("runtime_s", "median"),
    ).reset_index()
    return summary, aggregate


def paired_bootstrap_contrasts(runs: pd.DataFrame, resamples: int, seed: int) -> pd.DataFrame:
    contrasts = [
        ("potential_exchange", "potential_br"),
        ("auction_eps", "hungarian"),
        ("potential_exchange", "greedy"),
    ]
    wide = runs.pivot(index="instance_id", columns="method", values="regret_per_task")
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for left, right in contrasts:
        values = (wide[left] - wide[right]).dropna().to_numpy(dtype=float)
        estimates = np.empty(resamples, dtype=float)
        for index in range(resamples):
            estimates[index] = np.mean(rng.choice(values, size=len(values), replace=True))
        rows.append(
            {
                "contrast": f"{left} - {right}",
                "n_pairs": len(values),
                "mean_difference": float(np.mean(values)),
                "ci95_low": float(np.quantile(estimates, 0.025)),
                "ci95_high": float(np.quantile(estimates, 0.975)),
            }
        )
    return pd.DataFrame(rows)


def sp0_hypothesis_test(runs: pd.DataFrame) -> pd.DataFrame:
    """Exact paired test of feasibility with and without exclusion penalties."""

    paired = runs.pivot(index="instance_id", columns="method", values="feasible").astype(bool)
    complete = paired["potential_br"]
    ablation = paired["no_exclusion"]
    improved = int((complete & ~ablation).sum())
    worsened = int((~complete & ablation).sum())
    discordant = improved + worsened
    p_value = (
        float(binomtest(improved, discordant, p=0.5, alternative="two-sided").pvalue)
        if discordant
        else 1.0
    )
    return pd.DataFrame(
        [
            {
                "n_pairs": int(len(paired)),
                "complete_feasible": int(complete.sum()),
                "ablation_feasible": int(ablation.sum()),
                "complete_only": improved,
                "ablation_only": worsened,
                "paired_difference_pp": float(100.0 * (complete.mean() - ablation.mean())),
                "exact_mcnemar_p_two_sided": p_value,
                "reject_h0_alpha_0_05": bool(p_value < 0.05),
            }
        ]
    )


def _representative_seed(runs: pd.DataFrame, n_robots: int, n_tasks: int) -> int:
    """Select the potential-BR run closest to its median regret at one scale."""

    frame = runs[
        (runs.method == "potential_br")
        & (runs.n_robots == n_robots)
        & (runs.n_tasks == n_tasks)
    ].copy()
    if frame.empty:
        raise ValueError("representative scale is absent from the campaign")
    target = float(frame.regret_per_task.median())
    frame["distance_to_median"] = (frame.regret_per_task - target).abs()
    return int(frame.sort_values(["distance_to_median", "seed"]).iloc[0].seed)


def representative_trace(
    runs: pd.DataFrame, config: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float, dict[str, AllocationResult], pd.DataFrame, int]:
    """Re-run a median 4x4 instance and return event-level performance histories."""

    n_robots = int(config.get("trace_n_robots", 4))
    n_tasks = int(config.get("trace_n_tasks", 4))
    seed = _representative_seed(runs, n_robots, n_tasks)
    robot_positions, task_positions, costs = generate_geometric_instance(
        n_robots, n_tasks, seed
    )
    penalty = float(np.max(costs)) + float(config["penalty_margin"])
    welfare_offset = 1.0 + float(config["penalty_margin"])
    oracle = hungarian_assignment(costs)
    optimum_cost = float(profile_metrics(costs, oracle.assignment, penalty)["social_cost"])
    potential = potential_best_response(
        costs,
        penalty=penalty,
        rng=np.random.default_rng(seed + 1),
        max_sweeps=int(config["max_best_response_sweeps"]),
    )
    local_exchange = pairwise_exchange(
        costs,
        initial=potential.assignment,
        max_events=int(config["max_exchange_events"]),
    )
    combined_exchange = AllocationResult(
        assignment=local_exchange.assignment,
        iterations=potential.iterations + local_exchange.iterations,
        evaluations=potential.evaluations + local_exchange.evaluations,
        runtime_s=potential.runtime_s + local_exchange.runtime_s,
        converged=potential.converged and local_exchange.converged,
        history=(potential.history or ()) + (local_exchange.history or ())[1:],
    )
    methods = {
        "hungarian": oracle,
        "auction_eps": auction_assignment(costs, float(config["auction_epsilon"])),
        "greedy": greedy_assignment(costs),
        "potential_br": potential,
        "potential_exchange": combined_exchange,
        "no_exclusion": potential_best_response(
            costs,
            penalty=0.0,
            rng=np.random.default_rng(seed + 2),
            max_sweeps=int(config["max_best_response_sweeps"]),
        ),
    }
    rows: list[dict[str, Any]] = []
    for method in ("auction_eps", "greedy", "potential_br", "potential_exchange"):
        history = methods[method].history
        if not history:
            raise RuntimeError(f"missing event history for {method}")
        for event, assignment in enumerate(history):
            metrics = profile_metrics(costs, assignment, penalty)
            feasible = bool(metrics["feasible"])
            welfare = welfare_offset * n_tasks - float(metrics["penalized_cost"])
            optimum_welfare = welfare_offset * n_tasks - optimum_cost
            rows.append(
                {
                    "seed": seed,
                    "method": method,
                    "event": event,
                    "coverage_fraction": 1.0 - int(metrics["deficit"]) / n_tasks,
                    "duplicate_fraction": int(metrics["excess"]) / n_tasks,
                    "welfare_efficiency": welfare / optimum_welfare,
                    "regret_per_task": (
                        (float(metrics["social_cost"]) - optimum_cost) / n_tasks
                        if feasible
                        else np.nan
                    ),
                    "feasible": feasible,
                }
            )
    return (
        robot_positions,
        task_positions,
        costs,
        penalty,
        optimum_cost,
        methods,
        pd.DataFrame(rows),
        seed,
    )


def theorem_checks(runs: pd.DataFrame, exact: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    auction = runs[runs.method == "auction_eps"]
    potential = runs[runs.method == "potential_br"]
    exchange = runs[runs.method == "potential_exchange"]
    paired = runs.pivot(index="instance_id", columns="method", values="social_cost")
    checks = [
        (
            "exact_nash_equals_feasible",
            bool((exact.nash_count == exact.feasible_profiles).all()),
            int(len(exact)),
        ),
        (
            "exact_nash_count_equals_injections",
            bool((exact.nash_count == exact.theoretical_matchings).all()),
            int(len(exact)),
        ),
        (
            "potential_best_response_is_feasible",
            bool(potential.feasible.all()),
            int(len(potential)),
        ),
        (
            "pairwise_exchange_is_monotone",
            bool((paired.potential_exchange <= paired.potential_br + 1e-12).all()),
            int(len(paired)),
        ),
        (
            "auction_epsilon_cs",
            bool((auction.epsilon_cs_violation <= float(config["auction_epsilon"]) + 1e-10).all()),
            int(len(auction)),
        ),
        (
            "auction_additive_bound",
            bool(
                (
                    auction.regret
                    <= auction.n_robots * float(config["auction_epsilon"]) + 1e-10
                ).all()
            ),
            int(len(auction)),
        ),
        (
            "ablation_exposes_missing_exclusion",
            bool((~runs[runs.method == "no_exclusion"].feasible).all()),
            int(len(runs[runs.method == "no_exclusion"])),
        ),
    ]
    return pd.DataFrame(checks, columns=["check", "passed", "evaluated_cases"])


def _method_color(method: str) -> str:
    return {
        "hungarian": "#23395B",
        "auction_eps": "#3E7CB1",
        "greedy": "#F28E2B",
        "potential_br": "#8C6BB1",
        "potential_exchange": "#2A9D8F",
        "no_exclusion": "#C44E52",
    }[method]


def make_figures(
    runs: pd.DataFrame,
    exact: pd.DataFrame,
    output: Path,
    trace_bundle: tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        float,
        float,
        dict[str, AllocationResult],
        pd.DataFrame,
        int,
    ],
) -> None:
    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    order = list(METHOD_LABELS)

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.3), constrained_layout=True)
    square = exact[exact.n_robots == exact.n_tasks].groupby("n_robots").median(numeric_only=True)
    x = square.index.to_numpy()
    axes[0].semilogy(x, square.nash_count, "o-", color="#23395B", label="Nash enumerados")
    axes[0].semilogy(x, [factorial(int(v)) for v in x], "--", color="#E76F51", label="$N!$")
    axes[0].set_xlabel("$N=K$")
    axes[0].set_ylabel("Número de equilibrios")
    axes[0].set_title("(a) Multiplicidad de equilibrios")
    axes[0].set_xticks(x)
    axes[0].set_xlim(float(x.min()) - 0.15, float(x.max()) + 0.15)
    axes[0].set_ylim(1.6, float(square.nash_count.max()) * 1.45)
    axes[0].grid(alpha=0.25)
    axes[0].legend(fontsize=8)
    for n_robots, nash_count in zip(x, square.nash_count, strict=True):
        axes[0].annotate(
            f"{int(nash_count)}",
            (n_robots, nash_count),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color="#23395B",
        )

    feasible_methods = ("auction_eps", "greedy", "potential_br", "potential_exchange")
    box_data = [runs[(runs.method == m) & runs.feasible].regret_per_task for m in feasible_methods]
    box = axes[1].boxplot(
        box_data,
        patch_artist=True,
        showfliers=True,
        flierprops={
            "marker": "o",
            "markersize": 2.6,
            "markerfacecolor": "#555555",
            "markeredgecolor": "none",
            "alpha": 0.35,
        },
    )
    for patch, method in zip(box["boxes"], feasible_methods, strict=True):
        patch.set_facecolor(_method_color(method))
        patch.set_alpha(0.75)
    axes[1].set_xticks(
        np.arange(1, len(feasible_methods) + 1),
        [
            "Subasta\n$\\varepsilon$",
            "Greedy",
            "Mejor\nrespuesta",
            "Mejor respuesta\n+ 2-intercambio",
        ],
    )
    axes[1].set_ylabel(r"Brecha por carga $r$ ($\downarrow$)")
    axes[1].set_title("(b) Eficiencia frente al oráculo")
    axes[1].tick_params(axis="x", labelsize=8)
    axes[1].grid(axis="y", alpha=0.25)
    axes[1].axhline(0.0, color="#555555", linestyle="--", linewidth=0.8, alpha=0.65)
    for extension in ("png", "pdf"):
        fig.savefig(figures / f"fig-sp0-equilibrium-efficiency.{extension}", dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.7), constrained_layout=True)
    scaling = runs.groupby(["method", "n_robots"]).median(numeric_only=True).reset_index()
    for method in order[:-1]:
        frame = scaling[scaling.method == method]
        axes[0].loglog(frame.n_robots, frame.runtime_s, "o-", color=_method_color(method), label=METHOD_LABELS[method])
        axes[1].loglog(frame.n_robots, frame.evaluations, "o-", color=_method_color(method))
        axes[2].plot(frame.n_robots, frame.welfare_efficiency, "o-", color=_method_color(method))
    axes[0].set_title("(a) Tiempo observado")
    axes[0].set_ylabel("Mediana CPU [s]")
    axes[1].set_title("(b) Trabajo lógico")
    axes[1].set_ylabel("Evaluaciones")
    axes[2].set_title("(c) Bienestar normalizado")
    axes[2].set_ylabel(r"$W/W^\star$")
    for axis in axes:
        axis.set_xlabel("Robots $N$")
        axis.grid(alpha=0.25)
    axes[0].legend(fontsize=7)
    for extension in ("png", "pdf"):
        fig.savefig(figures / f"fig-sp0-scaling-welfare.{extension}", dpi=220)
    plt.close(fig)

    robot_positions, task_positions, _, _, _, methods, temporal, seed = trace_bundle
    fig, axes = plt.subplots(2, 3, figsize=(10.6, 6.8), sharex=True, sharey=True, constrained_layout=True)
    for axis, method in zip(axes.flat, order, strict=True):
        assignment = methods[method].assignment
        for robot, task_action in enumerate(assignment):
            if task_action <= 0:
                continue
            task = int(task_action) - 1
            axis.plot(
                [robot_positions[robot, 0], task_positions[task, 0]],
                [robot_positions[robot, 1], task_positions[task, 1]],
                color=_method_color(method),
                linewidth=1.7,
                alpha=0.85,
                zorder=1,
            )
        axis.scatter(
            robot_positions[:, 0],
            robot_positions[:, 1],
            s=58,
            marker="o",
            facecolor="#DCEAF7",
            edgecolor="#23395B",
            linewidth=1.1,
            label="Robots",
            zorder=3,
        )
        axis.scatter(
            task_positions[:, 0],
            task_positions[:, 1],
            s=64,
            marker="s",
            facecolor="#FCE8D5",
            edgecolor="#B95F18",
            linewidth=1.1,
            label="Cargas",
            zorder=3,
        )
        label_box = {"boxstyle": "round,pad=0.10", "facecolor": "white", "edgecolor": "none", "alpha": 0.78}
        for index, point in enumerate(robot_positions):
            axis.annotate(
                f"R{index + 1}",
                point,
                xytext=(-5, 5),
                textcoords="offset points",
                ha="right",
                va="bottom",
                fontsize=8.2,
                bbox=label_box,
            )
        for index, point in enumerate(task_positions):
            axis.annotate(
                f"L{index + 1}",
                point,
                xytext=(5, -5),
                textcoords="offset points",
                ha="left",
                va="top",
                fontsize=8.2,
                bbox=label_box,
            )
        axis.set_title(METHOD_LABELS[method], fontsize=10)
        axis.set_xlim(-0.04, 1.04)
        axis.set_ylim(-0.04, 1.04)
        axis.set_xticks((0.0, 0.5, 1.0))
        axis.set_yticks((0.0, 0.5, 1.0))
        axis.set_aspect("equal", adjustable="box")
        axis.grid(alpha=0.18)
    for axis in axes[-1, :]:
        axis.set_xlabel("$x$")
    for axis in axes[:, 0]:
        axis.set_ylabel("$y$")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=2, frameon=False)
    fig.suptitle(f"Instancia representativa $4\\times4$ (semilla {seed})", fontsize=11.5)
    for extension in ("png", "pdf"):
        fig.savefig(figures / f"fig-sp0-top-view-assignments.{extension}", dpi=220)
    plt.close(fig)

    temporal_methods = ("auction_eps", "greedy", "potential_br", "potential_exchange")
    metric_rows = (
        ("coverage_fraction", "Cargas cubiertas", 1.0),
        ("duplicate_fraction", "Duplicidad", 0.0),
        ("welfare_efficiency", r"Bienestar $W/W^\star$", 1.0),
        ("regret_per_task", "Regret por carga", 0.0),
    )
    welfare_values = temporal.welfare_efficiency[np.isfinite(temporal.welfare_efficiency)]
    regret_values = temporal.regret_per_task[np.isfinite(temporal.regret_per_task)]
    welfare_lower = max(0.0, float(welfare_values.min()) - 0.02)
    regret_upper = max(0.04, float(regret_values.max()) * 1.10)
    temporal_titles = {
        "auction_eps": r"Subasta $\varepsilon$",
        "greedy": "Greedy",
        "potential_br": "Mejor respuesta",
        "potential_exchange": "Mejor respuesta + 2-int.",
    }
    fig, axes = plt.subplots(4, 4, figsize=(10.4, 7.7), constrained_layout=True)
    for column, method in enumerate(temporal_methods):
        frame = temporal[temporal.method == method]
        for row, (metric, ylabel, target) in enumerate(metric_rows):
            axis = axes[row, column]
            axis.step(
                frame.event,
                frame[metric],
                where="post",
                color=_method_color(method),
                linewidth=1.7,
            )
            finite = frame[np.isfinite(frame[metric])]
            if metric == "regret_per_task" and not finite.empty:
                first_defined = float(finite.event.iloc[0])
                first_event = float(frame.event.min())
                if first_defined > first_event:
                    axis.axvspan(first_event, first_defined, color="#E5E7EB", alpha=0.65, zorder=0)
                    axis.text(
                        (first_event + first_defined) / 2.0,
                        0.90,
                        "no definido",
                        transform=axis.get_xaxis_transform(),
                        ha="center",
                        va="top",
                        fontsize=6.4,
                        color="#555555",
                    )
            if not finite.empty:
                axis.plot(
                    finite.event.iloc[-1],
                    finite[metric].iloc[-1],
                    "o",
                    color=_method_color(method),
                    markersize=3.5,
                )
            axis.axhline(target, color="#555555", linestyle="--", linewidth=0.8, alpha=0.65)
            axis.grid(alpha=0.2)
            axis.set_xlim(0, max(1, int(frame.event.max())))
            if metric in {"coverage_fraction", "duplicate_fraction"}:
                axis.set_ylim(-0.05, 1.05)
            elif metric == "welfare_efficiency":
                axis.set_ylim(welfare_lower, 1.02)
            elif metric == "regret_per_task":
                axis.set_ylim(-0.002, regret_upper)
            if column == 0:
                axis.set_ylabel(ylabel, fontsize=8.5)
            if row == 3:
                axis.set_xlabel("Evento algorítmico", fontsize=8.5)
            if row == 0:
                axis.set_title(temporal_titles[method], fontsize=9)
            axis.set_xticks(np.arange(0, int(frame.event.max()) + 1, 1))
            axis.tick_params(labelsize=7.2)
    fig.suptitle(f"Evolución por evento en la instancia representativa $4\\times4$ (semilla {seed})", fontsize=10.5)
    for extension in ("png", "pdf"):
        fig.savefig(figures / f"fig-sp0-temporal-performance-4x4.{extension}", dpi=220)
    plt.close(fig)


def _latex_method_table(aggregate: pd.DataFrame) -> str:
    rows = []
    indexed = aggregate.set_index("method")
    reported_methods = (
        "hungarian",
        "auction_eps",
        "greedy",
        "potential_br",
        "potential_exchange",
    )
    for method in reported_methods:
        row = indexed.loc[method]
        regret = "--" if pd.isna(row.median_regret_per_task) else f"{row.median_regret_per_task:.4f}"
        rows.append(
            f"{METHOD_LABELS[method]} & {100 * row.feasible_rate:.1f} & {regret} & "
            f"{100 * row.median_welfare_efficiency:.2f} & {row.median_evaluations:.0f} \\\\"
        )
    header = (
        "\\begin{tabular}{lrrrr}\n"
        "\\toprule\n"
        "Método & Factible [\\%] & Brecha/carga mediana & $100W/W^\\star$ & Op. registradas \\\\\n"
        "\\midrule\n"
    )
    return header + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"


def _latex_exact_table(exact: pd.DataFrame) -> str:
    grouped = exact.groupby(["n_robots", "n_tasks"]).median(numeric_only=True).reset_index()
    rows = []
    for row in grouped.itertuples():
        rows.append(
            f"{int(row.n_robots)} & {int(row.n_tasks)} & {int(row.action_profiles)} & "
            f"{int(row.nash_count)} & {100 * row.optimal_nash_fraction:.3f} \\\\"
        )
    return "\n".join(rows) + "\n"


def _latex_hypothesis_table(result: pd.DataFrame) -> str:
    row = result.iloc[0]
    p_value = float(row.exact_mcnemar_p_two_sided)
    exponent = int(np.floor(np.log10(p_value))) if p_value > 0.0 else 0
    mantissa = p_value / (10.0**exponent) if p_value > 0.0 else 0.0
    decision = "Rechazar" if bool(row.reject_h0_alpha_0_05) else "No rechazar"
    return (
        "\\begin{tabular}{lrr}\n"
        "\\toprule\n"
        "Resultado pareado & Penalización completa & Sin exclusión \\\\\n"
        "\\midrule\n"
        f"Asignaciones factibles & {int(row.complete_feasible)}/{int(row.n_pairs)} & "
        f"{int(row.ablation_feasible)}/{int(row.n_pairs)} \\\\\n"
        f"Casos ganados en exclusiva & {int(row.complete_only)} & {int(row.ablation_only)} \\\\\n"
        f"Diferencia de factibilidad [pp] & \\multicolumn{{2}}{{c}}{{{row.paired_difference_pp:.1f}}} \\\\\n"
        f"McNemar exacto bilateral & \\multicolumn{{2}}{{c}}{{${mantissa:.2f}\\times10^{{{exponent}}}$}} \\\\\n"
        f"Decisión ($\\alpha=0.05$) & \\multicolumn{{2}}{{c}}{{{decision} $H_{{0,\\mathrm{{SP0}}}}$}} \\\\\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
    )


def _write_report(
    output: Path,
    runs: pd.DataFrame,
    aggregate: pd.DataFrame,
    checks: pd.DataFrame,
) -> None:
    best_exchange = aggregate.set_index("method").loc["potential_exchange"]
    report = [
        "# SP0 theory and experiment report",
        "",
        f"Runs: {len(runs)}; paired instances: {runs.instance_id.nunique()}.",
        f"All theory checks passed: {bool(checks.passed.all())}.",
        f"Potential + 2-exchange feasibility: {100 * best_exchange.feasible_rate:.1f}%.",
        f"Potential + 2-exchange median regret/task: {best_exchange.median_regret_per_task:.6f}.",
        "",
        "Runtime values compare these concrete implementations only; they are not an architecture-independent complexity proof.",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def execute(config_path: Path, smoke: bool = False) -> Path:
    config = load_config(config_path)
    if smoke:
        config = dict(config)
        config["output_dir"] = str(Path(config["output_dir"]) / "smoke")
        config["fleet_sizes"] = [4, 8]
        config["task_ratios"] = [0.5, 1.0]
        config["number_seeds"] = 2
        config["exact_seeds"] = 1
        config["exact_pairs"] = [[2, 2], [3, 2], [3, 3]]
        config["bootstrap_resamples"] = 100
    output = Path(config["output_dir"])
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    runs = run_campaign(config)
    exact = run_exact_audit(config)
    summary, aggregate = summarize(runs)
    contrasts = paired_bootstrap_contrasts(
        runs, int(config["bootstrap_resamples"]), int(config["seed_base"]) + 777
    )
    hypothesis = sp0_hypothesis_test(runs)
    checks = theorem_checks(runs, exact, config)
    trace_bundle = representative_trace(runs, config)
    temporal = trace_bundle[6]
    representative_seed = trace_bundle[7]
    runs.to_csv(tables / "runs.csv", index=False)
    exact.to_csv(tables / "exact_nash_audit.csv", index=False)
    summary.to_csv(tables / "summary_by_scale.csv", index=False)
    aggregate.to_csv(tables / "method_summary.csv", index=False)
    contrasts.to_csv(tables / "paired_bootstrap_contrasts.csv", index=False)
    hypothesis.to_csv(tables / "sp0_hypothesis_test.csv", index=False)
    temporal.to_csv(tables / "sp0_temporal_metrics.csv", index=False)
    pd.DataFrame(
        [
            {
                "seed": representative_seed,
                "n_robots": int(config.get("trace_n_robots", 4)),
                "n_tasks": int(config.get("trace_n_tasks", 4)),
                "selection": "potential_br_closest_to_median_regret_per_task",
            }
        ]
    ).to_csv(tables / "sp0_representative_instance.csv", index=False)
    checks.to_csv(tables / "theorem_checks.csv", index=False)
    (tables / "sp0_method_summary.tex").write_text(_latex_method_table(aggregate), encoding="utf-8")
    (tables / "sp0_exact_summary.tex").write_text(_latex_exact_table(exact), encoding="utf-8")
    (tables / "sp0_hypothesis_summary.tex").write_text(
        _latex_hypothesis_table(hypothesis), encoding="utf-8"
    )
    make_figures(runs, exact, output, trace_bundle)
    _write_report(output, runs, aggregate, checks)
    artifact_paths = sorted(
        path
        for path in output.rglob("*")
        if path.is_file() and "smoke" not in path.relative_to(output).parts
    )
    manifest = {
        "experiment_id": config["experiment_id"],
        "config": config,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "theory_gate_passed": bool(checks.passed.all()),
        "artifacts": {
            str(path.relative_to(output)).replace("\\", "/"): _sha256(path)
            for path in artifact_paths
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return output

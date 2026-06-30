"""Finite-population Smith sweep for deterministic-approximation checks.

The script targets the well-mixed regime used by the theoretical result:
global information, no spatial discount, and the fluid scaling

    n_k^(N) = nu_k N,    beta_N = beta_tilde / N.

It compares a finite jump process against the associated Smith ODE and
estimates the log-log slope of the finite-population error versus N.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


Array = np.ndarray


@dataclass(frozen=True)
class SweepConfig:
    n_values: tuple[int, ...]
    seeds: tuple[int, ...]
    horizon: float
    dt: float
    mu: float
    beta_tilde: float
    rewards: Array
    nu: Array
    idle_reward: float
    x0: Array
    transient: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results/smith_deterministic_approx"))
    parser.add_argument(
        "--figure",
        type=Path,
        default=Path("docs/doc-06-explanatory-report/figures/fig-smith-deterministic-sweep.png"),
    )
    parser.add_argument("--n-values", default="6,12,24,48,96")
    parser.add_argument("--seeds", type=int, default=40)
    parser.add_argument("--start-seed", type=int, default=2026)
    parser.add_argument("--horizon", type=float, default=24.0)
    parser.add_argument("--dt", type=float, default=0.02)
    parser.add_argument("--mu", type=float, default=1.0)
    parser.add_argument("--beta-tilde", type=float, default=6.0)
    parser.add_argument("--transient", type=float, default=4.0)
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> SweepConfig:
    n_values = tuple(int(item) for item in args.n_values.split(",") if item.strip())
    seeds = tuple(range(args.start_seed, args.start_seed + args.seeds))
    rewards = np.array([1.25, 1.0, 0.85], dtype=float)
    nu = np.array([0.24, 0.26, 0.22], dtype=float)
    idle_reward = 0.18
    x0 = np.array([0.28, 0.30, 0.20, 0.22], dtype=float)
    x0 = x0 / np.sum(x0)
    return SweepConfig(
        n_values=n_values,
        seeds=seeds,
        horizon=float(args.horizon),
        dt=float(args.dt),
        mu=float(args.mu),
        beta_tilde=float(args.beta_tilde),
        rewards=rewards,
        nu=nu,
        idle_reward=float(idle_reward),
        x0=x0,
        transient=float(args.transient),
    )


def payoffs(x: Array, config: SweepConfig) -> Array:
    values = np.empty(config.rewards.size + 1, dtype=float)
    values[0] = config.idle_reward
    task_x = x[1:]
    values[1:] = config.rewards / (1.0 + np.exp(config.beta_tilde * (task_x - config.nu)))
    return values


def smith_rhs(x: Array, config: SweepConfig) -> Array:
    f = payoffs(x, config)
    positive = np.maximum(f[None, :] - f[:, None], 0.0)
    inflow = np.sum(x[:, None] * positive, axis=0)
    outflow = x * np.sum(positive, axis=1)
    return config.mu * (inflow - outflow)


def integrate_ode(config: SweepConfig) -> tuple[Array, Array]:
    steps = int(round(config.horizon / config.dt))
    times = np.linspace(0.0, config.horizon, steps + 1)
    x = np.empty((steps + 1, config.x0.size), dtype=float)
    x[0] = config.x0
    for step in range(steps):
        x_next = x[step] + config.dt * smith_rhs(x[step], config)
        x_next = np.maximum(x_next, 0.0)
        x[step + 1] = x_next / np.sum(x_next)
    return times, x


def sample_initial_strategies(n_agents: int, x0: Array, rng: np.random.Generator) -> Array:
    return rng.choice(np.arange(x0.size), size=n_agents, p=x0)


def simulate_finite(n_agents: int, seed: int, ode_path: Array, config: SweepConfig) -> Array:
    rng = np.random.default_rng(seed)
    states = sample_initial_strategies(n_agents, config.x0, rng)
    finite = np.empty_like(ode_path)
    finite[0] = np.bincount(states, minlength=config.x0.size) / n_agents

    for step in range(ode_path.shape[0] - 1):
        x_emp = finite[step]
        f = payoffs(x_emp, config)
        next_states = states.copy()
        for idx, current in enumerate(states):
            rates = config.mu * np.maximum(f - f[current], 0.0)
            rates[current] = 0.0
            total_rate = float(np.sum(rates))
            jump_probability = min(config.dt * total_rate, 0.95)
            if total_rate > 0.0 and rng.random() < jump_probability:
                next_states[idx] = int(rng.choice(np.arange(f.size), p=rates / total_rate))
        states = next_states
        finite[step + 1] = np.bincount(states, minlength=config.x0.size) / n_agents
    return finite


def run_sweep(config: SweepConfig) -> tuple[list[dict[str, float]], list[dict[str, float]], float]:
    times, ode_path = integrate_ode(config)
    transient_idx = int(math.ceil(config.transient / config.dt))

    run_rows: list[dict[str, float]] = []
    summary_rows: list[dict[str, float]] = []
    for n_agents in config.n_values:
        errors = []
        for seed in config.seeds:
            finite = simulate_finite(n_agents, seed, ode_path, config)
            norm_error = np.linalg.norm(finite - ode_path, axis=1)
            tail_error = norm_error[transient_idx:]
            rms = float(np.sqrt(np.mean(tail_error**2)))
            sup = float(np.max(tail_error))
            errors.append(rms)
            run_rows.append({"N": n_agents, "seed": seed, "rms_error": rms, "sup_error": sup})
        summary_rows.append(
            {
                "N": n_agents,
                "mean_rms_error": float(np.mean(errors)),
                "std_rms_error": float(np.std(errors, ddof=1)) if len(errors) > 1 else 0.0,
                "n_seeds": float(len(errors)),
            }
        )

    log_n = np.log([row["N"] for row in summary_rows])
    log_e = np.log([row["mean_rms_error"] for row in summary_rows])
    slope, intercept = np.polyfit(log_n, log_e, deg=1)
    for row in summary_rows:
        row["fit_slope"] = float(slope)
        row["fit_intercept"] = float(intercept)
    return run_rows, summary_rows, float(slope)


def write_csv(path: Path, rows: list[dict[str, float]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_plot(path: Path, summary_rows: list[dict[str, float]], slope: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n_values = np.array([row["N"] for row in summary_rows], dtype=float)
    means = np.array([row["mean_rms_error"] for row in summary_rows], dtype=float)
    stds = np.array([row["std_rms_error"] for row in summary_rows], dtype=float)
    reference = means[0] * (n_values / n_values[0]) ** (-0.5)

    plt.figure(figsize=(6.4, 4.2), dpi=180)
    plt.errorbar(n_values, means, yerr=stds, marker="o", capsize=4, label="Simulacion finita")
    plt.plot(n_values, reference, "--", label="Referencia $N^{-1/2}$")
    plt.xscale("log", base=2)
    plt.yscale("log")
    plt.xlabel("Numero de robots N")
    plt.ylabel("RMS de $\\|X^N(t)-x(t)\\|$")
    plt.title(f"Cota Smith finito-ODE: pendiente observada {slope:.2f}")
    plt.grid(True, which="both", alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def write_readme(path: Path, summary_rows: list[dict[str, float]], slope: float, config: SweepConfig) -> None:
    path.write_text(
        "\n".join(
            [
                "# Smith deterministic approximation sweep",
                "",
                f"- N values: {', '.join(str(n) for n in config.n_values)}",
                f"- Seeds: {config.seeds[0]}-{config.seeds[-1]} (`n={len(config.seeds)}`)",
                f"- Horizon: {config.horizon:g} s; dt: {config.dt:g} s",
                f"- Fluid scaling: beta_N = {config.beta_tilde:g} / N",
                f"- Fitted log-log slope: {slope:.4f} (target: -0.5)",
                "",
                "| N | mean RMS error | std |",
                "|---:|---:|---:|",
                *[
                    f"| {int(row['N'])} | {row['mean_rms_error']:.6g} | {row['std_rms_error']:.6g} |"
                    for row in summary_rows
                ],
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    config = build_config(args)
    run_rows, summary_rows, slope = run_sweep(config)

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "runs.csv", run_rows)
    write_csv(args.out / "summary.csv", summary_rows)
    write_plot(args.figure, summary_rows, slope)
    write_readme(args.out / "README.md", summary_rows, slope, config)
    print(f"wrote {args.out}")
    print(f"wrote {args.figure}")
    print(f"log-log slope: {slope:.4f}")


if __name__ == "__main__":
    main()

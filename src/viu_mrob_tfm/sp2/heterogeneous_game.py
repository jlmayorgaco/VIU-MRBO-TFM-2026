"""SP2 heterogeneous-capacity population-game experiment.

The module deliberately separates four stages: continuous preferences, RAW
argmax decoding, capacity-aware integer closure, and a centralized MILP oracle.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.stats import wilcoxon

from viu_mrob_tfm.sp1.homogeneous import project_rows, vector_field


PROTOCOLS = ("smith", "replicator", "erv_bnn")
FITNESS_MODES = ("plain_deficit", "marginal_deficit", "marginal_log")
POPULATION_METHODS = tuple(f"{p}__{f}" for p in PROTOCOLS for f in FITNESS_MODES)
CONTROL_METHODS = ("uniform_closure", "random_closure")
REFERENCE_METHODS = ("greedy_capacity", "auction_capacity", "milp_exact")
ALL_METHODS = POPULATION_METHODS + CONTROL_METHODS + REFERENCE_METHODS
ALIGNED_FITNESS = {"marginal_deficit", "marginal_log"}


@dataclass(frozen=True, slots=True)
class HeterogeneousWorld:
    seed: int
    n_robots: int
    n_loads: int
    heterogeneity: str
    demand_ratio: float
    geometry: str
    graph: str
    robot_capacity: np.ndarray
    battery: np.ndarray
    robot_positions: np.ndarray
    load_positions: np.ndarray
    effective_capacity: np.ndarray
    demand: np.ndarray
    reward: np.ndarray
    cost: np.ndarray
    adjacency: np.ndarray
    mixing: np.ndarray
    lambda2: float
    world_hash: str


@dataclass(slots=True)
class PopulationResult:
    x: np.ndarray
    initial_x: np.ndarray
    iterations: int
    converged: bool
    residual: float
    potential_initial: float
    potential_final: float
    potential_violations: int
    simplex_error: float
    messages: int
    runtime_s: float
    potential_history: list[float]


@dataclass(frozen=True, slots=True)
class AssignmentMetrics:
    integer_valid: bool
    served_rate: float
    coverage_ratio: float
    under_capacity: float
    over_capacity_ratio: float
    distance_cost: float
    objective_value: float
    normalized_regret: float


def _adjacency(n: int, graph: str) -> np.ndarray:
    if graph == "complete":
        return np.ones((n, n), dtype=float) - np.eye(n)
    if graph == "ring":
        a = np.zeros((n, n), dtype=float)
        for i in range(n):
            a[i, (i - 1) % n] = 1.0
            a[i, (i + 1) % n] = 1.0
        return a
    raise ValueError(f"Unknown graph: {graph}")


def _mixing(adjacency: np.ndarray) -> np.ndarray:
    degree = adjacency.sum(axis=1)
    w = np.zeros_like(adjacency)
    for i in range(len(adjacency)):
        for j in np.flatnonzero(adjacency[i]):
            w[i, j] = 1.0 / (1.0 + max(degree[i], degree[j]))
        w[i, i] = 1.0 - w[i].sum()
    return w


def make_heterogeneous_world(
    *, seed: int, n_robots: int, n_loads: int, heterogeneity: str,
    demand_ratio: float, geometry: str, graph: str,
) -> HeterogeneousWorld:
    rng = np.random.default_rng(seed)
    if geometry == "uniform":
        robots = rng.uniform(0.0, 20.0, size=(n_robots, 2))
        loads = rng.uniform(0.0, 20.0, size=(n_loads, 2))
    elif geometry == "clustered":
        centers = np.array([[5.0, 5.0], [15.0, 15.0]])
        robots = centers[np.arange(n_robots) % 2] + rng.normal(0.0, 2.0, size=(n_robots, 2))
        loads = centers[np.arange(n_loads) % 2] + rng.normal(0.0, 2.5, size=(n_loads, 2))
        robots = np.clip(robots, 0.0, 20.0)
        loads = np.clip(loads, 0.0, 20.0)
    else:
        raise ValueError(f"Unknown geometry: {geometry}")
    sigma = {"low": 0.15, "high": 0.55}[heterogeneity]
    capacity = rng.lognormal(0.0, sigma, n_robots)
    capacity /= capacity.mean()
    capacity = np.clip(capacity, 0.35, 2.25)
    battery = rng.uniform(0.45, 1.0, n_robots)
    distance = np.linalg.norm(robots[:, None, :] - loads[None, :, :], axis=2)
    cost = distance / max(float(distance.max()), 1.0)
    pair_factor = rng.uniform(0.82, 1.0, size=(n_robots, n_loads))
    effective = capacity[:, None] * (0.55 + 0.45 * battery[:, None])
    effective = effective * (0.65 + 0.35 * np.exp(-2.0 * cost)) * pair_factor
    available = float(np.sum(np.max(effective, axis=1)))
    weights = rng.lognormal(0.0, 0.42, n_loads)
    weights /= weights.sum()
    demand = np.maximum(demand_ratio * available * weights, 0.2)
    reward = 1.0 + 0.35 * demand / max(float(demand.mean()), 1.0e-9)
    adjacency = _adjacency(n_robots, graph)
    mixing = _mixing(adjacency)
    laplacian = np.diag(adjacency.sum(axis=1)) - adjacency
    eigenvalues = np.sort(np.linalg.eigvalsh(laplacian))
    lambda2 = float(eigenvalues[1]) if n_robots > 1 else 0.0
    payload = {
        "seed": seed, "n_robots": n_robots, "n_loads": n_loads,
        "heterogeneity": heterogeneity, "demand_ratio": demand_ratio,
        "geometry": geometry, "graph": graph,
        "capacity": np.round(capacity, 10).tolist(),
        "demand": np.round(demand, 10).tolist(),
        "positions": np.round(robots, 10).tolist(),
    }
    world_hash = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]
    return HeterogeneousWorld(
        seed, n_robots, n_loads, heterogeneity, demand_ratio, geometry, graph,
        capacity, battery, robots, loads, effective, demand, reward, cost,
        adjacency, mixing, lambda2, world_hash,
    )


def potential(world: HeterogeneousWorld, x: np.ndarray, *, fitness_mode: str,
              alpha: float, beta: float, epsilon: float) -> float:
    if fitness_mode not in ALIGNED_FITNESS:
        return math.nan
    supplied = np.sum(world.effective_capacity * x[:, 1:], axis=0)
    ratio = supplied / world.demand
    if fitness_mode == "marginal_deficit":
        utility = np.where(ratio <= 1.0, ratio - 0.5 * ratio**2, 0.5)
    else:
        utility = np.log(epsilon + ratio)
    return alpha * float(np.sum(world.reward * utility)) - beta * float(np.sum(world.cost * x[:, 1:]))


def fitness(world: HeterogeneousWorld, x: np.ndarray, *, fitness_mode: str,
            alpha: float, beta: float, epsilon: float, consensus_rounds: int) -> tuple[np.ndarray, int]:
    local = world.effective_capacity * x[:, 1:]
    estimate = local.copy()
    rounds = 1 if world.graph == "complete" else max(1, int(consensus_rounds))
    for _ in range(rounds):
        estimate = world.mixing @ estimate
    supplied = world.n_robots * estimate
    ratio = supplied / world.demand[None, :]
    if fitness_mode == "plain_deficit":
        load_values = alpha * world.reward[None, :] * np.maximum(1.0 - ratio, 0.0) - beta * world.cost
    elif fitness_mode == "marginal_deficit":
        marginal = world.effective_capacity / world.demand[None, :]
        load_values = alpha * world.reward[None, :] * marginal * np.maximum(1.0 - ratio, 0.0) - beta * world.cost
    elif fitness_mode == "marginal_log":
        marginal = world.effective_capacity / world.demand[None, :]
        load_values = alpha * world.reward[None, :] * marginal / (epsilon + ratio) - beta * world.cost
    else:
        raise ValueError(f"Unknown fitness: {fitness_mode}")
    values = np.zeros((world.n_robots, world.n_loads + 1), dtype=float)
    values[:, 1:] = load_values
    edges = int(world.adjacency.sum() / 2)
    return values, rounds * 2 * edges * world.n_loads


def run_population(
    world: HeterogeneousWorld, *, protocol: str, fitness_mode: str, seed: int,
    alpha: float, beta: float, epsilon: float, dt: float, max_steps: int,
    tolerance: float, stable_steps: int, consensus_rounds: int,
) -> PopulationResult:
    rng = np.random.default_rng(seed)
    x = project_rows(np.full((world.n_robots, world.n_loads + 1), 1.0 / (world.n_loads + 1))
                     + rng.normal(0.0, 0.01, (world.n_robots, world.n_loads + 1)))
    initial = x.copy()
    history = [potential(world, x, fitness_mode=fitness_mode, alpha=alpha, beta=beta, epsilon=epsilon)]
    violations = messages = stable = 0
    converged = False
    residual = math.inf
    start = perf_counter()
    protocol_field = "BNN" if protocol == "erv_bnn" else protocol.upper()
    for step in range(1, max_steps + 1):
        values, step_messages = fitness(
            world, x, fitness_mode=fitness_mode, alpha=alpha, beta=beta,
            epsilon=epsilon, consensus_rounds=consensus_rounds,
        )
        messages += step_messages
        field = vector_field(x, values, protocol_field)
        residual = float(np.max(np.abs(field)))
        scale = np.maximum(1.0, np.max(np.abs(field), axis=1, keepdims=True))
        step_size = dt
        previous = history[-1]
        for _backtrack in range(14):
            candidate = project_rows(x + step_size * field / scale)
            current = potential(
                world, candidate, fitness_mode=fitness_mode,
                alpha=alpha, beta=beta, epsilon=epsilon,
            )
            exact_potential = world.graph == "complete" and fitness_mode in ALIGNED_FITNESS
            if not exact_potential or current >= previous - 1.0e-12:
                break
            step_size *= 0.5
        x = candidate
        if np.isfinite(current) and current < history[-1] - 1.0e-9:
            violations += 1
        history.append(current)
        stable = stable + 1 if residual <= tolerance else 0
        if stable >= stable_steps:
            converged = True
            break
    return PopulationResult(
        x=x, initial_x=initial, iterations=step, converged=converged, residual=residual,
        potential_initial=history[0], potential_final=history[-1],
        potential_violations=violations,
        simplex_error=float(np.max(np.abs(x.sum(axis=1) - 1.0))),
        messages=messages, runtime_s=perf_counter() - start, potential_history=history,
    )


def raw_decode(preferences: np.ndarray) -> np.ndarray:
    return np.argmax(preferences, axis=1).astype(int)


def preference_closure(world: HeterogeneousWorld, preferences: np.ndarray) -> np.ndarray:
    labels = np.zeros(world.n_robots, dtype=int)
    residual = world.demand.copy()
    available = np.ones(world.n_robots, dtype=bool)
    for _ in range(world.n_robots):
        best: tuple[float, int, int] | None = None
        for i in np.flatnonzero(available):
            gain = np.minimum(world.effective_capacity[i], residual) / world.demand
            score = 1.8 * preferences[i, 1:] + 1.2 * world.reward * gain - 0.22 * world.cost[i]
            k = int(np.argmax(score))
            value = float(score[k])
            if best is None or value > best[0]:
                best = (value, int(i), k)
        if best is None or best[0] <= 0.0:
            break
        _, i, k = best
        labels[i] = k + 1
        residual[k] = max(0.0, residual[k] - world.effective_capacity[i, k])
        available[i] = False
        if np.all(residual <= 1.0e-9):
            break
    return labels


def greedy_capacity(world: HeterogeneousWorld) -> np.ndarray:
    pref = np.zeros((world.n_robots, world.n_loads + 1), dtype=float)
    pref[:, 1:] = world.effective_capacity / world.demand[None, :] - 0.35 * world.cost
    return preference_closure(world, project_rows(np.maximum(pref, 0.0) + 1.0e-6))


def auction_capacity(world: HeterogeneousWorld) -> np.ndarray:
    labels = np.zeros(world.n_robots, dtype=int)
    residual = world.demand.copy()
    available = np.ones(world.n_robots, dtype=bool)
    for _ in range(world.n_robots):
        best: tuple[float, int, int] | None = None
        for i in np.flatnonzero(available):
            gain = np.minimum(world.effective_capacity[i], residual) / world.demand
            bids = world.reward * gain - 0.28 * world.cost[i]
            k = int(np.argmax(bids))
            candidate = (float(bids[k]), int(i), k)
            if best is None or candidate[0] > best[0]:
                best = candidate
        if best is None or best[0] <= 0.0:
            break
        _, i, k = best
        labels[i] = k + 1
        residual[k] = max(0.0, residual[k] - world.effective_capacity[i, k])
        available[i] = False
    return labels


def milp_exact(world: HeterogeneousWorld, *, partial_weight: float, distance_weight: float) -> np.ndarray:
    n, k = world.n_robots, world.n_loads
    nx, ny, nz = n * k, k, k
    c = np.zeros(nx + ny + nz)
    c[:nx] = distance_weight * world.cost.ravel()
    c[nx:nx + ny] = -world.reward
    c[nx + ny:] = -partial_weight * world.reward
    integrality = np.zeros_like(c, dtype=int)
    integrality[:nx + ny] = 1
    lower = np.zeros_like(c)
    upper = np.ones_like(c)
    constraints: list[LinearConstraint] = []
    for i in range(n):
        row = np.zeros_like(c)
        row[i * k:(i + 1) * k] = 1.0
        constraints.append(LinearConstraint(row, -np.inf, 1.0))
    for load in range(k):
        full = np.zeros_like(c)
        full[load:nx:k] = world.effective_capacity[:, load]
        full[nx + load] = -world.demand[load]
        constraints.append(LinearConstraint(full, 0.0, np.inf))
        cover = np.zeros_like(c)
        cover[load:nx:k] = -world.effective_capacity[:, load] / world.demand[load]
        cover[nx + ny + load] = 1.0
        constraints.append(LinearConstraint(cover, -np.inf, 0.0))
    result = milp(
        c=c, integrality=integrality, bounds=Bounds(lower, upper), constraints=constraints,
        options={"time_limit": 5.0},
    )
    if not result.success or result.x is None:
        return auction_capacity(world)
    matrix = result.x[:nx].reshape(n, k)
    labels = np.zeros(n, dtype=int)
    for i in range(n):
        if matrix[i].max() > 0.5:
            labels[i] = int(np.argmax(matrix[i])) + 1
    return labels


def evaluate_assignment(
    world: HeterogeneousWorld, labels: np.ndarray, *, optimal_value: float | None,
    partial_weight: float, distance_weight: float,
) -> AssignmentMetrics:
    labels = np.asarray(labels, dtype=int)
    valid = bool(labels.shape == (world.n_robots,) and labels.min() >= 0 and labels.max() <= world.n_loads)
    supplied = np.zeros(world.n_loads)
    distance = 0.0
    if valid:
        for i, label in enumerate(labels):
            if label > 0:
                supplied[label - 1] += world.effective_capacity[i, label - 1]
                distance += world.cost[i, label - 1]
    coverage = np.minimum(supplied / world.demand, 1.0)
    completed = supplied + 1.0e-9 >= world.demand
    objective = float(np.sum(world.reward * completed) + partial_weight * np.sum(world.reward * coverage) - distance_weight * distance)
    regret = 0.0 if optimal_value is None else max(0.0, (optimal_value - objective) / max(abs(optimal_value), 1.0))
    return AssignmentMetrics(
        integer_valid=valid, served_rate=float(completed.mean()), coverage_ratio=float(coverage.mean()),
        under_capacity=float(np.maximum(world.demand - supplied, 0.0).sum()),
        over_capacity_ratio=float(np.maximum(supplied - world.demand, 0.0).sum() / world.demand.sum()),
        distance_cost=distance, objective_value=objective, normalized_regret=regret,
    )


def _write_table(frame: pd.DataFrame, prefix: Path) -> None:
    frame.to_csv(prefix.with_suffix(".csv"), index=False)
    frame.to_parquet(prefix.with_suffix(".parquet"), index=False)


def _holm(values: Iterable[float]) -> list[float]:
    raw = np.asarray(list(values), dtype=float)
    order = np.argsort(raw)
    adjusted = np.empty_like(raw)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, min(1.0, (len(raw) - rank) * raw[idx]))
        adjusted[idx] = running
    return adjusted.tolist()


def _bootstrap(values: np.ndarray, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(2500, len(values)))
    means = values[indices].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def _hypotheses(runs: pd.DataFrame) -> pd.DataFrame:
    comparisons = [
        ("smith__marginal_deficit", "smith__plain_deficit"),
        ("replicator__marginal_deficit", "replicator__plain_deficit"),
        ("erv_bnn__marginal_deficit", "erv_bnn__plain_deficit"),
        ("smith__marginal_log", "smith__plain_deficit"),
        ("replicator__marginal_log", "replicator__plain_deficit"),
        ("erv_bnn__marginal_log", "erv_bnn__plain_deficit"),
        ("erv_bnn__marginal_log", "smith__marginal_log"),
        ("erv_bnn__marginal_log", "replicator__marginal_log"),
        ("erv_bnn__marginal_log", "greedy_capacity"),
        ("erv_bnn__marginal_log", "auction_capacity"),
        ("erv_bnn__marginal_log", "milp_exact"),
    ]
    available = set(runs.method)
    comparisons = [(candidate, reference) for candidate, reference in comparisons
                   if candidate in available and reference in available]
    rows = []
    for index, (candidate, reference) in enumerate(comparisons, 1):
        left = runs[runs.method == candidate][["world_hash", "normalized_regret"]].rename(columns={"normalized_regret": "left"})
        right = runs[runs.method == reference][["world_hash", "normalized_regret"]].rename(columns={"normalized_regret": "right"})
        merged = left.merge(right, on="world_hash", validate="one_to_one")
        diff = merged.left.to_numpy() - merged.right.to_numpy()
        nonzero = diff[np.abs(diff) > 1.0e-14]
        p = float(wilcoxon(nonzero).pvalue) if len(nonzero) else 1.0
        low, high = _bootstrap(diff, 72100 + index)
        rows.append({
            "id": f"H-SP2-{index}", "candidate": candidate, "reference": reference,
            "metric": "normalized_regret", "n_pairs": len(diff),
            "effect_mean_paired": float(diff.mean()), "ci95_low": low, "ci95_high": high,
            "p_value_raw": max(p, np.finfo(float).tiny),
            "interpretation": "candidate_better" if high < 0 else "reference_better" if low > 0 else "inconclusive",
        })
    adjusted = _holm(row["p_value_raw"] for row in rows)
    for row, value in zip(rows, adjusted, strict=True):
        row["p_value_holm"] = value
        row["reject_holm_005"] = value < 0.05
    return pd.DataFrame(rows)


def _summarize(runs: pd.DataFrame) -> pd.DataFrame:
    return runs.groupby("method", as_index=False).agg(
        n=("world_hash", "nunique"), served_rate_mean=("final_served_rate", "mean"),
        coverage_mean=("final_coverage_ratio", "mean"), regret_mean=("normalized_regret", "mean"),
        regret_std=("normalized_regret", "std"), raw_served_rate_mean=("raw_served_rate", "mean"),
        convergence_rate=("continuous_converged", "mean"), potential_gain_mean=("potential_gain", "mean"),
        messages_mean=("messages", "mean"), runtime_s_mean=("runtime_s", "mean"),
    ).sort_values(["regret_mean", "method"])


def _audit(runs: pd.DataFrame) -> dict[str, Any]:
    population = runs[runs.method.isin(POPULATION_METHODS)]
    aligned_complete = population[(population.fitness_mode.isin(ALIGNED_FITNESS)) & (population.graph == "complete")]
    plain = population[population.fitness_mode == "plain_deficit"]
    checks = {
        "simplex_invariant": bool((population.simplex_error <= 1.0e-10).all()),
        "finite_residuals": bool(np.isfinite(population.equilibrium_residual).all()),
        "integer_assignments_valid": bool(runs.final_integer_valid.all()),
        "raw_closed_separated": bool((runs.raw_served_rate != runs.final_served_rate).any()),
        "aligned_complete_potential_monotone": bool((aligned_complete.potential_violations == 0).all()),
        "plain_fitness_not_claimed_as_potential": bool(plain.potential_initial.isna().all()),
        "oracle_dominates": bool((runs.normalized_regret >= -1.0e-10).all()),
        "world_pairing": bool(runs.groupby("world_hash").method.nunique().nunique() == 1),
    }
    return {"passed": all(checks.values()), "checks": checks,
            "population_runs": len(population), "aligned_complete_runs": len(aligned_complete),
            "max_simplex_error": float(population.simplex_error.max()),
            "potential_violations": int(aligned_complete.potential_violations.sum())}


def _plots(runs: pd.DataFrame, summary: pd.DataFrame, histories: pd.DataFrame, output: Path) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    ordered = summary.sort_values("regret_mean")
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.bar(ordered.method, ordered.regret_mean, color="#4477AA")
    ax.set_ylabel("Regret normalizado medio")
    ax.tick_params(axis="x", rotation=55)
    fig.tight_layout(); fig.savefig(output / "sp2_heterogeneous_regret.png", dpi=220); plt.close(fig)
    games = runs[runs.method.isin(POPULATION_METHODS)].groupby(["protocol", "fitness_mode"], as_index=False).final_served_rate.mean()
    pivot = games.pivot(index="protocol", columns="fitness_mode", values="final_served_rate")
    fig, ax = plt.subplots(figsize=(7.8, 4.2)); image = ax.imshow(pivot, cmap="viridis", vmin=0, vmax=1)
    ax.set_xticks(range(len(pivot.columns)), pivot.columns, rotation=25, ha="right")
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            ax.text(j, i, f"{pivot.iloc[i,j]:.3f}", ha="center", va="center", color="white")
    fig.colorbar(image, ax=ax, label="Tasa de cargas servidas")
    fig.tight_layout(); fig.savefig(output / "sp2_fitness_protocol_heatmap.png", dpi=220); plt.close(fig)
    if not histories.empty:
        chosen = histories.world_hash.iloc[0]
        fig, ax = plt.subplots(figsize=(8, 4.4))
        for method, group in histories[histories.world_hash == chosen].groupby("method"):
            ax.plot(group.step, group.potential, label=method)
        ax.set_xlabel("Iteración"); ax.set_ylabel("Potencial"); ax.legend(frameon=False, fontsize=7)
        fig.tight_layout(); fig.savefig(output / "sp2_potential.png", dpi=220); plt.close(fig)
    graph = runs[runs.method.isin(POPULATION_METHODS)].groupby(["fitness_mode", "graph"], as_index=False).normalized_regret.mean()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for name, group in graph.groupby("graph"):
        ax.plot(group.fitness_mode, group.normalized_regret, marker="o", label=name)
    ax.set_ylabel("Regret normalizado"); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(output / "sp2_graph_effect.png", dpi=220); plt.close(fig)


def run_heterogeneous_campaign(config_path: str | Path) -> dict[str, Any]:
    config_path = Path(config_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8-sig"))
    output = Path(config["output_dir"]); tables = output / "tables"; figures = output / "figures"
    tables.mkdir(parents=True, exist_ok=True); figures.mkdir(parents=True, exist_ok=True)
    factors = config["factors"]; pop = config["population"]; objective = config["objective"]
    methods = tuple(config.get("methods", ALL_METHODS)); rows = []; raw_rows = []; closed_rows = []; history_rows = []
    world_index = 0
    for n in factors["n_robots"]:
        for k in factors["n_loads"]:
            for heterogeneity in factors["heterogeneity"]:
                for demand_ratio in factors["demand_ratio"]:
                    for geometry in factors["geometry"]:
                        for graph in factors["graph"]:
                            for replicate in range(int(config["replicates_per_cell"])):
                                seed = int(config["base_seed"]) + world_index; world_index += 1
                                world = make_heterogeneous_world(seed=seed, n_robots=int(n), n_loads=int(k),
                                    heterogeneity=heterogeneity, demand_ratio=float(demand_ratio), geometry=geometry, graph=graph)
                                oracle_start = perf_counter()
                                oracle_labels = milp_exact(world, partial_weight=float(objective["partial_weight"]), distance_weight=float(objective["distance_weight"]))
                                oracle_runtime_s = perf_counter() - oracle_start
                                oracle_metrics = evaluate_assignment(world, oracle_labels, optimal_value=None,
                                    partial_weight=float(objective["partial_weight"]), distance_weight=float(objective["distance_weight"]))
                                for method_index, method in enumerate(methods):
                                    start = perf_counter(); population = None; protocol = fitness_mode = "none"
                                    if method in POPULATION_METHODS:
                                        protocol, fitness_mode = method.split("__", 1)
                                        population = run_population(world, protocol=protocol, fitness_mode=fitness_mode,
                                            seed=seed * 101 + method_index, alpha=float(pop["alpha"]), beta=float(pop["beta"]),
                                            epsilon=float(pop["epsilon"]), dt=float(pop["dt"]), max_steps=int(pop["max_steps"]),
                                            tolerance=float(pop["tolerance"]), stable_steps=int(pop["stable_steps"]),
                                            consensus_rounds=int(pop["consensus_rounds"]))
                                        preferences = population.x; raw = raw_decode(preferences); labels = preference_closure(world, preferences)
                                    elif method == "uniform_closure":
                                        preferences = np.full((world.n_robots, world.n_loads + 1), 1.0 / (world.n_loads + 1)); raw = raw_decode(preferences); labels = preference_closure(world, preferences)
                                    elif method == "random_closure":
                                        preferences = np.random.default_rng(seed * 101 + method_index).dirichlet(np.ones(world.n_loads + 1), world.n_robots); raw = raw_decode(preferences); labels = preference_closure(world, preferences)
                                    elif method == "greedy_capacity":
                                        labels = greedy_capacity(world); raw = labels.copy()
                                    elif method == "auction_capacity":
                                        labels = auction_capacity(world); raw = labels.copy()
                                    elif method == "milp_exact":
                                        labels = oracle_labels.copy(); raw = labels.copy()
                                    else:
                                        raise ValueError(f"Unknown method: {method}")
                                    raw_metrics = evaluate_assignment(world, raw, optimal_value=oracle_metrics.objective_value,
                                        partial_weight=float(objective["partial_weight"]), distance_weight=float(objective["distance_weight"]))
                                    final_metrics = evaluate_assignment(world, labels, optimal_value=oracle_metrics.objective_value,
                                        partial_weight=float(objective["partial_weight"]), distance_weight=float(objective["distance_weight"]))
                                    common = {"experiment_id": config["experiment_id"], "world_hash": world.world_hash,
                                        "seed": seed, "replicate": replicate, "n_robots": n, "n_loads": k,
                                        "heterogeneity": heterogeneity, "demand_ratio": demand_ratio, "geometry": geometry,
                                        "graph": graph, "lambda2": world.lambda2, "method": method,
                                        "protocol": protocol, "fitness_mode": fitness_mode}
                                    rows.append({**common, "raw_served_rate": raw_metrics.served_rate,
                                        "raw_coverage_ratio": raw_metrics.coverage_ratio,
                                        "final_integer_valid": final_metrics.integer_valid,
                                        "final_served_rate": final_metrics.served_rate,
                                        "final_coverage_ratio": final_metrics.coverage_ratio,
                                        "under_capacity": final_metrics.under_capacity,
                                        "over_capacity_ratio": final_metrics.over_capacity_ratio,
                                        "distance_cost": final_metrics.distance_cost,
                                        "objective_value": final_metrics.objective_value,
                                        "optimal_objective": oracle_metrics.objective_value,
                                        "normalized_regret": final_metrics.normalized_regret,
                                        "continuous_converged": bool(population.converged) if population else True,
                                        "iterations": population.iterations if population else 0,
                                        "equilibrium_residual": population.residual if population else 0.0,
                                        "simplex_error": population.simplex_error if population else 0.0,
                                        "potential_initial": population.potential_initial if population else math.nan,
                                        "potential_final": population.potential_final if population else math.nan,
                                        "potential_gain": (population.potential_final - population.potential_initial) if population and np.isfinite(population.potential_initial) else math.nan,
                                        "potential_violations": population.potential_violations if population else 0,
                                        "messages": population.messages if population else world.n_robots * world.n_loads,
                                        "runtime_s": population.runtime_s if population else oracle_runtime_s if method == "milp_exact" else perf_counter() - start,
                                        "runtime_scope": "population_solver" if population else "centralized_milp_solver" if method == "milp_exact" else "method_only"})
                                    for i, label in enumerate(raw): raw_rows.append({**common, "robot": i, "label": int(label)})
                                    for i, label in enumerate(labels): closed_rows.append({**common, "robot": i, "label": int(label)})
                                    if population and graph == "complete" and fitness_mode in ALIGNED_FITNESS and replicate == 0 and n == factors["n_robots"][0] and k == factors["n_loads"][0] and heterogeneity == factors["heterogeneity"][0] and float(demand_ratio) == float(factors["demand_ratio"][0]) and geometry == factors["geometry"][0]:
                                        for step, value in enumerate(population.potential_history): history_rows.append({**common, "step": step, "potential": value})
    runs = pd.DataFrame(rows); summary = _summarize(runs); hypotheses = _hypotheses(runs); audit = _audit(runs)
    _write_table(runs, tables / "runs"); _write_table(summary, tables / "summary")
    _write_table(hypotheses, tables / "hypothesis_results"); _write_table(pd.DataFrame(raw_rows), tables / "assignments_raw")
    _write_table(pd.DataFrame(closed_rows), tables / "assignments_closed")
    histories = pd.DataFrame(history_rows); _write_table(histories, tables / "potential_histories")
    _plots(runs, summary, histories, figures)
    manifest = {"experiment_id": config["experiment_id"], "status": "completed", "worlds": int(runs.world_hash.nunique()),
        "runs": len(runs), "methods": list(methods), "confirmatory": bool(config.get("confirmatory", False)),
        "seeds_opened": [int(config["base_seed"]), int(config["base_seed"]) + int(runs.world_hash.nunique()) - 1],
        "theory_audit_passed": bool(audit["passed"]), "config_path": str(config_path),
        "config_hash": sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "theory_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    report = [f"# {config['experiment_id']}", "", f"- Worlds: `{manifest['worlds']}`", f"- Runs: `{manifest['runs']}`",
        f"- Theory audit: `{'PASS' if audit['passed'] else 'FAIL'}`", "", "## Summary", "", summary.to_markdown(index=False, floatfmt=".5g"),
        "", "## Hypotheses", "", hypotheses.to_markdown(index=False, floatfmt=".5g"), "", "## Interpretation", "",
        "- Fitness and revision protocols are crossed factorially.", "- Plain deficit fitness is a heuristic under pair-dependent capacity.",
        "- RAW preferences, capacity closure, and the MILP oracle are separate stages.", "- Ring results are sensitivity evidence, not a time-varying-graph theorem."]
    (output / "report.md").write_text("\n".join(report), encoding="utf-8")
    return {"manifest": manifest, "audit": audit, "summary": summary, "hypotheses": hypotheses}


__all__ = ["ALL_METHODS", "FITNESS_MODES", "PROTOCOLS", "HeterogeneousWorld", "evaluate_assignment",
           "fitness", "make_heterogeneous_world", "milp_exact", "potential", "preference_closure",
           "run_heterogeneous_campaign", "run_population"]

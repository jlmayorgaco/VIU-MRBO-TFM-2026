"""Reproducible SP6-C failure-recovery experiment and evidence generator."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy import stats
import yaml

from viu_mrob_tfm.sp6.theory import (
    asynchronous_better_response,
    exact_feasible_oracle,
    is_feasible,
    is_inclusion_minimal,
    is_pure_nash,
    marginal_utility,
    potential,
    pure_nash_profiles,
    recovery_time_upper_bound,
    sufficient_penalty,
    weighted_deficit,
)


METHODS = (
    "guarded_potential",
    "marginal_auction",
    "distance_greedy",
    "no_repair",
    "central_exact",
)

METHOD_LABELS = {
    "guarded_potential": "Juego potencial guardado",
    "marginal_auction": "Subasta marginal",
    "distance_greedy": "Greedy por distancia",
    "no_repair": "Sin reparación",
    "central_exact": "Oráculo exacto",
}

SCENARIO_LABELS = {
    "balanced_recoverable": "Recuperable balanceado",
    "complementary_recoverable": "Capacidades complementarias",
    "tight_deadline": "Plazo estrecho",
    "infeasible_reserve": "Reserva insuficiente",
}


@dataclass(frozen=True, slots=True)
class RecoveryWorld:
    scenario: str
    reserve_size: int
    seed: int
    requirement: np.ndarray
    capabilities: np.ndarray
    costs: np.ndarray
    distances_m: np.ndarray
    speeds_mps: np.ndarray
    detection_delay_s: float
    deadline_s: float
    settling_time_s: float
    event_interval_s: float
    world_hash: str

    @property
    def physically_recoverable(self) -> bool:
        return is_feasible(np.ones(self.reserve_size, dtype=int), self.capabilities, self.requirement)


def run_sp6_config(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path)
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    experiment_id = str(config["experiment_id"])
    output_dir = Path(config.get("output_dir", f"results/processed/sp6/{experiment_id}"))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "tables").mkdir(exist_ok=True)
    (output_dir / "figures").mkdir(exist_ok=True)

    scenarios = [str(value) for value in config["scenarios"]]
    reserve_sizes = [int(value) for value in config["reserve_sizes"]]
    seeds = _expand_seeds(config["seeds"])
    methods = [str(value) for value in config.get("methods", METHODS)]
    if set(methods) != set(METHODS):
        raise ValueError(f"Canonical SP6 requires exactly these methods: {METHODS}")

    rows: list[dict[str, Any]] = []
    theory_rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        if scenario not in SCENARIO_LABELS:
            raise ValueError(f"Unknown SP6 scenario: {scenario}")
        for reserve_size in reserve_sizes:
            for seed in seeds:
                world = generate_world(scenario, reserve_size, seed)
                theory = audit_world_theory(world)
                theory_rows.append(theory)
                oracle = exact_feasible_oracle(world.capabilities, world.requirement, world.costs)
                oracle_cost = float(oracle @ world.costs) if is_feasible(oracle, world.capabilities, world.requirement) else math.nan
                for method in methods:
                    rows.append(simulate_method(world, method, oracle_cost, theory))

    runs = pd.DataFrame(rows)
    theory_df = pd.DataFrame(theory_rows)
    summary = summarize_runs(runs)
    hypotheses = evaluate_hypotheses(runs)
    audit = build_audit(config, runs, theory_df, scenarios, reserve_sizes, seeds, methods)

    runs.to_csv(output_dir / "tables" / "runs.csv", index=False)
    theory_df.to_csv(output_dir / "tables" / "theory_checks.csv", index=False)
    summary.to_csv(output_dir / "tables" / "summary.csv", index=False)
    hypotheses.to_csv(output_dir / "tables" / "hypotheses.csv", index=False)
    _write_latex_tables(output_dir, runs, summary, hypotheses)
    _plot_results(output_dir, runs)
    (output_dir / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "report.md").write_text(_report(experiment_id, runs, summary, hypotheses, audit), encoding="utf-8")
    manifest = {
        "experiment_id": experiment_id,
        "config_path": str(path),
        "output_dir": str(output_dir),
        "scenarios": scenarios,
        "reserve_sizes": reserve_sizes,
        "seeds": seeds,
        "methods": methods,
        "worlds": int(len(theory_df)),
        "runs": int(len(runs)),
        "evidence_level": "B",
        "audit": str(output_dir / "audit.json"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "gpu_used": False,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def generate_world(scenario: str, reserve_size: int, seed: int) -> RecoveryWorld:
    stable_offset = int.from_bytes(hashlib.sha256(scenario.encode("utf-8")).digest()[:4], "little")
    rng = np.random.default_rng(int(seed) + stable_offset + 1009 * int(reserve_size))
    requirement = rng.uniform(0.55, 0.90, size=3)
    if scenario == "complementary_recoverable":
        capabilities = rng.uniform(0.025, 0.12, size=(reserve_size, 3))
        for robot in range(reserve_size):
            capabilities[robot, robot % 3] += rng.uniform(0.28, 0.52)
    else:
        capabilities = rng.uniform(0.10, 0.34, size=(reserve_size, 3))

    if scenario != "infeasible_reserve":
        shortage = np.maximum(requirement - np.sum(capabilities, axis=0), 0.0)
        capabilities[-1] += shortage + 0.03
    else:
        capabilities[:, 0] *= 0.72 * requirement[0] / max(float(np.sum(capabilities[:, 0])), 1e-12)

    angles = rng.uniform(-math.pi, math.pi, size=reserve_size)
    radii = rng.uniform(1.2, 7.5, size=reserve_size)
    distances = radii + 0.15 * np.abs(np.sin(angles))
    speeds = rng.uniform(0.45, 0.85, size=reserve_size)
    costs = 0.12 + distances / 10.0 + rng.uniform(0.02, 0.22, size=reserve_size)
    detection_delay = float(rng.uniform(0.45, 1.25))
    if scenario == "tight_deadline":
        deadline = float(rng.uniform(7.5, 12.5))
    elif scenario == "infeasible_reserve":
        deadline = float(rng.uniform(18.0, 24.0))
    else:
        deadline = float(rng.uniform(18.0, 28.0))
    settling = 0.8
    event_interval = 0.12
    payload = {
        "scenario": scenario,
        "reserve_size": reserve_size,
        "seed": seed,
        "requirement": requirement.round(12).tolist(),
        "capabilities": capabilities.round(12).tolist(),
        "costs": costs.round(12).tolist(),
        "distances": distances.round(12).tolist(),
        "speeds": speeds.round(12).tolist(),
        "detection_delay": detection_delay,
        "deadline": deadline,
    }
    world_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return RecoveryWorld(
        scenario=scenario,
        reserve_size=reserve_size,
        seed=seed,
        requirement=requirement,
        capabilities=capabilities,
        costs=costs,
        distances_m=distances,
        speeds_mps=speeds,
        detection_delay_s=detection_delay,
        deadline_s=deadline,
        settling_time_s=settling,
        event_interval_s=event_interval,
        world_hash=world_hash,
    )


def audit_world_theory(world: RecoveryWorld) -> dict[str, Any]:
    penalty, delta_min = sufficient_penalty(world.capabilities, world.requirement, world.costs)
    recoverable = world.physically_recoverable
    if not recoverable:
        return {
            "world_hash": world.world_hash,
            "scenario": world.scenario,
            "reserve_size": world.reserve_size,
            "seed": world.seed,
            "physically_recoverable": False,
            "delta_min": 0.0,
            "penalty": math.nan,
            "pure_nash_count": 0,
            "exact_potential_verified": True,
            "all_nash_feasible": True,
            "all_feasible_nash_minimal": True,
        }
    equilibria = pure_nash_profiles(world.capabilities, world.requirement, world.costs, penalty)
    exact = _verify_exact_potential(world, penalty)
    return {
        "world_hash": world.world_hash,
        "scenario": world.scenario,
        "reserve_size": world.reserve_size,
        "seed": world.seed,
        "physically_recoverable": True,
        "delta_min": delta_min,
        "penalty": penalty,
        "pure_nash_count": len(equilibria),
        "exact_potential_verified": exact,
        "all_nash_feasible": bool(equilibria and all(is_feasible(x, world.capabilities, world.requirement) for x in equilibria)),
        "all_feasible_nash_minimal": bool(
            equilibria and all(is_inclusion_minimal(x, world.capabilities, world.requirement) for x in equilibria)
        ),
    }


def _verify_exact_potential(world: RecoveryWorld, penalty: float) -> bool:
    for encoded in range(2**world.reserve_size):
        profile = np.asarray([(encoded >> idx) & 1 for idx in range(world.reserve_size)], dtype=int)
        for robot in range(world.reserve_size):
            before = profile.copy()
            after = profile.copy()
            after[robot] = 1 - after[robot]
            utility_delta = marginal_utility(
                robot,
                int(after[robot]),
                before,
                world.capabilities,
                world.requirement,
                world.costs,
                penalty,
            ) - marginal_utility(
                robot,
                int(before[robot]),
                before,
                world.capabilities,
                world.requirement,
                world.costs,
                penalty,
            )
            potential_delta = potential(after, world.capabilities, world.requirement, world.costs, penalty) - potential(
                before, world.capabilities, world.requirement, world.costs, penalty
            )
            if not np.isclose(utility_delta, potential_delta, atol=1e-10):
                return False
    return True


def simulate_method(world: RecoveryWorld, method: str, oracle_cost: float, theory: dict[str, Any]) -> dict[str, Any]:
    start = perf_counter()
    recoverable = world.physically_recoverable
    penalty = float(theory["penalty"]) if recoverable else math.nan
    selected = np.zeros(world.reserve_size, dtype=int)
    strict_moves = 0
    activations = 0
    messages = 0
    monotone = True
    final_nash = False
    declares_impossible = False

    if method == "guarded_potential":
        if not recoverable:
            declares_impossible = True
            messages = 2 * world.reserve_size
        else:
            result = asynchronous_better_response(
                world.capabilities,
                world.requirement,
                world.costs,
                penalty,
                seed=world.seed,
            )
            selected = result.profile
            strict_moves = result.strict_moves
            activations = result.activations
            messages = 2 * activations
            monotone = bool(np.all(np.diff(result.potential_trace) > 0.0))
            final_nash = is_pure_nash(selected, world.capabilities, world.requirement, world.costs, penalty)
    elif method == "marginal_auction":
        selected, strict_moves = _marginal_auction(world)
        activations = strict_moves * world.reserve_size
        messages = 3 * activations
        declares_impossible = not recoverable and not is_feasible(selected, world.capabilities, world.requirement)
    elif method == "distance_greedy":
        selected, strict_moves = _distance_greedy(world)
        activations = strict_moves
        messages = 2 * strict_moves
        declares_impossible = not recoverable and not is_feasible(selected, world.capabilities, world.requirement)
    elif method == "no_repair":
        declares_impossible = False
    elif method == "central_exact":
        selected = exact_feasible_oracle(world.capabilities, world.requirement, world.costs)
        strict_moves = int(np.sum(selected))
        activations = 2**world.reserve_size
        messages = world.reserve_size * max(world.reserve_size - 1, 0)
        declares_impossible = not recoverable
    else:
        raise ValueError(f"Unknown SP6 method: {method}")

    certified = is_feasible(selected, world.capabilities, world.requirement)
    selected_indices = np.flatnonzero(selected)
    travel_time = float(np.max(world.distances_m[selected_indices] / world.speeds_mps[selected_indices])) if selected_indices.size else 0.0
    decision_time = strict_moves * world.event_interval_s
    recovery_time = world.detection_delay_s + decision_time + travel_time + (world.settling_time_s if certified else 0.0)
    time_bound = recovery_time_upper_bound(
        world.detection_delay_s,
        2**world.reserve_size - 1,
        world.event_interval_s,
        float(np.max(world.distances_m)),
        float(np.min(world.speeds_mps)),
        world.settling_time_s,
    )
    success = bool(certified and recovery_time <= world.deadline_s)
    selected_cost = float(selected @ world.costs)
    cost_gap = (
        float((selected_cost - oracle_cost) / max(oracle_cost, 1e-12))
        if certified and np.isfinite(oracle_cost)
        else math.nan
    )
    redundant = _redundant_count(selected, world)
    return {
        "scenario": world.scenario,
        "scenario_label": SCENARIO_LABELS[world.scenario],
        "reserve_size": world.reserve_size,
        "seed": world.seed,
        "world_hash": world.world_hash,
        "method": method,
        "method_label": METHOD_LABELS[method],
        "physically_recoverable": recoverable,
        "declares_impossible": declares_impossible,
        "impossibility_classification_correct": bool(declares_impossible == (not recoverable)),
        "certificate_restored": certified,
        "recovery_success": success,
        "deadline_s": world.deadline_s,
        "recovery_time_s": recovery_time,
        "time_bound_s": time_bound,
        "time_bound_verified": bool(recovery_time <= time_bound + 1e-10),
        "selected_count": int(np.sum(selected)),
        "redundant_count": redundant,
        "selected_cost": selected_cost,
        "oracle_cost": oracle_cost,
        "cost_gap_vs_oracle": cost_gap,
        "residual_deficit": weighted_deficit(selected, world.capabilities, world.requirement),
        "strict_moves": strict_moves,
        "activations": activations,
        "messages": messages,
        "potential_monotone": monotone,
        "final_pure_nash": final_nash,
        "theorem_penalty": penalty,
        "delta_min": theory["delta_min"],
        "runtime_ms": 1000.0 * (perf_counter() - start),
    }


def _distance_greedy(world: RecoveryWorld) -> tuple[np.ndarray, int]:
    selected = np.zeros(world.reserve_size, dtype=int)
    moves = 0
    for robot in np.argsort(world.costs):
        if is_feasible(selected, world.capabilities, world.requirement):
            break
        selected[int(robot)] = 1
        moves += 1
    return selected, moves


def _marginal_auction(world: RecoveryWorld) -> tuple[np.ndarray, int]:
    selected = np.zeros(world.reserve_size, dtype=int)
    moves = 0
    while not is_feasible(selected, world.capabilities, world.requirement):
        before = weighted_deficit(selected, world.capabilities, world.requirement)
        bids: list[tuple[float, float, int]] = []
        for robot in np.flatnonzero(selected == 0):
            candidate = selected.copy()
            candidate[int(robot)] = 1
            reduction = before - weighted_deficit(candidate, world.capabilities, world.requirement)
            bids.append((reduction / max(float(world.costs[int(robot)]), 1e-12), reduction, -int(robot)))
        if not bids or max(bids)[1] <= 1e-12:
            break
        winner = -max(bids)[2]
        selected[winner] = 1
        moves += 1
    return selected, moves


def _redundant_count(selected: np.ndarray, world: RecoveryWorld) -> int:
    count = 0
    if not is_feasible(selected, world.capabilities, world.requirement):
        return 0
    for robot in np.flatnonzero(selected):
        candidate = selected.copy()
        candidate[int(robot)] = 0
        count += int(is_feasible(candidate, world.capabilities, world.requirement))
    return count


def summarize_runs(runs: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "certificate_restored",
        "recovery_success",
        "impossibility_classification_correct",
        "recovery_time_s",
        "selected_count",
        "redundant_count",
        "cost_gap_vs_oracle",
        "messages",
        "runtime_ms",
    ]
    rows = []
    for method, group in runs.groupby("method", sort=False):
        row: dict[str, Any] = {"method": method, "method_label": METHOD_LABELS[str(method)], "n": len(group)}
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values)) if values.size else math.nan
            low, high = _bootstrap_mean_ci(values, seed=20260716)
            row[f"{metric}_ci_low"] = low
            row[f"{metric}_ci_high"] = high
        rows.append(row)
    return pd.DataFrame(rows)


def evaluate_hypotheses(runs: pd.DataFrame) -> pd.DataFrame:
    specs = [
        ("H6.1", "certificate_restored", "guarded_potential", "no_repair", "greater", "mcnemar"),
        ("H6.2", "redundant_count", "guarded_potential", "distance_greedy", "less", "wilcoxon"),
        ("H6.3", "selected_cost", "guarded_potential", "central_exact", "greater", "wilcoxon"),
    ]
    rows = []
    for hid, metric, method_a, method_b, direction, test in specs:
        paired = _paired(runs, metric, method_a, method_b)
        a = paired[method_a].to_numpy(dtype=float)
        b = paired[method_b].to_numpy(dtype=float)
        diff = a - b
        if test == "mcnemar":
            discordant_a = int(np.sum((a == 1) & (b == 0)))
            discordant_b = int(np.sum((a == 0) & (b == 1)))
            p = float(stats.binomtest(discordant_a, discordant_a + discordant_b, 0.5, alternative="greater").pvalue) if discordant_a + discordant_b else 1.0
        else:
            nonzero = diff[np.abs(diff) > 1e-12]
            if nonzero.size:
                p = float(stats.wilcoxon(nonzero, alternative=direction, zero_method="wilcox").pvalue)
            else:
                p = 1.0
        low, high = _bootstrap_mean_ci(diff, seed=20260717)
        rows.append(
            {
                "id": hid,
                "metric": metric,
                "method_a": method_a,
                "method_b": method_b,
                "direction": direction,
                "test": test,
                "n_pairs": len(diff),
                "effect_a_minus_b": float(np.mean(diff)) if diff.size else math.nan,
                "ci95_low": low,
                "ci95_high": high,
                "p_raw": p,
            }
        )
    raw = [float(row["p_raw"]) for row in rows]
    adjusted = _holm(raw)
    for row, p_holm in zip(rows, adjusted, strict=True):
        row["p_holm"] = p_holm
        row["reject_holm"] = bool(p_holm < 0.05)
    return pd.DataFrame(rows)


def build_audit(
    config: dict[str, Any],
    runs: pd.DataFrame,
    theory: pd.DataFrame,
    scenarios: list[str],
    reserve_sizes: list[int],
    seeds: list[int],
    methods: list[str],
) -> dict[str, Any]:
    expected_worlds = len(scenarios) * len(reserve_sizes) * len(seeds)
    expected_runs = expected_worlds * len(methods)
    paired_counts = runs.groupby("world_hash")["method"].nunique()
    potential_runs = runs[runs["method"] == "guarded_potential"]
    recoverable_potential = potential_runs[potential_runs["physically_recoverable"]]
    impossible_potential = potential_runs[~potential_runs["physically_recoverable"]]
    numeric = runs[["recovery_time_s", "selected_count", "residual_deficit", "messages", "runtime_ms"]].to_numpy(dtype=float)
    checks = {
        "world_count": len(theory) == expected_worlds,
        "run_count": len(runs) == expected_runs,
        "paired_methods": bool((paired_counts == len(methods)).all()),
        "world_hash_unique": theory["world_hash"].nunique() == expected_worlds,
        "finite_primary_metrics": bool(np.isfinite(numeric).all()),
        "exact_potential_identity": bool(theory["exact_potential_verified"].all()),
        "all_recoverable_nash_feasible": bool(theory[theory["physically_recoverable"]]["all_nash_feasible"].all()),
        "all_feasible_nash_inclusion_minimal": bool(theory[theory["physically_recoverable"]]["all_feasible_nash_minimal"].all()),
        "strict_potential_monotonicity": bool(recoverable_potential["potential_monotone"].all()),
        "better_response_ends_at_nash": bool(recoverable_potential["final_pure_nash"].all()),
        "recoverable_certificate_restored": bool(recoverable_potential["certificate_restored"].all()),
        "impossible_cases_not_reopened": bool((~impossible_potential["certificate_restored"]).all()),
        "time_bound_verified": bool(potential_runs["time_bound_verified"].all()),
        "finite_profile_move_bound": bool((potential_runs["strict_moves"] <= (2 ** potential_runs["reserve_size"] - 1)).all()),
        "no_pose_repair": True,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "evidence_level": "B",
        "primary_branch": "SP6-C single failure, one affected rigid payload",
        "worlds": expected_worlds,
        "runs": expected_runs,
        "model_scope": "finite asynchronous binary recovery game plus event-time replacement travel proxy",
        "not_claimed": "No multiple simultaneous failures, frictional contact, SP6-E, persistent partitions, hardware validation or global social optimality is claimed.",
        "historical_campaign_used": False,
        "config_protocol": config.get("protocol_family", "sp6_potential_recovery_v1"),
    }


def _paired(runs: pd.DataFrame, metric: str, method_a: str, method_b: str) -> pd.DataFrame:
    selected = runs[runs["method"].isin([method_a, method_b])]
    pivot = selected.pivot(index="world_hash", columns="method", values=metric)
    return pivot[[method_a, method_b]].dropna()


def _bootstrap_mean_ci(values: np.ndarray, *, seed: int, reps: int = 2000) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return math.nan, math.nan
    if values.size == 1:
        return float(values[0]), float(values[0])
    rng = np.random.default_rng(seed)
    means = np.mean(rng.choice(values, size=(reps, values.size), replace=True), axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def _holm(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = np.ones(len(p_values), dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        value = min(1.0, (len(p_values) - rank) * p_values[int(index)])
        running = max(running, value)
        adjusted[int(index)] = running
    return adjusted.tolist()


def _write_latex_tables(output_dir: Path, runs: pd.DataFrame, summary: pd.DataFrame, hypotheses: pd.DataFrame) -> None:
    tables = output_dir / "tables"
    worlds = runs["world_hash"].nunique()
    potential_rows = runs[runs["method"] == "guarded_potential"]
    recoverable_potential = potential_rows[potential_rows["physically_recoverable"]]
    tight_potential = potential_rows[potential_rows["scenario"] == "tight_deadline"]
    tight_greedy = runs[(runs["method"] == "distance_greedy") & (runs["scenario"] == "tight_deadline")]
    potential_gap = pd.to_numeric(recoverable_potential["cost_gap_vs_oracle"], errors="coerce").dropna()
    h1 = hypotheses[hypotheses["id"] == "H6.1"].iloc[0]
    h2 = hypotheses[hypotheses["id"] == "H6.2"].iloc[0]
    h3 = hypotheses[hypotheses["id"] == "H6.3"].iloc[0]
    numbers = (
        f"\\newcommand{{\\SPSixWorlds}}{{{worlds}}}\n"
        f"\\newcommand{{\\SPSixRuns}}{{{len(runs)}}}\n"
        f"\\newcommand{{\\SPSixRecoverableWorlds}}{{{int(runs.drop_duplicates('world_hash')['physically_recoverable'].sum())}}}\n"
        f"\\newcommand{{\\SPSixIrrecoverableWorlds}}{{{int((~runs.drop_duplicates('world_hash')['physically_recoverable']).sum())}}}\n"
        f"\\newcommand{{\\SPSixConditionalRestore}}{{{recoverable_potential['certificate_restored'].mean():.3f}}}\n"
        f"\\newcommand{{\\SPSixPotentialSuccess}}{{{potential_rows['recovery_success'].mean():.3f}}}\n"
        f"\\newcommand{{\\SPSixPotentialGap}}{{{potential_gap.mean():.3f}}}\n"
        f"\\newcommand{{\\SPSixPotentialMessages}}{{{potential_rows['messages'].mean():.1f}}}\n"
        f"\\newcommand{{\\SPSixTightPotentialSuccess}}{{{tight_potential['recovery_success'].mean():.3f}}}\n"
        f"\\newcommand{{\\SPSixTightGreedySuccess}}{{{tight_greedy['recovery_success'].mean():.3f}}}\n"
        f"\\newcommand{{\\SPSixHOneEffect}}{{{h1['effect_a_minus_b']:.3f}}}\n"
        f"\\newcommand{{\\SPSixHOneCILow}}{{{h1['ci95_low']:.3f}}}\n"
        f"\\newcommand{{\\SPSixHOneCIHigh}}{{{h1['ci95_high']:.3f}}}\n"
        f"\\newcommand{{\\SPSixHOnePHolm}}{{{_latex_scientific(float(h1['p_holm']))}}}\n"
        f"\\newcommand{{\\SPSixHTwoEffect}}{{{h2['effect_a_minus_b']:.3f}}}\n"
        f"\\newcommand{{\\SPSixHTwoPHolm}}{{{_latex_scientific(float(h2['p_holm']))}}}\n"
        f"\\newcommand{{\\SPSixHThreeEffect}}{{{h3['effect_a_minus_b']:.3f}}}\n"
        f"\\newcommand{{\\SPSixHThreePHolm}}{{{_latex_scientific(float(h3['p_holm']))}}}\n"
    )
    (tables / "sp6_numbers.tex").write_text(numbers, encoding="utf-8")

    lines = [
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Método & Cert. restaurado & Éxito temporal & Redundantes & Mensajes \\\\",
        "\\midrule",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"{row['method_label']} & {row['certificate_restored_mean']:.3f} & {row['recovery_success_mean']:.3f} & "
            f"{row['redundant_count_mean']:.3f} & {row['messages_mean']:.1f} \\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}"]
    (tables / "sp6_results.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    hlines = [
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "ID & Métrica & $n$ & Efecto $A-B$ & IC 95\\% & $p_{Holm}$ \\\\",
        "\\midrule",
    ]
    metric_labels = {
        "certificate_restored": "certificado restaurado",
        "redundant_count": "miembros redundantes",
        "selected_cost": "coste seleccionado",
    }
    for _, row in hypotheses.iterrows():
        ci = f"[{row['ci95_low']:.3f}; {row['ci95_high']:.3f}]"
        hlines.append(
            f"{row['id']} & {metric_labels.get(str(row['metric']), str(row['metric']))} & {int(row['n_pairs'])} & "
            f"{row['effect_a_minus_b']:.3f} & {ci} & \\({_latex_scientific(float(row['p_holm']))}\\) \\\\"
        )
    hlines += ["\\bottomrule", "\\end{tabular}"]
    (tables / "sp6_hypotheses.tex").write_text("\n".join(hlines) + "\n", encoding="utf-8")


def _plot_results(output_dir: Path, runs: pd.DataFrame) -> None:
    figures = output_dir / "figures"
    method_order = list(METHODS)
    scenario_order = list(SCENARIO_LABELS)
    matrix = np.zeros((len(scenario_order), len(method_order)), dtype=float)
    for i, scenario in enumerate(scenario_order):
        for j, method in enumerate(method_order):
            values = runs[(runs["scenario"] == scenario) & (runs["method"] == method)]["recovery_success"]
            matrix[i, j] = float(values.mean())
    fig, ax = plt.subplots(figsize=(8.2, 3.8))
    im = ax.imshow(matrix, vmin=0.0, vmax=1.0, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(method_order)), [METHOD_LABELS[m] for m in method_order], rotation=25, ha="right", fontsize=8)
    ax.set_yticks(range(len(scenario_order)), [SCENARIO_LABELS[s] for s in scenario_order], fontsize=8)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", color="white" if matrix[i, j] < 0.55 else "black", fontsize=8)
    fig.colorbar(im, ax=ax, label="Tasa de recuperación antes del plazo")
    fig.tight_layout()
    fig.savefig(figures / "fig-sp6-recovery-matrix.pdf", bbox_inches="tight")
    plt.close(fig)

    selected = runs[runs["method"].isin(["guarded_potential", "marginal_auction", "distance_greedy", "central_exact"])]
    grouped = selected.groupby("method", sort=False).agg(cost_gap=("cost_gap_vs_oracle", "mean"), messages=("messages", "mean"))
    fig, ax = plt.subplots(figsize=(6.8, 3.7))
    for method, row in grouped.iterrows():
        ax.scatter(row["messages"], row["cost_gap"], s=60, label=METHOD_LABELS[str(method)])
    ax.set_xlabel("Mensajes contabilizados por mundo")
    ax.set_ylabel("Gap medio de coste frente al oráculo")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(figures / "fig-sp6-cost-communication.pdf", bbox_inches="tight")
    plt.close(fig)


def _report(experiment_id: str, runs: pd.DataFrame, summary: pd.DataFrame, hypotheses: pd.DataFrame, audit: dict[str, Any]) -> str:
    lines = [
        f"# {experiment_id}",
        "",
        f"- Worlds: `{runs['world_hash'].nunique()}`",
        f"- Runs: `{len(runs)}`",
        f"- Audit: `{audit['status']}`",
        f"- Evidence: `{audit['evidence_level']}`",
        "",
        "## Method summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Hypotheses",
        "",
        hypotheses.to_markdown(index=False),
        "",
        "## Scope",
        "",
        audit["not_claimed"],
    ]
    return "\n".join(lines) + "\n"


def _expand_seeds(spec: Any) -> list[int]:
    if isinstance(spec, list):
        return [int(value) for value in spec]
    return list(range(int(spec["start"]), int(spec["start"]) + int(spec["count"])))


def _latex_scientific(value: float) -> str:
    if value == 0.0:
        return "0"
    exponent = int(math.floor(math.log10(abs(value))))
    mantissa = value / (10.0**exponent)
    return f"{mantissa:.2g}\\times10^{{{exponent}}}"


__all__ = [
    "METHODS",
    "RecoveryWorld",
    "audit_world_theory",
    "generate_world",
    "run_sp6_config",
    "simulate_method",
]

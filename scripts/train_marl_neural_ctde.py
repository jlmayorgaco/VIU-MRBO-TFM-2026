"""Train a neural shared-actor CTDE MARL baseline on warehouse episodes.

This is an honest neural MARL comparator for the thesis: one actor is shared by
all robots, training uses centralized multi-robot episode returns, and execution
is decentralized from local robot-load features. The optimizer is a
cross-entropy/evolution-strategy search over a compact residual MLP; it avoids
claiming PPO/MAPPO without per-action log-probability traces from the simulator.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from benchmark_warehouse_methods import scenario_runs  # noqa: E402
from viu_mrob_tfm.marl import DEFAULT_HIDDEN_DIM, MARL_CTDE_FEATURE_NAMES, initial_neural_vector  # noqa: E402
from viu_mrob_tfm.simulations import POLICY_MARL_NEURAL_CTDE, WarehouseConfig, run_warehouse_simulation  # noqa: E402


@dataclass(frozen=True)
class EvalCase:
    scenario: str
    case: str


DEFAULT_CASES = (
    EvalCase("comm_degradation", "R3_p0"),
    EvalCase("scarcity_priority", "adversarial"),
    EvalCase("robot_failures", "fail4"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results/marl_neural_ctde_training"))
    parser.add_argument("--base-linear-model", type=Path, default=Path("results/marl_ctde_training_v1/model.json"))
    parser.add_argument("--cases", default=",".join(f"{case.scenario}:{case.case}" for case in DEFAULT_CASES))
    parser.add_argument("--train-seeds", default="1000,1001,1002")
    parser.add_argument("--generations", type=int, default=6)
    parser.add_argument("--population", type=int, default=10)
    parser.add_argument("--elite-fraction", type=float, default=0.3)
    parser.add_argument("--sigma", type=float, default=0.18)
    parser.add_argument("--min-sigma", type=float, default=0.025)
    parser.add_argument("--random-seed", type=int, default=991)
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--max-loads", type=int, default=12)
    parser.add_argument("--hidden-dim", type=int, default=DEFAULT_HIDDEN_DIM)
    parser.add_argument("--smoke", action="store_true", help="Use shortest scenario templates before overrides.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    train_cases = _parse_cases(args.cases)
    train_seeds = _parse_seeds(args.train_seeds)
    scenario_lookup = _scenario_lookup(train_cases, smoke=args.smoke)
    rng = np.random.default_rng(args.random_seed)

    base_weights, base_idle = _load_linear_seed(args.base_linear_model)
    mean = initial_neural_vector(base_weights, hidden_dim=args.hidden_dim, idle_score=base_idle)
    sigma = np.full(mean.size, max(args.sigma, args.min_sigma), dtype=float)
    sigma[: len(base_weights)] *= 0.75
    sigma[-1] *= 1.5
    elite_count = max(1, int(math.ceil(args.population * args.elite_fraction)))
    best_vector = mean.copy()
    best_eval: dict[str, Any] | None = None
    history: list[dict[str, Any]] = []
    started = time.perf_counter()

    for generation in range(args.generations):
        candidates = [mean.copy()]
        while len(candidates) < args.population:
            candidates.append(rng.normal(mean, sigma))
        evaluations = []
        for candidate_idx, vector in enumerate(candidates):
            evaluation = evaluate_vector(
                vector,
                train_cases=train_cases,
                train_seeds=train_seeds,
                scenario_lookup=scenario_lookup,
                duration=args.duration,
                max_loads=args.max_loads,
                hidden_dim=args.hidden_dim,
            )
            evaluation.update({"generation": generation, "candidate": candidate_idx})
            history.append(evaluation)
            evaluations.append(evaluation)
            print(
                "gen={generation} cand={candidate} score={objective:.4f} "
                "capture={reward_capture_ratio:.4f} delivered={loads_delivered:.3f} waste={wasted_distance:.2f}".format(
                    **evaluation,
                )
            )
        order = np.argsort([row["objective"] for row in evaluations])[::-1]
        elites = np.vstack([candidates[int(idx)] for idx in order[:elite_count]])
        elite_scores = np.asarray([evaluations[int(idx)]["objective"] for idx in order[:elite_count]], dtype=float)
        weights = elite_scores - float(np.min(elite_scores)) + 1.0e-6
        weights /= float(np.sum(weights))
        mean = 0.40 * mean + 0.60 * np.average(elites, axis=0, weights=weights)
        sigma = np.maximum(args.min_sigma, 0.70 * sigma + 0.30 * np.std(elites, axis=0, ddof=0))
        generation_best = evaluations[int(order[0])]
        if best_eval is None or generation_best["objective"] > best_eval["objective"]:
            best_eval = generation_best
            best_vector = candidates[int(order[0])].copy()

    elapsed = time.perf_counter() - started
    write_csv(args.out / "training_history.csv", history, history_columns())
    initial_objective = next(
        (
            float(row["objective"])
            for row in history
            if int(row["generation"]) == 0 and int(row["candidate"]) == 0
        ),
        math.nan,
    )
    model = {
        "model_version": "marl-neural-ctde-residual-v1",
        "algorithm": "centralized episodic cross-entropy search with decentralized shared neural actor",
        "feature_names": list(MARL_CTDE_FEATURE_NAMES),
        "hidden_dim": args.hidden_dim,
        "params": [float(value) for value in best_vector],
        "base_linear_weights": [float(value) for value in base_weights],
        "base_idle_score": float(base_idle),
        "train_cases": [f"{case.scenario}:{case.case}" for case in train_cases],
        "train_seeds": train_seeds,
        "duration": args.duration,
        "max_loads": args.max_loads,
        "generations": args.generations,
        "population": args.population,
        "elite_fraction": args.elite_fraction,
        "initial_objective": initial_objective,
        "best_objective": None if best_eval is None else float(best_eval["objective"]),
        "best_capture": None if best_eval is None else float(best_eval["reward_capture_ratio"]),
        "runtime_seconds": elapsed,
        "objective": "capture + delivery/throughput reward minus waste, switches and contact deficit",
    }
    (args.out / "model.json").write_text(json.dumps(model, indent=2, sort_keys=True), encoding="utf-8")
    write_readme(args.out / "README.md", model, history)
    return 0


def evaluate_vector(
    vector: np.ndarray,
    *,
    train_cases: tuple[EvalCase, ...],
    train_seeds: list[int],
    scenario_lookup: dict[tuple[str, str], Any],
    duration: float,
    max_loads: int,
    hidden_dim: int,
) -> dict[str, Any]:
    rows = []
    for eval_case in train_cases:
        scenario = scenario_lookup[(eval_case.scenario, eval_case.case)]
        for seed in train_seeds:
            overrides = dict(scenario.overrides)
            overrides.update(
                {
                    "assignment_policy": POLICY_MARL_NEURAL_CTDE,
                    "duration": duration,
                    "max_loads": max_loads,
                    "max_active_loads": min(int(overrides.get("max_active_loads", 3)), max_loads),
                    "marl_neural_params": tuple(float(value) for value in vector),
                    "marl_neural_hidden_dim": hidden_dim,
                    "seed": seed,
                    "scenario_name": eval_case.scenario,
                }
            )
            result = run_warehouse_simulation(WarehouseConfig(**overrides))
            rows.append(result.summary)
    return summarize_episode_rows(rows)


def summarize_episode_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    capture = _mean_metric(rows, "reward_capture_ratio")
    delivery_rate = _mean_metric(rows, "delivery_rate")
    throughput = _mean_metric(rows, "throughput_steady")
    waste = _mean_metric(rows, "wasted_distance")
    switches = _mean_metric(rows, "lateral_switches_per_delivery")
    deficit = _mean_metric(rows, "mean_contact_deficit")
    objective = (
        capture
        + 0.05 * delivery_rate
        + 0.02 * throughput
        - 0.0015 * waste
        - 0.006 * switches
        - 0.015 * deficit
    )
    return {
        "objective": objective,
        "reward_capture_ratio": capture,
        "delivery_rate": delivery_rate,
        "throughput_steady": throughput,
        "loads_delivered": _mean_metric(rows, "loads_delivered"),
        "wasted_distance": waste,
        "lateral_switches_per_delivery": switches,
        "mean_contact_deficit": deficit,
    }


def _load_linear_seed(path: Path) -> tuple[list[float], float]:
    if not path.exists():
        return [], 0.0
    model = json.loads(path.read_text(encoding="utf-8"))
    return [float(value) for value in model.get("weights", [])], float(model.get("idle_score", 0.0))


def _parse_cases(value: str) -> tuple[EvalCase, ...]:
    cases: list[EvalCase] = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        scenario, sep, case = token.partition(":")
        if not sep:
            raise SystemExit(f"Case must be scenario:case, got {token!r}")
        cases.append(EvalCase(scenario, case))
    return tuple(cases)


def _parse_seeds(value: str) -> list[int]:
    return [int(token.strip()) for token in value.split(",") if token.strip()]


def _scenario_lookup(cases: tuple[EvalCase, ...], smoke: bool) -> dict[tuple[str, str], Any]:
    lookup: dict[tuple[str, str], Any] = {}
    for scenario_name in sorted({case.scenario for case in cases}):
        for run in scenario_runs(scenario_name, quick=True, smoke=smoke):
            lookup[(scenario_name, run.case)] = run
    missing = [(case.scenario, case.case) for case in cases if (case.scenario, case.case) not in lookup]
    if missing:
        raise SystemExit(f"Unavailable train cases: {missing}")
    return lookup


def _mean_metric(rows: list[dict[str, Any]], metric: str) -> float:
    values = np.asarray([_as_float(row.get(metric)) for row in rows], dtype=float)
    values = values[np.isfinite(values)]
    return float(np.mean(values)) if values.size else 0.0


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def history_columns() -> list[str]:
    return [
        "generation",
        "candidate",
        "objective",
        "reward_capture_ratio",
        "delivery_rate",
        "throughput_steady",
        "loads_delivered",
        "wasted_distance",
        "lateral_switches_per_delivery",
        "mean_contact_deficit",
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_readme(path: Path, model: dict[str, Any], history: list[dict[str, Any]]) -> None:
    best = max(history, key=lambda row: row["objective"]) if history else {}
    lines = [
        "# Neural MARL CTDE training",
        "",
        "- Baseline: shared residual neural actor trained from full multi-robot episode returns.",
        "- Execution: decentralized; each robot scores visible loads from local features.",
        "- Optimizer: centralized cross-entropy search, not labelled as PPO/MAPPO.",
        f"- Initial objective: {_as_float(model.get('initial_objective')):.4f}.",
        f"- Best objective: {_as_float(best.get('objective')):.4f}.",
        f"- Best capture: {_as_float(best.get('reward_capture_ratio')):.4f}.",
        f"- Runtime: {_as_float(model.get('runtime_seconds')):.1f} s.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

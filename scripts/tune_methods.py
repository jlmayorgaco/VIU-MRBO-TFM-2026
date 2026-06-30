"""Small fair tuning grid for warehouse benchmark methods."""

from __future__ import annotations

import argparse
import json
import sys
import time
from itertools import product
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from benchmark_warehouse_methods import METHODS, SMITH_ABLATIONS, smith_params_for_method, scenario_runs  # noqa: E402
from viu_mrob_tfm.simulations import (  # noqa: E402
    INFO_REQUIREMENT,
    POLICY_AUCTION_CBBA,
    POLICY_GREEDY_NEAREST,
    POLICY_PROXY_PIBT,
    POLICY_PROXY_ROLLING_HORIZON,
    POLICY_PROXY_TOKEN_PASSING,
    POLICY_RANDOM_FEASIBLE,
    POLICY_RESPONSE_THRESHOLD,
    POLICY_SMITH_FULL,
    POLICY_SMITH_NO_INTEGER,
    POLICY_SMITH_NO_PRICES,
    POLICY_SMITH_RAW_OCCUPANCY,
    WarehouseConfig,
    run_warehouse_simulation,
)


def _grid(**kwargs: list[Any]) -> list[dict[str, Any]]:
    keys = list(kwargs)
    return [dict(zip(keys, values)) for values in product(*(kwargs[key] for key in keys))]


GRID: dict[str, list[dict[str, Any]]] = {
    POLICY_SMITH_FULL: _grid(
        epsilon_switch=[0.02, 0.05, 0.1],
    ),
    POLICY_SMITH_NO_PRICES: _grid(switch_margin=[0.025, 0.06], reserve_robot_slack=[0, 1]),
    POLICY_SMITH_NO_INTEGER: _grid(switch_margin=[0.025, 0.06], price_gain=[0.45, 0.75]),
    POLICY_SMITH_RAW_OCCUPANCY: _grid(switch_margin=[0.025, 0.06], price_gain=[0.45, 0.75]),
    POLICY_AUCTION_CBBA: _grid(auction_stickiness=[0.10, 0.28], auction_age_bonus=[0.006, 0.018]),
    POLICY_RESPONSE_THRESHOLD: _grid(response_sensitivity=[0.18, 0.34], response_threshold_mean=[0.8, 1.2]),
    POLICY_GREEDY_NEAREST: [{}],
    POLICY_PROXY_TOKEN_PASSING: [{}],
    POLICY_PROXY_ROLLING_HORIZON: _grid(policy_replan_period=[1.5, 3.0]),
    POLICY_PROXY_PIBT: [{}],
    POLICY_RANDOM_FEASIBLE: [{}],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("configs/tuned_params_v26.json"))
    parser.add_argument("--scenarios", default="nominal_flow,scarcity_extreme")
    parser.add_argument("--base-params", type=Path, default=Path("configs/tuned_params_v25.json"))
    parser.add_argument("--seeds", default="1000,1001,1002")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    requested_scenarios = [item.strip() for item in args.scenarios.split(",") if item.strip()]
    tuning_runs = [run for name in requested_scenarios for run in scenario_runs(name, quick=False)]
    tuning_seeds = [int(item.strip()) for item in args.seeds.split(",") if item.strip()]
    base_params = json.loads(args.base_params.read_text(encoding="utf-8")) if args.base_params.exists() else {}
    selected: dict[str, dict[str, Any]] = {
        method: params for method, params in base_params.items() if method not in SMITH_ABLATIONS
    }
    scores: dict[str, dict[str, float]] = {}
    grid_results: dict[str, list[dict[str, float]]] = {}
    for method, label, _family in METHODS:
        if INFO_REQUIREMENT[method] != "local" or method != POLICY_SMITH_FULL:
            if method not in SMITH_ABLATIONS:
                selected[method] = base_params.get(method, {})
            scores[method] = {"best_score": float("nan")}
            continue
        candidates = GRID.get(method, [{}])
        best_score = float("-inf")
        best_params: dict[str, Any] = {}
        base_method_params = smith_params_for_method(method, base_params)
        method_grid: list[dict[str, float]] = []
        for params in candidates:
            candidate_params = dict(base_method_params)
            candidate_params.update(params)
            if method == POLICY_SMITH_FULL:
                candidate_params.update(
                    {
                        "price_feedback_signal": "effective_committed",
                        "lateral_switch_rule": "potential",
                        "clearing_mode": "tick",
                    }
                )
            started = time.perf_counter()
            score = 0.0
            run_count = 0
            captures_by_scenario: dict[str, list[float]] = {}
            lateral_per_delivery_by_scenario: dict[str, list[float]] = {}
            for scenario in tuning_runs:
                for seed in tuning_seeds:
                    kwargs = dict(scenario.overrides)
                    kwargs.update(candidate_params)
                    kwargs["seed"] = seed
                    kwargs["scenario_name"] = scenario.name
                    kwargs["assignment_policy"] = method
                    config = WarehouseConfig(**kwargs)
                    result = run_warehouse_simulation(config)
                    score += _tuning_score(result.summary)
                    captures_by_scenario.setdefault(scenario.name, []).append(
                        float(result.summary["reward_capture_ratio"])
                    )
                    lateral_per_delivery_by_scenario.setdefault(scenario.name, []).append(
                        float(result.summary["lateral_switches_per_delivery"])
                    )
                    run_count += 1
            score /= max(run_count, 1)
            grid_row: dict[str, float] = {"score": float(score)}
            for key, value in params.items():
                if isinstance(value, (float, int)):
                    grid_row[key] = float(value)
            for scenario_name, values in captures_by_scenario.items():
                grid_row[f"{scenario_name}_capture_mean"] = float(sum(values) / max(len(values), 1))
            for scenario_name, values in lateral_per_delivery_by_scenario.items():
                grid_row[f"{scenario_name}_lateral_per_delivery_mean"] = float(sum(values) / max(len(values), 1))
            method_grid.append(grid_row)
            if score > best_score:
                best_score = score
                best_params = candidate_params
            print(
                f"{label:<30} params={candidate_params} "
                f"score={score:.3f} runtime={time.perf_counter() - started:.2f}s"
            )
        selected[method] = best_params
        scores[method] = {"best_score": best_score}
        grid_results[method] = method_grid
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(selected, indent=2, sort_keys=True), encoding="utf-8")
    score_path = args.out.with_name(args.out.stem + "_scores.json")
    score_path.write_text(
        json.dumps({"scores": scores, "grid": grid_results}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"Saved tuned params to {args.out}")
    return 0


def _tuning_score(summary: dict[str, Any]) -> float:
    return (
        float(summary["delivered_reward"])
        - 0.02 * float(summary["lateral_switches"])
        - 0.001 * float(summary["total_robot_distance"])
    )


if __name__ == "__main__":
    raise SystemExit(main())

"""SP1.N1 confirmatory campaign and publication package.

The campaign keeps four evidence layers separate:

1. spatial quality under the valid homogeneous slot reduction;
2. controlled runtime and memory scaling;
3. centralized static re-allocation after homogeneous robot loss; and
4. an out-of-domain capacity audit that motivates N2.

The heterogeneous MILP is used only as an external validity auditor in layer
4. It is not presented as an N1 method or as a fair architectural comparator.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
from scipy import stats

import sp1_a1_hungarian as homogeneous
import sp1_a2_milp as heterogeneous
from sp1_levels_common import (
    COLORS,
    LEVELS_OUTPUT_ROOT,
    REPOSITORY_ROOT,
    PowerLawFit,
    configure_publication_style,
    fit_power_law,
    label_panels,
    save_figure,
    write_json,
    write_level_manifest,
)


DEFAULT_CONFIG = (
    REPOSITORY_ROOT
    / "experiments"
    / "configs"
    / "sp1_n1_confirmatory_v2.yaml"
)
DEFAULT_OUTPUT = LEVELS_OUTPUT_ROOT / "n1_v2"

SCENARIO_LABELS = {
    "uniform": "Aleatorio",
    "clustered": "Agrupado",
    "separated": "Separado",
    "ring": "Anillo",
    "corridor": "Pasillo",
}
CAPACITY_LABELS = {
    "homogeneous": "Homogénea",
    "low": "Baja",
    "moderate": "Moderada",
    "high": "Alta",
    "extreme": "Extrema",
}
ASPECT_COLORS = {
    0.25: COLORS["green"],
    0.50: COLORS["blue"],
    1.00: COLORS["orange"],
}
ASPECT_MARKERS = {0.25: "o", 0.50: "s", 1.00: "^"}
QUOTA_LABELS = {
    "symmetric": "simétrica",
    "moderate": "moderada",
    "extreme": "extrema",
}
JOURNAL_WIDTH_IN = 7.16
JOURNAL_HEIGHT_IN = 3.12


def _load_config(path: Path, *, smoke: bool) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("The N1 configuration must be a mapping.")
    if smoke:
        payload = copy.deepcopy(payload)
        payload["analysis"]["bootstrap_resamples"] = 200
        payload["quality"]["slots"] = [12]
        payload["quality"]["quota_modes"] = ["moderate"]
        payload["quality"]["seeds_per_cell"] = 2
        payload["scaling"]["robot_counts"] = [16, 32]
        payload["scaling"]["slot_to_robot_ratios"] = [0.5, 1.0]
        payload["scaling"]["seeds_per_cell"] = 2
        payload["failure"]["slots"] = [12]
        payload["failure"]["reserve_deltas"] = [0.0, 0.2]
        payload["failure"]["failure_fractions"] = [0.0, 0.1]
        payload["failure"]["seeds_per_cell"] = 2
        payload["heterogeneity"]["slots"] = [12]
        payload["heterogeneity"]["scenarios"] = ["uniform", "ring"]
        payload["heterogeneity"]["capacity_modes"] = [
            "homogeneous",
            "moderate",
            "extreme",
        ]
        payload["heterogeneity"]["seeds_per_cell"] = 2
        payload["campaign_id"] = payload["campaign_id"] + "_SMOKE"
    return payload


def _world_id(*parts: object) -> str:
    text = "|".join(str(part) for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]


def _workspace(config: Mapping[str, Any]) -> tuple[float, float]:
    width, height = config["workspace_m"]
    return float(width), float(height)


def _progress(label: str, index: int, total: int) -> None:
    if index == 1 or index == total or index % max(1, total // 10) == 0:
        print(f"[{label}] cell {index:,}/{total:,}", flush=True)


def _quantile(values: Sequence[float], probability: float) -> float:
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    return float(np.quantile(array, probability)) if array.size else math.nan


def _decimal_comma(value: float, decimals: int) -> str:
    """Format a plotted decimal according to Spanish typographic usage."""

    return f"{value:.{decimals}f}".replace(".", ",")


def _comma_tick(value: float, _: int) -> str:
    return f"{value:g}".replace(".", ",")


def _bootstrap_median_interval(
    values: Sequence[float],
    *,
    resamples: int,
    seed: int,
    confidence: float,
) -> tuple[float, float, float]:
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return math.nan, math.nan, math.nan
    rng = np.random.default_rng(seed)
    estimates = np.empty(resamples, dtype=float)
    for index in range(resamples):
        estimates[index] = float(
            np.median(rng.choice(array, size=array.size, replace=True))
        )
    alpha = 1.0 - confidence
    return (
        float(np.median(array)),
        float(np.quantile(estimates, alpha / 2.0)),
        float(np.quantile(estimates, 1.0 - alpha / 2.0)),
    )


def _wilson_interval(
    successes: int,
    total: int,
    *,
    confidence: float,
) -> tuple[float, float]:
    if total <= 0:
        return math.nan, math.nan
    z_value = float(stats.norm.ppf(0.5 + confidence / 2.0))
    proportion = successes / total
    denominator = 1.0 + z_value**2 / total
    center = (proportion + z_value**2 / (2.0 * total)) / denominator
    radius = (
        z_value
        * math.sqrt(
            proportion * (1.0 - proportion) / total
            + z_value**2 / (4.0 * total**2)
        )
        / denominator
    )
    return max(0.0, center - radius), min(1.0, center + radius)


def _holm_adjust(p_values: Mapping[str, float]) -> dict[str, float]:
    finite = sorted(
        ((key, float(value)) for key, value in p_values.items() if np.isfinite(value)),
        key=lambda item: item[1],
    )
    adjusted: dict[str, float] = {key: math.nan for key in p_values}
    running = 0.0
    count = len(finite)
    for rank, (key, value) in enumerate(finite):
        candidate = min(1.0, (count - rank) * value)
        running = max(running, candidate)
        adjusted[key] = running
    return adjusted


def _safe_wilcoxon_greater(values: Sequence[float]) -> float:
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return math.nan
    if np.allclose(array, 0.0):
        return 1.0
    return float(
        stats.wilcoxon(
            array,
            alternative="greater",
            zero_method="wilcox",
            method="auto",
        ).pvalue
    )


def _rank_biserial_paired(values: Sequence[float]) -> float:
    """Return paired rank-biserial correlation for signed differences."""

    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array) & ~np.isclose(array, 0.0)]
    if array.size == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(array), method="average")
    positive = float(ranks[array > 0.0].sum())
    negative = float(ranks[array < 0.0].sum())
    denominator = positive + negative
    return (positive - negative) / denominator if denominator else 0.0


def _exact_sign_greater(values: Sequence[float]) -> float:
    """Distribution-free sensitivity test for a positive median shift."""

    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array) & ~np.isclose(array, 0.0)]
    if array.size == 0:
        return 1.0
    positive = int(np.sum(array > 0.0))
    return float(
        stats.binomtest(
            positive,
            int(array.size),
            p=0.5,
            alternative="greater",
        ).pvalue
    )


def _run_quality(config: Mapping[str, Any]) -> pd.DataFrame:
    section = config["quality"]
    width, height = _workspace(config)
    q_bar = float(config["q_bar_kg"])
    mean_quota = float(config["mean_slots_per_load"])
    base_seed = int(config["base_seed"])
    slots_values = [int(value) for value in section["slots"]]
    quota_modes = list(section["quota_modes"])
    scenarios = list(section["scenarios"])
    replicates = int(section["seeds_per_cell"])
    delta = float(section["reserve_delta"])
    total_cells = len(slots_values) * len(quota_modes) * len(scenarios)
    rows: list[dict[str, Any]] = []
    cell = 0
    workspace_diagonal = math.hypot(width, height)

    for total_slots in slots_values:
        robot_count = homogeneous.robot_count_from_delta(total_slots, delta)
        for quota_mode in quota_modes:
            for scenario in scenarios:
                cell += 1
                _progress("quality", cell, total_cells)
                for replicate in range(replicates):
                    world_seed = homogeneous.stable_seed(
                        base_seed,
                        "n1-quality-confirmatory",
                        total_slots,
                        quota_mode,
                        scenario,
                        replicate,
                    )
                    robots, loads, quotas = homogeneous.generate_world(
                        robot_count=robot_count,
                        total_slots=total_slots,
                        q_bar=q_bar,
                        mean_quota=mean_quota,
                        quota_mode=quota_mode,
                        spatial_mode=scenario,
                        workspace_width=width,
                        workspace_height=height,
                        seed=world_seed,
                    )
                    result = homogeneous.solve_hungarian(
                        robots,
                        loads,
                        q_bar,
                        allow_partial=False,
                    )
                    greedy_cost = homogeneous.sequential_greedy_cost(
                        result.cost_matrix
                    )
                    saving = (
                        (greedy_cost - result.total_cost) / greedy_cost
                        if greedy_cost > 0.0
                        else 0.0
                    )
                    assignment_costs = [item.cost for item in result.assignments]
                    expected_slots = int(np.sum(quotas))
                    violations = int(
                        len(result.assignments) != expected_slots
                        or result.missing_slots != 0
                        or not result.feasible
                    )
                    rows.append(
                        {
                            "experiment": "quality",
                            "world_id": _world_id(
                                "quality",
                                total_slots,
                                quota_mode,
                                scenario,
                                replicate,
                                world_seed,
                            ),
                            "world_seed": world_seed,
                            "replicate": replicate,
                            "scenario": scenario,
                            "scenario_label": SCENARIO_LABELS[scenario],
                            "quota_mode": quota_mode,
                            "N": robot_count,
                            "K": len(loads),
                            "M": expected_slots,
                            "reserve_delta": delta,
                            "mission_feasible": bool(result.feasible),
                            "constraint_violations": violations,
                            "hungarian_cost": result.total_cost,
                            "greedy_cost": greedy_cost,
                            "greedy_to_hungarian_ratio": (
                                greedy_cost / result.total_cost
                                if result.total_cost > 0.0
                                else 1.0
                            ),
                            "relative_saving": saving,
                            "normalized_assignment_cost_p95": (
                                _quantile(assignment_costs, 0.95)
                                / workspace_diagonal
                            ),
                            "assignment_cost_gini": homogeneous.gini_coefficient(
                                assignment_costs
                            ),
                            "solver_ms": result.timings.solver_wall_ns / 1e6,
                            "total_ms": result.timings.total_wall_ns / 1e6,
                        }
                    )
    return pd.DataFrame(rows)


def _run_scaling(config: Mapping[str, Any]) -> pd.DataFrame:
    section = config["scaling"]
    width, height = _workspace(config)
    q_bar = float(config["q_bar_kg"])
    mean_quota = float(config["mean_slots_per_load"])
    base_seed = int(config["base_seed"])
    robot_counts = [int(value) for value in section["robot_counts"]]
    ratios = [float(value) for value in section["slot_to_robot_ratios"]]
    replicates = int(section["seeds_per_cell"])
    total_cells = len(robot_counts) * len(ratios)
    rows: list[dict[str, Any]] = []
    cell = 0

    for robot_count in robot_counts:
        for ratio in ratios:
            cell += 1
            _progress("scaling", cell, total_cells)
            total_slots = max(1, int(round(robot_count * ratio)))
            for replicate in range(replicates):
                world_seed = homogeneous.stable_seed(
                    base_seed,
                    "n1-scaling-confirmatory",
                    robot_count,
                    total_slots,
                    replicate,
                )
                robots, loads, _ = homogeneous.generate_world(
                    robot_count=robot_count,
                    total_slots=total_slots,
                    q_bar=q_bar,
                    mean_quota=mean_quota,
                    quota_mode=str(section["quota_mode"]),
                    spatial_mode=str(section["scenario"]),
                    workspace_width=width,
                    workspace_height=height,
                    seed=world_seed,
                )
                result = homogeneous.solve_hungarian(
                    robots,
                    loads,
                    q_bar,
                    allow_partial=False,
                )
                expected_bytes = 8 * robot_count * total_slots
                rows.append(
                    {
                        "experiment": "scaling",
                        "world_id": _world_id(
                            "scaling",
                            robot_count,
                            total_slots,
                            replicate,
                            world_seed,
                        ),
                        "world_seed": world_seed,
                        "replicate": replicate,
                        "N": robot_count,
                        "K": len(loads),
                        "M": total_slots,
                        "slot_to_robot_ratio": ratio,
                        "matrix_elements": robot_count * total_slots,
                        "matrix_bytes": int(result.cost_matrix.nbytes),
                        "expected_matrix_bytes": expected_bytes,
                        "matrix_ms": result.timings.matrix_wall_ns / 1e6,
                        "solver_ms": result.timings.solver_wall_ns / 1e6,
                        "post_ms": result.timings.post_wall_ns / 1e6,
                        "total_ms": result.timings.total_wall_ns / 1e6,
                        "mission_feasible": bool(result.feasible),
                    }
                )
    return pd.DataFrame(rows)


def _run_failure(config: Mapping[str, Any]) -> pd.DataFrame:
    section = config["failure"]
    width, height = _workspace(config)
    q_bar = float(config["q_bar_kg"])
    mean_quota = float(config["mean_slots_per_load"])
    base_seed = int(config["base_seed"])
    slots_values = [int(value) for value in section["slots"]]
    deltas = [float(value) for value in section["reserve_deltas"]]
    fractions = [float(value) for value in section["failure_fractions"]]
    replicates = int(section["seeds_per_cell"])
    total_cells = len(slots_values) * len(deltas)
    rows: list[dict[str, Any]] = []
    cell = 0

    for total_slots in slots_values:
        for delta in deltas:
            cell += 1
            _progress("failure", cell, total_cells)
            robot_count = homogeneous.robot_count_from_delta(total_slots, delta)
            for replicate in range(replicates):
                world_seed = homogeneous.stable_seed(
                    base_seed,
                    "n1-failure-confirmatory",
                    total_slots,
                    delta,
                    replicate,
                )
                robots, loads, _ = homogeneous.generate_world(
                    robot_count=robot_count,
                    total_slots=total_slots,
                    q_bar=q_bar,
                    mean_quota=mean_quota,
                    quota_mode=str(section["quota_mode"]),
                    spatial_mode=str(section["scenario"]),
                    workspace_width=width,
                    workspace_height=height,
                    seed=world_seed,
                )
                base_result = homogeneous.solve_hungarian(
                    robots,
                    loads,
                    q_bar,
                    allow_partial=False,
                )
                all_ids = np.asarray([robot.id for robot in robots], dtype=object)
                for fraction in fractions:
                    treatment_seed = homogeneous.stable_seed(
                        base_seed,
                        "n1-failure-treatment",
                        world_seed,
                        fraction,
                    )
                    rng = np.random.default_rng(treatment_seed)
                    failed_count = (
                        0
                        if fraction == 0.0
                        else max(1, int(round(fraction * robot_count)))
                    )
                    failed_ids = set(
                        str(value)
                        for value in (
                            rng.choice(
                                all_ids,
                                size=min(failed_count, robot_count),
                                replace=False,
                            ).tolist()
                            if failed_count
                            else []
                        )
                    )
                    active = [robot for robot in robots if robot.id not in failed_ids]
                    recovered = homogeneous.solve_hungarian(
                        active,
                        loads,
                        q_bar,
                        allow_partial=True,
                    )
                    survivor_ids = {robot.id for robot in active}
                    churn = homogeneous.changed_assignment_fraction(
                        base_result,
                        recovered,
                        survivor_ids,
                    )
                    relative_cost = (
                        (recovered.total_cost - base_result.total_cost)
                        / base_result.total_cost
                        if recovered.feasible and base_result.total_cost > 0.0
                        else math.nan
                    )
                    theoretical = len(active) >= total_slots
                    rows.append(
                        {
                            "experiment": "failure",
                            "world_id": _world_id(
                                "failure",
                                total_slots,
                                delta,
                                replicate,
                                world_seed,
                            ),
                            "world_seed": world_seed,
                            "treatment_seed": treatment_seed,
                            "replicate": replicate,
                            "N_original": robot_count,
                            "N_active": len(active),
                            "K": len(loads),
                            "M": total_slots,
                            "reserve_delta": delta,
                            "failure_fraction_nominal": fraction,
                            "failure_fraction_realized": failed_count / robot_count,
                            "failure_count": failed_count,
                            "recovery_feasible": bool(recovered.feasible),
                            "theoretical_recoverable": bool(theoretical),
                            "theory_agreement": bool(recovered.feasible == theoretical),
                            "assignment_churn": churn,
                            "relative_cost_increase": relative_cost,
                            "solver_ms": recovered.timings.solver_wall_ns / 1e6,
                            "total_ms": recovered.timings.total_wall_ns / 1e6,
                        }
                    )
    return pd.DataFrame(rows)


def _audit_hungarian_capacity(
    robots: Sequence[Any],
    loads: Sequence[Any],
    assignments: Sequence[Any],
) -> tuple[bool, float, float, float]:
    capacity_by_robot = {robot.id: float(robot.capacity) for robot in robots}
    mass_by_load = {load.id: float(load.mass) for load in loads}
    recruited = {load.id: 0.0 for load in loads}
    for assignment in assignments:
        recruited[assignment.load_id] += capacity_by_robot[assignment.robot_id]
    margins = np.asarray(
        [recruited[load_id] - mass for load_id, mass in mass_by_load.items()],
        dtype=float,
    )
    shortfalls = np.maximum(-margins, 0.0)
    return (
        bool(np.all(margins >= -1e-9)),
        float(np.sum(shortfalls)),
        float(np.min(margins)),
        float(np.mean(margins)),
    )


def _run_heterogeneity(config: Mapping[str, Any]) -> pd.DataFrame:
    section = config["heterogeneity"]
    width, height = _workspace(config)
    q_bar = float(config["q_bar_kg"])
    mean_quota = float(config["mean_slots_per_load"])
    base_seed = int(config["base_seed"])
    slots_values = [int(value) for value in section["slots"]]
    scenarios = list(section["scenarios"])
    capacity_modes = list(section["capacity_modes"])
    replicates = int(section["seeds_per_cell"])
    delta = float(section["reserve_delta"])
    total_cells = len(slots_values) * len(scenarios)
    rows: list[dict[str, Any]] = []
    cell = 0

    for total_slots in slots_values:
        robot_count = homogeneous.robot_count_from_delta(total_slots, delta)
        for scenario in scenarios:
            cell += 1
            _progress("heterogeneity", cell, total_cells)
            for replicate in range(replicates):
                world_seed = homogeneous.stable_seed(
                    base_seed,
                    "n1-heterogeneity-confirmatory",
                    total_slots,
                    scenario,
                    replicate,
                )
                for capacity_mode in capacity_modes:
                    robots, loads, _ = heterogeneous.generate_paired_world(
                        robot_count=robot_count,
                        total_slots=total_slots,
                        q_bar=q_bar,
                        mean_quota=mean_quota,
                        quota_mode=str(section["quota_mode"]),
                        spatial_mode=scenario,
                        capacity_mode=capacity_mode,
                        workspace_width=width,
                        workspace_height=height,
                        seed=world_seed,
                    )
                    homogeneous_robots, homogeneous_loads = (
                        heterogeneous._hungarian_entities(robots, loads, q_bar)
                    )
                    slot_result = heterogeneous.HUNGARIAN.solve_hungarian(
                        homogeneous_robots,
                        homogeneous_loads,
                        q_bar,
                        allow_partial=False,
                    )
                    (
                        capacity_feasible,
                        total_shortfall,
                        minimum_margin,
                        mean_margin,
                    ) = _audit_hungarian_capacity(
                        robots,
                        loads,
                        slot_result.assignments,
                    )

                    milp_result = None
                    milp_error = ""
                    try:
                        milp_result = heterogeneous.solve_heterogeneous_milp(
                            robots,
                            loads,
                            time_limit_seconds=float(section["milp_time_limit_s"]),
                            mip_rel_gap=float(section["milp_relative_gap"]),
                        )
                    except heterogeneous.InfeasibleCoalitionError as error:
                        milp_error = str(error)
                    milp_feasible = bool(
                        milp_result is not None and milp_result.feasible
                    )
                    milp_optimal = bool(
                        milp_result is not None and milp_result.optimal
                    )
                    false_feasible = bool(
                        slot_result.feasible and not capacity_feasible
                    )
                    capacities = np.asarray(
                        [robot.capacity for robot in robots], dtype=float
                    )
                    rows.append(
                        {
                            "experiment": "heterogeneity",
                            "world_id": _world_id(
                                "heterogeneity",
                                total_slots,
                                scenario,
                                replicate,
                                world_seed,
                            ),
                            "world_seed": world_seed,
                            "replicate": replicate,
                            "scenario": scenario,
                            "scenario_label": SCENARIO_LABELS[scenario],
                            "capacity_mode": capacity_mode,
                            "capacity_label": CAPACITY_LABELS[capacity_mode],
                            "capacity_sigma": float(
                                heterogeneous.CAPACITY_MODE_SIGMA[capacity_mode]
                            ),
                            "capacity_cv": float(
                                np.std(capacities) / np.mean(capacities)
                            ),
                            "N": robot_count,
                            "K": len(loads),
                            "M": total_slots,
                            "reserve_delta": delta,
                            "hungarian_declared_feasible": bool(
                                slot_result.feasible
                            ),
                            "hungarian_capacity_feasible": capacity_feasible,
                            "hungarian_false_feasible": false_feasible,
                            "hungarian_total_shortfall_kg": total_shortfall,
                            "hungarian_minimum_margin_kg": minimum_margin,
                            "hungarian_mean_margin_kg": mean_margin,
                            "milp_feasible": milp_feasible,
                            "milp_optimal_certified": milp_optimal,
                            "milp_mip_gap": (
                                float(milp_result.mip_gap)
                                if milp_result is not None
                                and milp_result.mip_gap is not None
                                else math.nan
                            ),
                            "milp_rescues_false_feasible": bool(
                                false_feasible and milp_feasible and milp_optimal
                            ),
                            "milp_solver_ms": (
                                milp_result.timings.solver_wall_ns / 1e6
                                if milp_result is not None
                                else math.nan
                            ),
                            "milp_error": milp_error,
                        }
                    )
    return pd.DataFrame(rows)


def _quality_analysis(
    runs: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    confidence = float(config["analysis"]["confidence_level"])
    resamples = int(config["analysis"]["bootstrap_resamples"])
    threshold = float(config["analysis"]["practical_saving_threshold"])
    raw_p: dict[str, float] = {}
    sign_p: dict[str, float] = {}
    rows: list[dict[str, Any]] = []
    scenario_order = list(config["quality"]["scenarios"])
    for scenario in scenario_order:
        block = runs.loc[runs["scenario"] == scenario]
        values = block["relative_saving"].to_numpy(float)
        estimate, low, high = _bootstrap_median_interval(
            values,
            resamples=resamples,
            seed=homogeneous.stable_seed(
                int(config["base_seed"]), "analysis-quality", scenario
            ),
            confidence=confidence,
        )
        shifted = values - threshold
        raw_p[scenario] = _safe_wilcoxon_greater(shifted)
        sign_p[scenario] = _exact_sign_greater(shifted)
        rows.append(
            {
                "scenario": scenario,
                "scenario_label": SCENARIO_LABELS[scenario],
                "n_worlds": len(block),
                "relative_saving_median": estimate,
                "relative_saving_ci_low": low,
                "relative_saving_ci_high": high,
                "normalized_p95_cost_median": float(
                    block["normalized_assignment_cost_p95"].median()
                ),
                "normalized_p95_cost_q25": float(
                    block["normalized_assignment_cost_p95"].quantile(0.25)
                ),
                "normalized_p95_cost_q75": float(
                    block["normalized_assignment_cost_p95"].quantile(0.75)
                ),
                "normalized_p95_cost_p05": float(
                    block["normalized_assignment_cost_p95"].quantile(0.05)
                ),
                "normalized_p95_cost_p95": float(
                    block["normalized_assignment_cost_p95"].quantile(0.95)
                ),
                "feasibility_rate": float(block["mission_feasible"].mean()),
                "constraint_violations": int(
                    block["constraint_violations"].sum()
                ),
                "wilcoxon_p_raw": raw_p[scenario],
                "rank_biserial_vs_5pct": _rank_biserial_paired(shifted),
                "sign_sensitivity_p_raw": sign_p[scenario],
            }
        )
    adjusted = _holm_adjust(raw_p)
    sign_adjusted = _holm_adjust(sign_p)
    summary = pd.DataFrame(rows)
    summary["wilcoxon_p_holm"] = summary["scenario"].map(adjusted)
    summary["sign_sensitivity_p_holm"] = summary["scenario"].map(
        sign_adjusted
    )
    summary["saving_over_5pct_supported"] = (
        (summary["relative_saving_ci_low"] > threshold)
        & (summary["wilcoxon_p_holm"] < 0.05)
    )
    summary["sign_sensitivity_supported"] = (
        summary["sign_sensitivity_p_holm"] < 0.05
    )

    overall = _bootstrap_median_interval(
        runs["relative_saving"].to_numpy(float),
        resamples=resamples,
        seed=homogeneous.stable_seed(
            int(config["base_seed"]), "analysis-quality-overall"
        ),
        confidence=confidence,
    )
    overall_p = _safe_wilcoxon_greater(
        runs["relative_saving"].to_numpy(float) - threshold
    )
    metrics = {
        "overall_saving_median": overall[0],
        "overall_saving_ci_low": overall[1],
        "overall_saving_ci_high": overall[2],
        "overall_saving_p": overall_p,
        "scenario_gates_passed": int(
            summary["saving_over_5pct_supported"].sum()
        ),
        "scenario_gates_total": len(summary),
        "quality_supported_max_p_holm": float(
            summary.loc[
                summary["saving_over_5pct_supported"],
                "wilcoxon_p_holm",
            ].max()
        ),
        "sign_sensitivity_matches_confirmatory_gate": bool(
            np.array_equal(
                summary["saving_over_5pct_supported"].to_numpy(bool),
                summary["sign_sensitivity_supported"].to_numpy(bool),
            )
        ),
        "quality_feasibility_rate": float(runs["mission_feasible"].mean()),
        "quality_constraint_violations": int(
            runs["constraint_violations"].sum()
        ),
        "median_greedy_to_hungarian_ratio": float(
            runs["greedy_to_hungarian_ratio"].median()
        ),
    }
    return summary, metrics


def _quality_cell_diagnostic(
    runs: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    """Return a post-hoc stratification without changing the E1 gate."""

    rows: list[dict[str, Any]] = []
    for scenario in config["quality"]["scenarios"]:
        for slots in config["quality"]["slots"]:
            for quota_mode in config["quality"]["quota_modes"]:
                block = runs.loc[
                    (runs["scenario"] == scenario)
                    & (runs["M"] == slots)
                    & (runs["quota_mode"] == quota_mode)
                ]
                if block.empty:
                    continue
                rows.append(
                    {
                        "scenario": scenario,
                        "scenario_label": SCENARIO_LABELS[scenario],
                        "M": int(slots),
                        "quota_mode": quota_mode,
                        "quota_label": QUOTA_LABELS.get(
                            quota_mode, str(quota_mode)
                        ),
                        "n_worlds": len(block),
                        "relative_saving_median": float(
                            block["relative_saving"].median()
                        ),
                        "cells_above_practical_threshold": bool(
                            block["relative_saving"].median()
                            > float(
                                config["analysis"][
                                    "practical_saving_threshold"
                                ]
                            )
                        ),
                    }
                )
    return pd.DataFrame(rows)


def _bootstrap_scaling_exponent(
    runs: pd.DataFrame,
    *,
    resamples: int,
    seed: int,
    confidence: float,
) -> tuple[PowerLawFit, float, float]:
    balanced = runs.loc[np.isclose(runs["slot_to_robot_ratio"], 1.0)].copy()
    summary = (
        balanced.groupby("N", as_index=False)["solver_ms"].median()
    )
    fit = fit_power_law(summary["N"], summary["solver_ms"])
    rng = np.random.default_rng(seed)
    sizes = sorted(int(value) for value in balanced["N"].unique())
    exponents: list[float] = []
    for _ in range(resamples):
        medians: list[float] = []
        for size in sizes:
            values = balanced.loc[balanced["N"] == size, "solver_ms"].to_numpy(
                float
            )
            sampled = rng.choice(values, size=values.size, replace=True)
            medians.append(float(np.median(sampled)))
        candidate = fit_power_law(sizes, medians)
        if np.isfinite(candidate.exponent):
            exponents.append(candidate.exponent)
    alpha = 1.0 - confidence
    return (
        fit,
        float(np.quantile(exponents, alpha / 2.0)),
        float(np.quantile(exponents, 1.0 - alpha / 2.0)),
    )


def _scaling_analysis(
    runs: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (ratio, size), block in runs.groupby(
        ["slot_to_robot_ratio", "N"], sort=True
    ):
        rows.append(
            {
                "slot_to_robot_ratio": ratio,
                "N": int(size),
                "M": int(block["M"].iloc[0]),
                "n_worlds": len(block),
                "solver_ms_median": float(block["solver_ms"].median()),
                "solver_ms_p05": float(block["solver_ms"].quantile(0.05)),
                "solver_ms_p95": float(block["solver_ms"].quantile(0.95)),
                "total_ms_median": float(block["total_ms"].median()),
                "matrix_mib_median": float(
                    block["matrix_bytes"].median() / 2**20
                ),
                "mission_feasible_rate": float(
                    block["mission_feasible"].mean()
                ),
            }
        )
    summary = pd.DataFrame(rows)
    fit, low, high = _bootstrap_scaling_exponent(
        runs,
        resamples=int(config["analysis"]["bootstrap_resamples"]),
        seed=homogeneous.stable_seed(
            int(config["base_seed"]), "analysis-scaling"
        ),
        confidence=float(config["analysis"]["confidence_level"]),
    )
    relative_memory_error = np.abs(
        runs["matrix_bytes"] - runs["expected_matrix_bytes"]
    ) / runs["expected_matrix_bytes"]
    metrics = {
        "solver_power_exponent": fit.exponent,
        "solver_power_scale": fit.scale,
        "solver_power_fit_points": fit.n_points,
        "solver_power_ci_low": low,
        "solver_power_ci_high": high,
        "solver_power_r_squared": fit.r_squared,
        "scaling_max_n": int(runs["N"].max()),
        "scaling_max_m": int(runs["M"].max()),
        "scaling_completion_rate": float(runs["mission_feasible"].mean()),
        "scaling_completed_count": int(runs["mission_feasible"].sum()),
        "scaling_failed_count": int((~runs["mission_feasible"]).sum()),
        "memory_formula_max_relative_error": float(
            relative_memory_error.max()
        ),
        "balanced_p95_solver_ms_at_max_n": float(
            runs.loc[
                np.isclose(runs["slot_to_robot_ratio"], 1.0)
                & (runs["N"] == runs["N"].max()),
                "solver_ms",
            ].quantile(0.95)
        ),
    }
    return summary, metrics


def _failure_analysis(
    runs: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    confidence = float(config["analysis"]["confidence_level"])
    resamples = int(config["analysis"]["bootstrap_resamples"])
    rows: list[dict[str, Any]] = []
    for (delta, fraction), block in runs.groupby(
        ["reserve_delta", "failure_fraction_nominal"], sort=True
    ):
        successes = int(block["recovery_feasible"].sum())
        low, high = _wilson_interval(
            successes,
            len(block),
            confidence=confidence,
        )
        feasible = block.loc[block["recovery_feasible"]]
        cost_interval = _bootstrap_median_interval(
            feasible["relative_cost_increase"].to_numpy(float),
            resamples=resamples,
            seed=homogeneous.stable_seed(
                int(config["base_seed"]),
                "analysis-failure-cost",
                float(delta),
                float(fraction),
            ),
            confidence=confidence,
        )
        rows.append(
            {
                "reserve_delta": delta,
                "failure_fraction_nominal": fraction,
                "n_worlds": len(block),
                "recovery_count": successes,
                "feasible_cost_n": len(feasible),
                "recovery_rate": successes / len(block),
                "recovery_ci_low": low,
                "recovery_ci_high": high,
                "assignment_churn_median": float(
                    block["assignment_churn"].median()
                ),
                "relative_cost_increase_median": (
                    cost_interval[0]
                ),
                "relative_cost_increase_ci_low": cost_interval[1],
                "relative_cost_increase_ci_high": cost_interval[2],
                "theory_agreement_rate": float(
                    block["theory_agreement"].mean()
                ),
            }
        )
    summary = pd.DataFrame(rows)
    metrics = {
        "failure_theory_agreement_rate": float(
            runs["theory_agreement"].mean()
        ),
        "zero_reserve_positive_failure_recovery_rate": float(
            runs.loc[
                np.isclose(runs["reserve_delta"], 0.0)
                & (runs["failure_fraction_nominal"] > 0.0),
                "recovery_feasible",
            ].mean()
        ),
        "max_tested_failure_fraction": float(
            runs["failure_fraction_nominal"].max()
        ),
    }
    return summary, metrics


def _heterogeneity_analysis(
    runs: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    confidence = float(config["analysis"]["confidence_level"])
    modes = list(config["heterogeneity"]["capacity_modes"])
    rows: list[dict[str, Any]] = []
    for (mode, scenario), block in runs.groupby(
        ["capacity_mode", "scenario"], sort=False
    ):
        false_count = int(block["hungarian_false_feasible"].sum())
        low, high = _wilson_interval(
            false_count,
            len(block),
            confidence=confidence,
        )
        false_block = block.loc[block["hungarian_false_feasible"]]
        certified_count = int(block["milp_optimal_certified"].sum())
        certified_low, certified_high = _wilson_interval(
            certified_count,
            len(block),
            confidence=confidence,
        )
        rescue_count = int(false_block["milp_rescues_false_feasible"].sum())
        rescue_low, rescue_high = _wilson_interval(
            rescue_count,
            len(false_block),
            confidence=confidence,
        )
        rows.append(
            {
                "capacity_mode": mode,
                "capacity_label": CAPACITY_LABELS[mode],
                "scenario": scenario,
                "scenario_label": SCENARIO_LABELS[scenario],
                "n_worlds": len(block),
                "false_feasible_count": false_count,
                "capacity_cv_median": float(block["capacity_cv"].median()),
                "false_feasible_rate": false_count / len(block),
                "false_feasible_ci_low": low,
                "false_feasible_ci_high": high,
                "shortfall_kg_median_when_false": (
                    float(false_block["hungarian_total_shortfall_kg"].median())
                    if not false_block.empty
                    else 0.0
                ),
                "milp_certification_rate": float(
                    block["milp_optimal_certified"].mean()
                ),
                "milp_certified_count": certified_count,
                "milp_certification_ci_low": certified_low,
                "milp_certification_ci_high": certified_high,
                "milp_rescue_rate_among_false": (
                    float(false_block["milp_rescues_false_feasible"].mean())
                    if not false_block.empty
                    else math.nan
                ),
                "milp_rescue_count": rescue_count,
                "milp_rescue_ci_low": rescue_low,
                "milp_rescue_ci_high": rescue_high,
            }
        )
    summary = pd.DataFrame(rows)

    contrast_rows: list[dict[str, Any]] = []
    p_values: dict[str, float] = {}
    key_columns = ["world_id"]
    homogeneous_rows = runs.loc[
        runs["capacity_mode"] == "homogeneous",
        key_columns + ["hungarian_false_feasible"],
    ].rename(columns={"hungarian_false_feasible": "homogeneous_false"})
    for mode in modes:
        if mode == "homogeneous":
            continue
        mode_rows = runs.loc[
            runs["capacity_mode"] == mode,
            key_columns + ["hungarian_false_feasible"],
        ].rename(columns={"hungarian_false_feasible": "mode_false"})
        paired = homogeneous_rows.merge(mode_rows, on=key_columns, how="inner")
        b_count = int((~paired["homogeneous_false"] & paired["mode_false"]).sum())
        c_count = int((paired["homogeneous_false"] & ~paired["mode_false"]).sum())
        discordant = b_count + c_count
        p_value = (
            float(
                stats.binomtest(
                    b_count,
                    discordant,
                    p=0.5,
                    alternative="greater",
                ).pvalue
            )
            if discordant
            else 1.0
        )
        p_values[mode] = p_value
        contrast_rows.append(
            {
                "capacity_mode": mode,
                "n_pairs": len(paired),
                "discordant_heterogeneous_only": b_count,
                "discordant_homogeneous_only": c_count,
                "mcnemar_exact_p_raw": p_value,
            }
        )
    adjusted = _holm_adjust(p_values)
    contrasts = pd.DataFrame(contrast_rows)
    contrasts["mcnemar_exact_p_holm"] = contrasts["capacity_mode"].map(
        adjusted
    )
    contrasts["supported"] = contrasts["mcnemar_exact_p_holm"] < 0.05

    overall = (
        runs.groupby("capacity_mode", sort=False)
        .agg(
            worlds=("world_id", "count"),
            capacity_cv_median=("capacity_cv", "median"),
            false_feasible_rate=("hungarian_false_feasible", "mean"),
            milp_certification_rate=("milp_optimal_certified", "mean"),
        )
        .reset_index()
    )
    extreme = overall.loc[overall["capacity_mode"] == "extreme"].iloc[0]
    false_rows = runs.loc[runs["hungarian_false_feasible"]]
    uncertified = runs.loc[~runs["milp_optimal_certified"]]
    uncertified_false = false_rows.loc[
        ~false_rows["milp_optimal_certified"]
    ]
    metrics = {
        "heterogeneous_world_rows": int(len(runs)),
        "heterogeneity_contrasts_supported": int(contrasts["supported"].sum()),
        "heterogeneity_contrasts_total": len(contrasts),
        "extreme_false_feasible_rate": float(extreme["false_feasible_rate"]),
        "extreme_capacity_cv_median": float(extreme["capacity_cv_median"]),
        "milp_certification_rate": float(
            runs["milp_optimal_certified"].mean()
        ),
        "milp_audit_count": int(len(runs)),
        "milp_feasible_incumbent_count": int(runs["milp_feasible"].sum()),
        "milp_certified_count": int(runs["milp_optimal_certified"].sum()),
        "milp_uncertified_count": int(len(uncertified)),
        "false_feasible_count": int(len(false_rows)),
        "milp_rescue_count_among_false": int(
            false_rows["milp_rescues_false_feasible"].sum()
        ),
        "milp_uncertified_false_count": int(len(uncertified_false)),
        "milp_uncertified_gap_min": float(uncertified["milp_mip_gap"].min()),
        "milp_uncertified_gap_max": float(uncertified["milp_mip_gap"].max()),
        "milp_time_limit_s": float(
            config["heterogeneity"]["milp_time_limit_s"]
        ),
        "heterogeneity_supported_max_p_holm": float(
            contrasts.loc[contrasts["supported"], "mcnemar_exact_p_holm"].max()
        ),
        "milp_rescue_rate_among_false": (
            float(false_rows["milp_rescues_false_feasible"].mean())
            if not false_rows.empty
            else math.nan
        ),
    }
    return summary, contrasts, metrics


def _plot_quality(
    summary: pd.DataFrame,
    diagnostic: pd.DataFrame,
    runs: pd.DataFrame,
    output_dir: Path,
    config: Mapping[str, Any],
) -> list[Path]:
    scenario_order = list(config["quality"]["scenarios"])
    ordered = summary.set_index("scenario").loc[scenario_order].reset_index()
    positions = np.arange(len(ordered))
    figure, axes = plt.subplots(
        1,
        2,
        figsize=(JOURNAL_WIDTH_IN, JOURNAL_HEIGHT_IN),
        gridspec_kw={"width_ratios": [0.95, 1.05]},
    )

    estimates = 100.0 * ordered["relative_saving_median"].to_numpy(float)
    lower = 100.0 * ordered["relative_saving_ci_low"].to_numpy(float)
    upper = 100.0 * ordered["relative_saving_ci_high"].to_numpy(float)
    supported = ordered["saving_over_5pct_supported"].to_numpy(bool)
    axes[0].errorbar(
        estimates,
        positions,
        xerr=np.vstack((estimates - lower, upper - estimates)),
        fmt="none",
        ecolor=COLORS["dark"],
        elinewidth=0.9,
        capsize=2.5,
        zorder=2,
    )
    axes[0].scatter(
        estimates[supported],
        positions[supported],
        s=34,
        marker="o",
        facecolor=COLORS["orange"],
        edgecolor=COLORS["dark"],
        linewidth=0.55,
        zorder=3,
    )
    axes[0].scatter(
        estimates[~supported],
        positions[~supported],
        s=34,
        marker="D",
        facecolor="white",
        edgecolor=COLORS["blue"],
        linewidth=1.0,
        zorder=3,
    )
    axes[0].axvline(
        5.0,
        color=COLORS["red"],
        linestyle="--",
        linewidth=1.0,
    )
    for position, estimate, effect in zip(
        positions,
        estimates,
        ordered["rank_biserial_vs_5pct"].to_numpy(float),
        strict=True,
    ):
        axes[0].annotate(
            rf"$r_{{rb}}={_decimal_comma(effect, 2)}$",
            (estimate, position),
            xytext=(5, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=6.2,
            color=COLORS["gray"],
        )
    axes[0].set_yticks(positions, ordered["scenario_label"])
    axes[0].invert_yaxis()
    axes[0].set(
        xlabel="Ahorro frente a greedy [%]",
        title="Efecto pareado: mediana e IC 95 %",
        xlim=(0.5, 13.8),
    )
    axes[0].legend(
        handles=[
            Line2D(
                [0], [0], marker="o", color="none",
                markerfacecolor=COLORS["orange"],
                markeredgecolor=COLORS["dark"], label="gate superado",
            ),
            Line2D(
                [0], [0], marker="D", color="none",
                markerfacecolor="white", markeredgecolor=COLORS["blue"],
                label="gate no superado",
            ),
            Line2D(
                [0], [0], color=COLORS["red"], linestyle="--",
                label="umbral 5 %",
            ),
        ],
        loc="upper left",
        fontsize=6.4,
    )

    cell_order = [
        (int(slots), quota)
        for slots in config["quality"]["slots"]
        for quota in config["quality"]["quota_modes"]
        if (
            (diagnostic["M"] == int(slots))
            & (diagnostic["quota_mode"] == quota)
        ).any()
    ]
    diagnostic_indexed = diagnostic.set_index(
        ["scenario", "M", "quota_mode"]
    )
    heatmap = np.asarray(
        [
            [
                100.0
                * float(
                    diagnostic_indexed.loc[
                        (scenario, slots, quota),
                        "relative_saving_median",
                    ]
                )
                for slots, quota in cell_order
            ]
            for scenario in scenario_order
        ]
    )
    cmap = LinearSegmentedColormap.from_list(
        "viu_quality_threshold",
        [COLORS["blue"], "#F8FAFC", COLORS["orange"]],
    )
    norm = TwoSlopeNorm(
        vmin=min(0.0, float(np.nanmin(heatmap))),
        vcenter=5.0,
        vmax=max(5.01, float(np.nanmax(heatmap))),
    )
    image = axes[1].imshow(
        heatmap,
        cmap=cmap,
        norm=norm,
        aspect="auto",
        interpolation="nearest",
    )
    for row_index in range(heatmap.shape[0]):
        for column_index in range(heatmap.shape[1]):
            value = float(heatmap[row_index, column_index])
            axes[1].text(
                column_index,
                row_index,
                _decimal_comma(value, 1),
                ha="center",
                va="center",
                fontsize=5.9,
                fontweight="bold" if value > 5.0 else "normal",
                color=(
                    "white"
                    if value >= 10.0
                    else COLORS["dark"]
                ),
            )
    quota_initial = {"symmetric": "S", "moderate": "M", "extreme": "E"}
    axes[1].set_xticks(
        np.arange(len(cell_order)),
        [
            f"{slots}\n{quota_initial.get(quota, str(quota)[:1].upper())}"
            for slots, quota in cell_order
        ],
    )
    axes[1].set_yticks(
        np.arange(len(scenario_order)),
        [SCENARIO_LABELS[scenario] for scenario in scenario_order],
    )
    axes[1].set(
        xlabel="$M$ puestos · cuota S/M/E",
        title="Diagnóstico posterior: mediana por celda [%]",
    )
    colorbar = figure.colorbar(image, ax=axes[1], fraction=0.045, pad=0.025)
    colorbar.set_label("Ahorro mediano [%]", fontsize=7.2)
    colorbar.ax.yaxis.set_major_formatter(FuncFormatter(_comma_tick))
    axes[1].text(
        0.0,
        -0.27,
        "S: simétrica · M: moderada · E: extrema · blanco: umbral 5 %",
        transform=axes[1].transAxes,
        fontsize=6.1,
        color=COLORS["gray"],
    )
    label_panels(axes)
    figure.tight_layout(pad=0.45, w_pad=1.15)
    return save_figure(figure, output_dir / "n1_quality_scenarios", tight=False)


def _plot_scaling(
    summary: pd.DataFrame,
    output_dir: Path,
    metrics: Mapping[str, Any],
) -> list[Path]:
    figure, axes = plt.subplots(
        1, 2, figsize=(JOURNAL_WIDTH_IN, JOURNAL_HEIGHT_IN)
    )
    for ratio in sorted(summary["slot_to_robot_ratio"].unique()):
        block = summary.loc[
            np.isclose(summary["slot_to_robot_ratio"], ratio)
        ].sort_values("N")
        color = ASPECT_COLORS.get(float(ratio), COLORS["blue"])
        marker = ASPECT_MARKERS.get(float(ratio), "o")
        axes[0].plot(
            block["N"],
            block["solver_ms_median"],
            marker=marker,
            color=color,
            label=rf"$M/N={_decimal_comma(float(ratio), 2)}$",
        )
        axes[0].fill_between(
            block["N"],
            block["solver_ms_p05"],
            block["solver_ms_p95"],
            color=color,
            alpha=0.12,
        )
        axes[0].plot(
            block["N"],
            block["total_ms_median"],
            color=color,
            linestyle=":",
            linewidth=1.0,
            alpha=0.9,
            label="_nolegend_",
        )
        axes[1].plot(
            block["N"],
            block["matrix_mib_median"],
            marker=marker,
            color=color,
            label=rf"$M/N={_decimal_comma(float(ratio), 2)}$",
        )
    balanced = summary.loc[
        np.isclose(summary["slot_to_robot_ratio"], 1.0)
    ].sort_values("N")
    fit_x = np.geomspace(float(balanced["N"].min()), float(balanced["N"].max()), 80)
    fit_y = (
        float(metrics["solver_power_scale"])
        * fit_x ** float(metrics["solver_power_exponent"])
    )
    axes[0].plot(
        fit_x,
        fit_y,
        color=COLORS["dark"],
        linestyle="--",
        linewidth=1.0,
        label=(
            rf"ajuste $N=M$: $N^{{"
            f"{_decimal_comma(float(metrics['solver_power_exponent']), 2)}"
            r"}$"
        ),
        zorder=4,
    )
    axes[0].set(
        xscale="log",
        yscale="log",
        xlabel="Robots, $N$",
        ylabel="Tiempo del solver [ms]",
        title="Solver y pipeline total por mundo",
    )
    axes[0].legend(loc="upper left", ncols=2, fontsize=6.2)
    axes[0].text(
        0.98,
        0.05,
        (
            rf"$n={metrics['solver_power_fit_points']}$ tamaños balanceados"
            "\n"
            "IC 95 % ["
            f"{_decimal_comma(float(metrics['solver_power_ci_low']), 2)}; "
            f"{_decimal_comma(float(metrics['solver_power_ci_high']), 2)}]"
            "\n"
            rf"$R^2={_decimal_comma(float(metrics['solver_power_r_squared']), 3)}$"
            " · descriptivo"
        ),
        transform=axes[0].transAxes,
        ha="right",
        va="bottom",
        fontsize=6.3,
        color=COLORS["dark"],
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": COLORS["light_gray"],
        },
    )
    axes[0].text(
        0.03,
        0.37,
        "línea continua: solver P50 [P05, P95]\nlínea de puntos: pipeline total P50",
        transform=axes[0].transAxes,
        ha="left",
        va="top",
        fontsize=6.1,
        color=COLORS["gray"],
    )
    axes[1].set(
        xscale="log",
        yscale="log",
        xlabel="Robots, $N$",
        ylabel="Huella mínima de $C$ [MiB]",
        title="Almacenamiento del ndarray denso",
    )
    axes[1].legend(loc="upper left", fontsize=6.4)
    label_panels(axes)
    figure.tight_layout(pad=0.45, w_pad=1.15)
    return save_figure(figure, output_dir / "n1_central_scaling", tight=False)


def _plot_boundary(
    failure_summary: pd.DataFrame,
    heterogeneity_summary: pd.DataFrame,
    heterogeneity_runs: pd.DataFrame,
    output_dir: Path,
) -> list[Path]:
    figure, axes = plt.subplots(
        1, 2, figsize=(JOURNAL_WIDTH_IN, JOURNAL_HEIGHT_IN)
    )
    deltas = sorted(failure_summary["reserve_delta"].unique())
    fractions = sorted(
        failure_summary["failure_fraction_nominal"].unique()
    )
    pivot = failure_summary.pivot(
        index="reserve_delta",
        columns="failure_fraction_nominal",
        values="recovery_rate",
    ).loc[deltas, fractions]
    cmap = LinearSegmentedColormap.from_list(
        "viu_recovery",
        ["#F7D7D2", "#FFF4E8", "#DDF2E7", COLORS["green"]],
    )
    image = axes[0].imshow(
        pivot.to_numpy(float),
        vmin=0.0,
        vmax=1.0,
        cmap=cmap,
        aspect="auto",
        origin="lower",
    )
    axes[0].set_xticks(
        np.arange(len(fractions)),
        [f"{100*value:.0f}" for value in fractions],
    )
    axes[0].set_yticks(
        np.arange(len(deltas)),
        [f"{value:.2f}" for value in deltas],
    )
    axes[0].set(
        xlabel="Robots retirados [%]",
        ylabel=r"Reserva estructural, $\delta$",
        title="Recuperación central tras el fallo",
    )
    for row_index, delta in enumerate(deltas):
        for column_index, fraction in enumerate(fractions):
            value = float(pivot.loc[delta, fraction])
            axes[0].text(
                column_index,
                row_index,
                f"{100*value:.0f}%",
                ha="center",
                va="center",
                fontsize=8.2,
                fontweight="bold",
                color="white" if value > 0.75 else COLORS["dark"],
            )
        boundary = 2.0 * delta / (1.0 + delta)
        axes[0].text(
            len(fractions) - 0.55,
            row_index + 0.30,
            rf"$f^*={100*boundary:.0f}\%$",
            ha="right",
            va="center",
            fontsize=7.2,
            color=COLORS["dark"],
        )
    colorbar = figure.colorbar(image, ax=axes[0], fraction=0.045, pad=0.03)
    colorbar.set_label("Fracción factible", fontsize=8.2)

    scenario_order = [
        scenario
        for scenario in SCENARIO_LABELS
        if scenario in set(heterogeneity_summary["scenario"])
    ]
    capacity_order = [
        mode
        for mode in CAPACITY_LABELS
        if mode in set(heterogeneity_summary["capacity_mode"])
    ]
    for scenario in scenario_order:
        block = heterogeneity_summary.loc[
            heterogeneity_summary["scenario"] == scenario
        ].set_index("capacity_mode").loc[capacity_order].reset_index()
        axes[1].plot(
            block["capacity_cv_median"],
            100.0 * block["false_feasible_rate"],
            color=COLORS["gray"],
            alpha=0.38,
            linewidth=1.0,
            marker="o",
            markersize=3.3,
        )
    overall_rows: list[dict[str, float]] = []
    for mode in capacity_order:
        block = heterogeneity_runs.loc[
            heterogeneity_runs["capacity_mode"] == mode
        ]
        successes = int(block["hungarian_false_feasible"].sum())
        low, high = _wilson_interval(successes, len(block), confidence=0.95)
        overall_rows.append(
            {
                "cv": float(block["capacity_cv"].median()),
                "rate": successes / len(block),
                "low": low,
                "high": high,
            }
        )
    overall = pd.DataFrame(overall_rows)
    rates = 100.0 * overall["rate"].to_numpy(float)
    lows = 100.0 * overall["low"].to_numpy(float)
    highs = 100.0 * overall["high"].to_numpy(float)
    axes[1].errorbar(
        overall["cv"],
        rates,
        yerr=np.vstack(
            (
                np.maximum(0.0, rates - lows),
                np.maximum(0.0, highs - rates),
            )
        ),
        color=COLORS["orange"],
        marker="o",
        linewidth=2.1,
        capsize=3,
        label="agregado · IC 95 % Wilson",
        zorder=4,
    )
    for index, mode in enumerate(capacity_order):
        axes[1].annotate(
            CAPACITY_LABELS[mode],
            (overall.iloc[index]["cv"], rates[index]),
            xytext=(0, 8 if index % 2 == 0 else -13),
            textcoords="offset points",
            ha="center",
            fontsize=7.0,
            color=COLORS["dark"],
        )
    axes[1].set(
        xlabel=r"Heterogeneidad realizada, $\mathrm{CV}(c_i^{\mathrm{pay}})$",
        ylabel="Falsos factibles de N1 [%]",
        ylim=(-3.0, 103.0),
        title="La capacidad individual rompe los slots",
    )
    axes[1].legend(loc="lower right")
    axes[1].text(
        0.01,
        -0.22,
        "Líneas grises: escenarios; naranja: batería agregada.",
        transform=axes[1].transAxes,
        fontsize=7.5,
        color=COLORS["gray"],
    )
    label_panels(axes)
    figure.tight_layout(pad=0.45, w_pad=1.05)
    return save_figure(figure, output_dir / "n1_validity_boundary", tight=False)


def _plot_failure_recovery(
    failure_summary: pd.DataFrame,
    output_dir: Path,
) -> list[Path]:
    """Plot the recoverability boundary and the cost of static reallocation."""

    figure, axes = plt.subplots(
        1, 2, figsize=(JOURNAL_WIDTH_IN, JOURNAL_HEIGHT_IN)
    )
    deltas = sorted(failure_summary["reserve_delta"].unique())
    fractions = sorted(failure_summary["failure_fraction_nominal"].unique())
    pivot = failure_summary.pivot(
        index="reserve_delta",
        columns="failure_fraction_nominal",
        values="recovery_rate",
    ).loc[deltas, fractions]
    cmap = LinearSegmentedColormap.from_list(
        "viu_recovery_detail", ["#F2E7E3", "#DCEAF5"]
    )
    fraction_percent = 100.0 * np.asarray(fractions, dtype=float)
    delta_values = np.asarray(deltas, dtype=float)

    def cell_edges(values: np.ndarray) -> np.ndarray:
        midpoints = (values[:-1] + values[1:]) / 2.0
        first = values[0] - (midpoints[0] - values[0])
        last = values[-1] + (values[-1] - midpoints[-1])
        return np.concatenate(([first], midpoints, [last]))

    axes[0].pcolormesh(
        cell_edges(fraction_percent),
        cell_edges(delta_values),
        pivot.to_numpy(float),
        vmin=0.0,
        vmax=1.0,
        cmap=cmap,
        shading="flat",
    )
    axes[0].set_xticks(
        fraction_percent,
        [f"{100 * value:.0f}" for value in fractions],
    )
    axes[0].set_yticks(
        delta_values,
        [
            (
                f"{_decimal_comma(float(value), 2)}  |  "
                f"{100 * (2.0 * value / (1.0 + value)):.0f}%"
            )
            for value in deltas
        ],
    )
    axes[0].set(
        xlabel="Robots retirados [%]",
        ylabel=r"Reserva $\delta$  |  frontera $f^*(\delta)$",
        title="Frontera cardinal observada",
    )
    for row_index, delta in enumerate(deltas):
        for column_index, fraction in enumerate(fractions):
            value = float(pivot.loc[delta, fraction])
            cell = failure_summary.loc[
                np.isclose(failure_summary["reserve_delta"], delta)
                & np.isclose(
                    failure_summary["failure_fraction_nominal"], fraction
                )
            ].iloc[0]
            axes[0].text(
                100.0 * fraction,
                delta,
                f"{int(cell['recovery_count'])}/{int(cell['n_worlds'])}",
                ha="center",
                va="center",
                fontsize=6.6,
                fontweight="bold",
                color=COLORS["dark"],
            )

    for index, delta in enumerate(deltas):
        block = failure_summary.loc[
            np.isclose(failure_summary["reserve_delta"], delta)
        ].sort_values("failure_fraction_nominal")
        feasible = block["recovery_rate"] > 0.0
        color = [
            COLORS["gray"],
            COLORS["blue"],
            COLORS["green"],
            COLORS["orange"],
        ][index]
        feasible_block = block.loc[feasible]
        x_values = 100.0 * feasible_block["failure_fraction_nominal"].to_numpy(float)
        medians = 100.0 * feasible_block["relative_cost_increase_median"].to_numpy(float)
        lows = 100.0 * feasible_block["relative_cost_increase_ci_low"].to_numpy(float)
        highs = 100.0 * feasible_block["relative_cost_increase_ci_high"].to_numpy(float)
        axes[1].fill_between(
            x_values,
            lows,
            highs,
            color=color,
            alpha=0.13,
            linewidth=0.0,
        )
        axes[1].plot(
            x_values,
            medians,
            marker="o",
            linewidth=1.45,
            color=color,
            label=rf"$\delta={_decimal_comma(float(delta), 2)}$",
        )
    axes[1].set(
        xlabel="Robots retirados [%]",
        ylabel="Aumento mediano de coste [%]",
        title="Coste del recálculo factible",
        xlim=(-1.0, 31.0),
        ylim=(-2.0, 60.0),
    )
    axes[1].legend(loc="upper left", ncols=2, fontsize=6.3)

    axes[0].grid(False)
    axes[1].grid(True, which="major", linewidth=0.55, alpha=0.38)
    axes[1].set_axisbelow(True)
    label_panels(axes)
    figure.tight_layout(pad=0.45, w_pad=1.15)
    return save_figure(figure, output_dir / "n1_failure_recovery", tight=False)


def _plot_heterogeneity_boundary(
    heterogeneity_summary: pd.DataFrame,
    heterogeneity_runs: pd.DataFrame,
    output_dir: Path,
) -> list[Path]:
    """Plot false feasibility and the MILP audit under individual capacities."""

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(JOURNAL_WIDTH_IN, JOURNAL_HEIGHT_IN),
        gridspec_kw={"width_ratios": [1.08, 0.92]},
    )
    scenario_order = [
        scenario
        for scenario in SCENARIO_LABELS
        if scenario in set(heterogeneity_summary["scenario"])
    ]
    capacity_order = [
        mode
        for mode in CAPACITY_LABELS
        if mode in set(heterogeneity_summary["capacity_mode"])
    ]
    for scenario in scenario_order:
        block = heterogeneity_summary.loc[
            heterogeneity_summary["scenario"] == scenario
        ].set_index("capacity_mode").loc[capacity_order].reset_index()
        axes[0].plot(
            block["capacity_cv_median"],
            100.0 * block["false_feasible_rate"],
            color=COLORS["light_gray"],
            linewidth=0.8,
            marker="o",
            markersize=2.7,
            alpha=0.75,
        )

    confidence = 0.95
    overall_rows: list[dict[str, float | str | int]] = []
    for mode in capacity_order:
        block = heterogeneity_runs.loc[
            heterogeneity_runs["capacity_mode"] == mode
        ]
        false_rows = block.loc[block["hungarian_false_feasible"]]
        successes = int(block["hungarian_false_feasible"].sum())
        low, high = _wilson_interval(successes, len(block), confidence=confidence)
        certified = int(block["milp_optimal_certified"].sum())
        cert_low, cert_high = _wilson_interval(
            certified, len(block), confidence=confidence
        )
        rescued = int(false_rows["milp_rescues_false_feasible"].sum())
        rescue_low, rescue_high = _wilson_interval(
            rescued, len(false_rows), confidence=confidence
        )
        overall_rows.append(
            {
                "mode": mode,
                "cv": float(block["capacity_cv"].median()),
                "false_rate": successes / len(block),
                "low": low,
                "high": high,
                "certification": certified / len(block),
                "certification_low": cert_low,
                "certification_high": cert_high,
                "certified": certified,
                "audits": len(block),
                "rescue": (
                    rescued / len(false_rows)
                    if not false_rows.empty
                    else math.nan
                ),
                "rescue_low": rescue_low,
                "rescue_high": rescue_high,
                "rescued": rescued,
                "false_total": len(false_rows),
            }
        )
    overall = pd.DataFrame(overall_rows)
    rates = 100.0 * overall["false_rate"].to_numpy(float)
    lows = 100.0 * overall["low"].to_numpy(float)
    highs = 100.0 * overall["high"].to_numpy(float)
    axes[0].errorbar(
        overall["cv"],
        rates,
        yerr=np.vstack(
            (np.maximum(0.0, rates - lows), np.maximum(0.0, highs - rates))
        ),
        color=COLORS["orange"],
        marker="o",
        linewidth=2.1,
        capsize=3,
        label="agregado · IC 95 % Wilson",
        zorder=4,
    )
    annotation_offsets = {
        "homogeneous": (6, 7),
        "low": (0, -13),
        "moderate": (0, 8),
        "high": (0, -13),
        "extreme": (-5, 8),
    }
    for index, mode in enumerate(capacity_order):
        offset = annotation_offsets.get(mode, (0, 8))
        axes[0].annotate(
            CAPACITY_LABELS[mode],
            (overall.iloc[index]["cv"], rates[index]),
            xytext=offset,
            textcoords="offset points",
            ha="left" if mode == "homogeneous" else "center",
            fontsize=6.2,
            color=COLORS["dark"],
        )
    axes[0].set(
        xlabel=r"Heterogeneidad realizada, $\mathrm{CV}(c_i^{\mathrm{pay}})$",
        ylabel="Falsos factibles de N1 [%]",
        ylim=(-3.0, 103.0),
        title="Falsos factibles del modelo por puestos",
    )
    axes[0].legend(loc="lower right", fontsize=6.4)

    positions = np.arange(len(capacity_order), dtype=float)
    certification = 100.0 * overall["certification"].to_numpy(float)
    cert_low = 100.0 * overall["certification_low"].to_numpy(float)
    cert_high = 100.0 * overall["certification_high"].to_numpy(float)
    rescue = 100.0 * overall["rescue"].to_numpy(float)
    rescue_low = 100.0 * overall["rescue_low"].to_numpy(float)
    rescue_high = 100.0 * overall["rescue_high"].to_numpy(float)
    axes[1].errorbar(
        certification,
        positions + 0.12,
        xerr=np.vstack(
            (
                np.maximum(0.0, certification - cert_low),
                np.maximum(0.0, cert_high - certification),
            )
        ),
        fmt="o",
        color=COLORS["blue"],
        markersize=4.0,
        capsize=2.4,
        linewidth=1.0,
        label="certificación / auditorías",
    )
    finite_rescue = np.isfinite(rescue)
    axes[1].errorbar(
        rescue[finite_rescue],
        positions[finite_rescue] - 0.12,
        xerr=np.vstack(
            (
                np.maximum(
                    0.0,
                    rescue[finite_rescue] - rescue_low[finite_rescue],
                ),
                np.maximum(
                    0.0,
                    rescue_high[finite_rescue] - rescue[finite_rescue],
                ),
            )
        ),
        fmt="s",
        markerfacecolor="white",
        color=COLORS["green"],
        markersize=4.0,
        capsize=2.4,
        linewidth=1.0,
        label="rescate / falsos factibles",
    )
    count_column_x = 100.15
    for index, row in overall.iterrows():
        axes[1].text(
            count_column_x,
            positions[index] + 0.12,
            f"{int(row['certified'])}/{int(row['audits'])}",
            ha="left",
            va="center",
            fontsize=5.8,
            color=COLORS["blue"],
        )
        if int(row["false_total"]) > 0:
            axes[1].text(
                count_column_x,
                positions[index] - 0.12,
                f"{int(row['rescued'])}/{int(row['false_total'])}",
                ha="left",
                va="center",
                fontsize=5.8,
                color=COLORS["green"],
            )
        else:
            axes[1].text(
                94.0,
                positions[index] + 0.12,
                "rescate n/a",
                ha="left",
                va="center",
                fontsize=5.8,
                color=COLORS["gray"],
            )
    axes[1].set_yticks(
        positions, [CAPACITY_LABELS[mode] for mode in capacity_order]
    )
    axes[1].set(
        xlabel="Tasa [%] · vista ampliada",
        xlim=(93.5, 101.25),
        title="Auditoría MILP: estimado e IC 95 %",
    )
    axes[1].invert_yaxis()
    axes[1].axvline(100.0, color=COLORS["light_gray"], linewidth=0.8)
    axes[1].legend(loc="lower left", fontsize=6.1)

    axes[0].grid(True, axis="both", linewidth=0.55, alpha=0.38)
    axes[1].grid(True, axis="x", linewidth=0.55, alpha=0.38)
    for axis in axes:
        axis.set_axisbelow(True)
    label_panels(axes)
    figure.tight_layout(pad=0.45, w_pad=1.05)
    return save_figure(
        figure,
        output_dir / "n1_heterogeneity_boundary",
        tight=False,
    )


def _plot_operating_envelope(
    scaling_summary: pd.DataFrame,
    scaling_metrics: Mapping[str, Any],
    failure_summary: pd.DataFrame,
    heterogeneity_summary: pd.DataFrame,
    heterogeneity_runs: pd.DataFrame,
    output_dir: Path,
) -> list[Path]:
    """Synthesize computation, static recourse and model validity in one plate."""

    figure, axes = plt.subplots(
        1, 3, figsize=(JOURNAL_WIDTH_IN, JOURNAL_HEIGHT_IN)
    )

    # A. Measured centralized solver time.
    for ratio in sorted(scaling_summary["slot_to_robot_ratio"].unique()):
        block = scaling_summary.loc[
            np.isclose(scaling_summary["slot_to_robot_ratio"], ratio)
        ].sort_values("N")
        color = ASPECT_COLORS.get(float(ratio), COLORS["blue"])
        axes[0].plot(
            block["N"],
            block["solver_ms_median"],
            marker="o",
            markersize=3.8,
            linewidth=1.35,
            color=color,
            label=rf"$M/N={ratio:.2f}$",
        )
        axes[0].fill_between(
            block["N"],
            block["solver_ms_p05"],
            block["solver_ms_p95"],
            color=color,
            alpha=0.10,
            linewidth=0,
        )
    axes[0].set(
        xscale="log",
        yscale="log",
        xlabel="robots, $N$",
        ylabel="tiempo solver [ms]",
        title="Coste del oráculo central",
    )
    axes[0].legend(loc="upper left", fontsize=6.8, frameon=True)
    axes[0].text(
        0.97,
        0.05,
        (
            rf"$N=M$: $\hat\beta={scaling_metrics['solver_power_exponent']:.2f}$"
            "\n"
            rf"IC 95 % [{scaling_metrics['solver_power_ci_low']:.2f}, "
            rf"{scaling_metrics['solver_power_ci_high']:.2f}]"
            "\najuste descriptivo"
        ),
        transform=axes[0].transAxes,
        ha="right",
        va="bottom",
        fontsize=7.0,
        color=COLORS["dark"],
        bbox={
            "boxstyle": "round,pad=0.30",
            "facecolor": "white",
            "edgecolor": COLORS["light_gray"],
            "linewidth": 0.7,
        },
    )

    # B. Static centralized recovery after robot withdrawal.
    deltas = sorted(failure_summary["reserve_delta"].unique())
    fractions = sorted(failure_summary["failure_fraction_nominal"].unique())
    pivot = failure_summary.pivot(
        index="reserve_delta",
        columns="failure_fraction_nominal",
        values="recovery_rate",
    ).loc[deltas, fractions]
    cmap = LinearSegmentedColormap.from_list(
        "viu_recovery_compact",
        ["#F7D7D2", "#FFF4E8", "#DDF2E7", COLORS["green"]],
    )
    axes[1].imshow(
        pivot.to_numpy(float),
        vmin=0.0,
        vmax=1.0,
        cmap=cmap,
        aspect="auto",
        origin="lower",
    )
    axes[1].set_xticks(
        np.arange(len(fractions)),
        [f"{100 * value:.0f}" for value in fractions],
    )
    axes[1].set_yticks(
        np.arange(len(deltas)),
        [f"{value:.2f}" for value in deltas],
    )
    axes[1].set(
        xlabel="robots retirados [%]",
        ylabel=r"reserva $\delta$",
        title="Recálculo postfallo",
    )
    for row_index, delta in enumerate(deltas):
        for column_index, fraction in enumerate(fractions):
            value = float(pivot.loc[delta, fraction])
            axes[1].text(
                column_index,
                row_index,
                f"{100 * value:.0f}",
                ha="center",
                va="center",
                fontsize=7.2,
                fontweight="bold",
                color="white" if value > 0.75 else COLORS["dark"],
            )
    axes[1].text(
        0.02,
        0.98,
        "celdas: factibilidad [%]",
        transform=axes[1].transAxes,
        ha="left",
        va="top",
        fontsize=6.8,
        color=COLORS["gray"],
        bbox={
            "boxstyle": "round,pad=0.22",
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.88,
        },
    )

    # C. External-validity audit under individual capacities.
    scenario_order = [
        scenario
        for scenario in SCENARIO_LABELS
        if scenario in set(heterogeneity_summary["scenario"])
    ]
    capacity_order = [
        mode
        for mode in CAPACITY_LABELS
        if mode in set(heterogeneity_summary["capacity_mode"])
    ]
    for scenario in scenario_order:
        block = heterogeneity_summary.loc[
            heterogeneity_summary["scenario"] == scenario
        ].set_index("capacity_mode").loc[capacity_order].reset_index()
        axes[2].plot(
            block["capacity_cv_median"],
            100.0 * block["false_feasible_rate"],
            color=COLORS["light_gray"],
            linewidth=0.9,
            marker="o",
            markersize=2.6,
            alpha=0.85,
        )
    overall_rows: list[dict[str, float]] = []
    for mode in capacity_order:
        block = heterogeneity_runs.loc[
            heterogeneity_runs["capacity_mode"] == mode
        ]
        successes = int(block["hungarian_false_feasible"].sum())
        low, high = _wilson_interval(successes, len(block), confidence=0.95)
        overall_rows.append(
            {
                "cv": float(block["capacity_cv"].median()),
                "rate": successes / len(block),
                "low": low,
                "high": high,
            }
        )
    overall = pd.DataFrame(overall_rows)
    rates = 100.0 * overall["rate"].to_numpy(float)
    lows = 100.0 * overall["low"].to_numpy(float)
    highs = 100.0 * overall["high"].to_numpy(float)
    axes[2].errorbar(
        overall["cv"],
        rates,
        yerr=np.vstack(
            (np.maximum(0.0, rates - lows), np.maximum(0.0, highs - rates))
        ),
        color=COLORS["orange"],
        marker="o",
        markersize=4.2,
        linewidth=1.7,
        capsize=2.5,
        label="agregado · IC 95 %",
        zorder=4,
    )
    for index, mode in enumerate(capacity_order):
        axes[2].annotate(
            CAPACITY_LABELS[mode],
            (overall.iloc[index]["cv"], rates[index]),
            xytext=(0, 8 if index % 2 == 0 else -13),
            textcoords="offset points",
            ha="center",
            fontsize=6.4,
            color=COLORS["dark"],
        )
    axes[2].set(
        xlabel=r"heterogeneidad, $\mathrm{CV}(c_i^{\mathrm{pay}})$",
        ylabel="falsos factibles N1 [%]",
        ylim=(-4.0, 104.0),
        title="Ruptura de la reducción",
    )
    axes[2].legend(loc="lower right", fontsize=6.8, frameon=True)

    for axis in axes:
        axis.grid(True, which="major", linewidth=0.55, alpha=0.38)
        axis.set_axisbelow(True)
    label_panels(axes)
    figure.text(
        0.045,
        0.018,
        "A: rango medido, no ley asintótica · B: recálculo central estático · C: el MILP solo audita validez externa",
        ha="left",
        va="bottom",
        fontsize=6.1,
        color=COLORS["gray"],
    )
    figure.tight_layout(rect=(0.01, 0.075, 0.995, 0.99), w_pad=0.75)
    return save_figure(
        figure,
        output_dir / "n1_operating_envelope",
        tight=False,
    )


def _write_report(
    path: Path,
    metrics: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    lines = [
        "# SP1.N1 — campaña confirmatoria húngara homogénea",
        "",
        f"- Campaña: `{config['campaign_id']}`.",
        f"- Filas RAW: {metrics['raw_rows']:,}.",
        f"- Mundos de calidad: {metrics['quality_rows']:,}.",
        (
            "- Ahorro mediano frente a greedy: "
            f"{100*metrics['overall_saving_median']:.2f}% "
            f"(IC 95% {100*metrics['overall_saving_ci_low']:.2f}–"
            f"{100*metrics['overall_saving_ci_high']:.2f}%)."
        ),
        (
            "- Escenarios que superan el gate del 5% tras Holm: "
            f"{metrics['scenario_gates_passed']}/"
            f"{metrics['scenario_gates_total']}."
        ),
        (
            "- Sensibilidad exacta de signo: "
            + (
                "misma clasificación que el gate confirmatorio."
                if metrics["sign_sensitivity_matches_confirmatory_gate"]
                else "clasificación distinta; requiere discusión."
            )
        ),
        (
            "- Pendiente log-log balanceada observada: "
            f"{metrics['solver_power_exponent']:.3f} "
            f"(IC 95% {metrics['solver_power_ci_low']:.3f}–"
            f"{metrics['solver_power_ci_high']:.3f})."
        ),
        (
            "- Concordancia recuperación–frontera cardinal: "
            f"{100*metrics['failure_theory_agreement_rate']:.2f}%."
        ),
        (
            "- Falsos factibles con heterogeneidad extrema: "
            f"{100*metrics['extreme_false_feasible_rate']:.2f}%."
        ),
        (
            "- Rescate MILP certificado entre falsos factibles: "
            f"{100*metrics['milp_rescue_rate_among_false']:.2f}%."
        ),
        "",
        "## Alcance",
        "",
        "- El Húngaro es exacto únicamente para la reducción homogénea a slots.",
        "- Las regresiones describen el rango medido; no prueban complejidad asintótica.",
        "- El fallo se resuelve mediante un recálculo central estático.",
        "- El MILP heterogéneo actúa como auditor de validez externa y anticipa N2.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_level(
    *,
    config_path: Path,
    output_dir: Path,
    smoke: bool,
    reuse_raw: bool,
) -> dict[str, Any]:
    configure_publication_style()
    config = _load_config(config_path, smoke=smoke)
    raw_dir = output_dir / "raw"
    processed_dir = output_dir / "processed"
    figures_dir = output_dir / "figures"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    raw_paths = {
        "quality": raw_dir / "quality_runs.csv",
        "scaling": raw_dir / "scaling_runs.csv",
        "failure": raw_dir / "failure_runs.csv",
        "heterogeneity": raw_dir / "heterogeneity_runs.csv",
    }
    if reuse_raw:
        missing = [str(path) for path in raw_paths.values() if not path.is_file()]
        if missing:
            raise FileNotFoundError("Missing RAW files: " + ", ".join(missing))
        quality_runs = pd.read_csv(raw_paths["quality"])
        scaling_runs = pd.read_csv(raw_paths["scaling"])
        failure_runs = pd.read_csv(raw_paths["failure"])
        heterogeneity_runs = pd.read_csv(raw_paths["heterogeneity"])
    else:
        quality_runs = _run_quality(config)
        quality_runs.to_csv(raw_paths["quality"], index=False)
        scaling_runs = _run_scaling(config)
        scaling_runs.to_csv(raw_paths["scaling"], index=False)
        failure_runs = _run_failure(config)
        failure_runs.to_csv(raw_paths["failure"], index=False)
        heterogeneity_runs = _run_heterogeneity(config)
        heterogeneity_runs.to_csv(raw_paths["heterogeneity"], index=False)

    quality_summary, quality_metrics = _quality_analysis(quality_runs, config)
    quality_diagnostic = _quality_cell_diagnostic(quality_runs, config)
    scaling_summary, scaling_metrics = _scaling_analysis(scaling_runs, config)
    failure_summary, failure_metrics = _failure_analysis(failure_runs, config)
    (
        heterogeneity_summary,
        heterogeneity_contrasts,
        heterogeneity_metrics,
    ) = _heterogeneity_analysis(heterogeneity_runs, config)

    quality_summary.to_csv(
        processed_dir / "quality_scenario_summary.csv", index=False
    )
    quality_diagnostic.to_csv(
        processed_dir / "quality_cell_diagnostic.csv", index=False
    )
    scaling_summary.to_csv(processed_dir / "scaling_summary.csv", index=False)
    failure_summary.to_csv(processed_dir / "failure_summary.csv", index=False)
    heterogeneity_summary.to_csv(
        processed_dir / "heterogeneity_summary.csv", index=False
    )
    heterogeneity_contrasts.to_csv(
        processed_dir / "heterogeneity_contrasts.csv", index=False
    )

    figure_paths = []
    figure_paths += _plot_quality(
        quality_summary,
        quality_diagnostic,
        quality_runs,
        figures_dir,
        config,
    )
    figure_paths += _plot_scaling(
        scaling_summary, figures_dir, scaling_metrics
    )
    figure_paths += _plot_boundary(
        failure_summary,
        heterogeneity_summary,
        heterogeneity_runs,
        figures_dir,
    )
    figure_paths += _plot_failure_recovery(
        failure_summary,
        figures_dir,
    )
    figure_paths += _plot_heterogeneity_boundary(
        heterogeneity_summary,
        heterogeneity_runs,
        figures_dir,
    )
    figure_paths += _plot_operating_envelope(
        scaling_summary,
        scaling_metrics,
        failure_summary,
        heterogeneity_summary,
        heterogeneity_runs,
        figures_dir,
    )

    independent_worlds = set(quality_runs["world_id"])
    independent_worlds.update(scaling_runs["world_id"])
    independent_worlds.update(failure_runs["world_id"])
    independent_worlds.update(heterogeneity_runs["world_id"])
    metrics: dict[str, Any] = {
        "campaign_id": config["campaign_id"],
        "raw_rows": int(
            len(quality_runs)
            + len(scaling_runs)
            + len(failure_runs)
            + len(heterogeneity_runs)
        ),
        "independent_worlds": len(independent_worlds),
        "quality_rows": len(quality_runs),
        "scaling_rows": len(scaling_runs),
        "failure_rows": len(failure_runs),
        "heterogeneity_rows": len(heterogeneity_runs),
        "max_n": int(
            max(
                quality_runs["N"].max(),
                scaling_runs["N"].max(),
                failure_runs["N_original"].max(),
                heterogeneity_runs["N"].max(),
            )
        ),
        "homogeneous_capacity_model": True,
        **quality_metrics,
        **scaling_metrics,
        **failure_metrics,
        **heterogeneity_metrics,
    }
    metrics["quality_cells_per_scenario"] = int(
        quality_diagnostic.groupby("scenario").size().max()
    )
    for scenario, block in quality_diagnostic.groupby("scenario", sort=False):
        metrics[f"quality_{scenario}_cells_above_threshold"] = int(
            block["cells_above_practical_threshold"].sum()
        )
    diagnostic_target_quota = (
        "extreme"
        if "extreme" in set(quality_diagnostic["quota_mode"])
        else str(config["quality"]["quota_modes"][-1])
    )
    corridor_extreme_small = quality_diagnostic.loc[
        (quality_diagnostic["scenario"] == "corridor")
        & (quality_diagnostic["quota_mode"] == diagnostic_target_quota)
        & (quality_diagnostic["M"] == quality_diagnostic["M"].min())
    ]
    metrics["corridor_small_extreme_saving_median"] = float(
        corridor_extreme_small["relative_saving_median"].iloc[0]
    )
    for row in quality_summary.itertuples(index=False):
        scenario = str(row.scenario)
        metrics[f"saving_{scenario}_median"] = float(
            row.relative_saving_median
        )
        metrics[f"saving_{scenario}_ci_low"] = float(
            row.relative_saving_ci_low
        )
        metrics[f"saving_{scenario}_ci_high"] = float(
            row.relative_saving_ci_high
        )
    for capacity_mode, block in heterogeneity_runs.groupby(
        "capacity_mode", sort=False
    ):
        metrics[f"false_feasible_{capacity_mode}_rate"] = float(
            block["hungarian_false_feasible"].mean()
        )
        metrics[f"capacity_cv_{capacity_mode}_median"] = float(
            block["capacity_cv"].median()
        )
    metrics["failure_independent_worlds"] = int(
        failure_runs["world_id"].nunique()
    )
    metrics["heterogeneity_independent_worlds"] = int(
        heterogeneity_runs["world_id"].nunique()
    )
    write_json(output_dir / "key_metrics.json", metrics)
    _write_report(output_dir / "REPORT.md", metrics, config)
    manifest_path = write_level_manifest(
        output_dir=output_dir,
        level="N1",
        description=(
            "Confirmatory homogeneous Hungarian campaign: spatial quality, "
            "controlled scaling, static post-failure re-allocation and an "
            "out-of-domain heterogeneous-capacity audit."
        ),
        sources=(
            config_path,
            Path(__file__).resolve(),
            REPOSITORY_ROOT / "scripts" / "sp1_levels_common.py",
            Path(homogeneous.__file__).resolve(),
            Path(heterogeneous.__file__).resolve(),
            *raw_paths.values(),
        ),
        row_counts={
            "quality_runs": len(quality_runs),
            "scaling_runs": len(scaling_runs),
            "failure_runs": len(failure_runs),
            "heterogeneity_runs": len(heterogeneity_runs),
            "quality_summary": len(quality_summary),
            "quality_cell_diagnostic": len(quality_diagnostic),
            "scaling_summary": len(scaling_summary),
            "failure_summary": len(failure_summary),
            "heterogeneity_summary": len(heterogeneity_summary),
            "heterogeneity_contrasts": len(heterogeneity_contrasts),
        },
        claims=(
            "Hungarian is exact for the homogeneous robot-slot reduction.",
            "Its practical saving against sequential greedy is scenario dependent.",
            "The measured runtime slope is descriptive and strictly positive in the tested interval.",
            "Heterogeneous capacities create false-feasible slot assignments and motivate N2.",
        ),
        limitations=tuple(config["limitations"]),
    )
    return {
        "manifest": manifest_path,
        "figures": figure_paths,
        "metrics": metrics,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run and package the SP1.N1 confirmatory campaign."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run a small deterministic campaign for integration testing.",
    )
    parser.add_argument(
        "--reuse-raw",
        action="store_true",
        help="Rebuild summaries and figures without rerunning worlds.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    package = build_level(
        config_path=args.config.resolve(),
        output_dir=args.output_dir.resolve(),
        smoke=bool(args.smoke),
        reuse_raw=bool(args.reuse_raw),
    )
    print(f"N1 package: {package['manifest'].resolve()}")


if __name__ == "__main__":
    main()

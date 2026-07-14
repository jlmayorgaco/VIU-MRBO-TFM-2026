"""Benchmark SP0 dispatch policies on the CoppeliaSim scene layout.

This is a lightweight, deterministic dispatcher benchmark. It mirrors the
scene-level task logic used by ``build_sp0_corners_scene.py`` without requiring
CoppeliaSim to run, which makes policy comparisons reproducible and fast.
"""

from __future__ import annotations

import argparse
import copy
import csv
import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scripts.coppelia.build_sp0_corners_scene import build_scene_dict

plt.rcParams.update(
    {
        "figure.dpi": 160,
        "savefig.dpi": 300,
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.linewidth": 0.8,
        "grid.linewidth": 0.55,
        "lines.linewidth": 1.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)

BASELINE_POLICY = "fifo_nearest_baseline"
POLICIES = (BASELINE_POLICY, "hungarian_centralized", "distributed_greedy", "replicator_distributed")
CONTROLLER_POLICIES = ("hungarian_centralized", "distributed_greedy", "replicator_distributed")
DEFAULT_CASES = ("balanced", "battery_stress", "target_skew", "scarce_robots")
MISSED_ASSIGNMENT_PENALTY = 1000.0
FIG_DPI = 300


@dataclass
class RobotState:
    name: str
    base: str
    pos: list[float]
    battery: float
    release_delay: float
    state: str = "idle"
    assigned_box: str | None = None
    carrying: bool = False
    wait_until: float = 0.0
    distance_m: float = 0.0
    energy_used_pct: float = 0.0
    charge_cycles: int = 0


@dataclass
class BoxState:
    name: str
    drop: str
    target: str
    target_index: int
    slot_offset: tuple[float, float]
    state: str = "waiting"
    assigned_robot: str | None = None
    carrier: str | None = None
    wait_since: float = 0.0
    wait_until: float = 0.0
    respawn_at: float = 0.0


@dataclass
class RunMetrics:
    case: str
    policy: str
    seed: int
    delivered: int = 0
    total_distance_m: float = 0.0
    energy_used_pct: float = 0.0
    charge_cycles: int = 0
    assignments: int = 0
    assignment_cost: float = 0.0
    wait_samples: list[float] = field(default_factory=list)
    min_distance_m: float = 99.0
    collision_warnings: int = 0
    robot_trace: list[dict[str, Any]] = field(default_factory=list)
    objective_trace: list[dict[str, Any]] = field(default_factory=list)
    assignment_trace: list[dict[str, Any]] = field(default_factory=list)

    @property
    def avg_wait_s(self) -> float:
        return sum(self.wait_samples) / len(self.wait_samples) if self.wait_samples else 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "results/coppeliasim_validation/sp0_corners/dispatch_benchmark")
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--cases", default=",".join(DEFAULT_CASES), help="Comma-separated cases: balanced,battery_stress,target_skew,scarce_robots.")
    parser.add_argument("--horizon-s", type=float, default=180.0)
    parser.add_argument("--dt-s", type=float, default=0.10)
    parser.add_argument("--trace-interval-s", type=float, default=1.0, help="Sampling period for robot x/y/battery traces.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    base_scene = build_scene_dict(Path(r"C:\Program Files\CoppeliaRobotics\CoppeliaSimEdu"))
    cases = tuple(case.strip() for case in str(args.cases).split(",") if case.strip())
    rows: list[dict[str, Any]] = []
    robot_trace_rows: list[dict[str, Any]] = []
    objective_trace_rows: list[dict[str, Any]] = []
    assignment_trace_rows: list[dict[str, Any]] = []
    for case in cases:
        scene = build_case_scene(base_scene, case)
        for policy in POLICIES:
            for seed in range(args.seeds):
                metrics = run_policy(
                    scene,
                    case,
                    policy,
                    seed,
                    args.horizon_s,
                    args.dt_s,
                    trace_interval_s=args.trace_interval_s,
                    collect_trace=policy in CONTROLLER_POLICIES,
                )
                rows.append(
                    {
                        "case": metrics.case,
                        "policy": metrics.policy,
                        "seed": metrics.seed,
                        "delivered": metrics.delivered,
                        "total_distance_m": round(metrics.total_distance_m, 4),
                        "energy_used_pct": round(metrics.energy_used_pct, 4),
                        "charge_cycles": metrics.charge_cycles,
                        "assignments": metrics.assignments,
                        "assignment_cost": round(metrics.assignment_cost, 4),
                        "avg_wait_s": round(metrics.avg_wait_s, 4),
                        "min_distance_m": round(metrics.min_distance_m, 4),
                        "collision_warnings": metrics.collision_warnings,
                    }
                )
                robot_trace_rows.extend(metrics.robot_trace)
                objective_trace_rows.extend(metrics.objective_trace)
                assignment_trace_rows.extend(metrics.assignment_trace)
    write_csv(args.out / "dispatch_policy_runs.csv", rows)
    write_csv(args.out / "dispatch_robot_trace.csv", robot_trace_rows)
    write_csv(args.out / "dispatch_objective_trace.csv", objective_trace_rows)
    write_csv(args.out / "dispatch_assignment_trace.csv", assignment_trace_rows)
    summary = summarize(rows)
    write_csv(args.out / "dispatch_policy_summary.csv", summary)
    deltas = baseline_deltas(summary)
    write_csv(args.out / "dispatch_policy_baseline_delta.csv", deltas)
    gap_summary = objective_gap_summary(objective_trace_rows)
    write_csv(args.out / "dispatch_hungarian_gap_summary.csv", gap_summary)
    ci_rows = policy_confidence_intervals(rows)
    write_csv(args.out / "dispatch_policy_ci.csv", ci_rows)
    seed_gap_summary = seed_objective_gap_summary(objective_trace_rows)
    write_csv(args.out / "dispatch_seed_hungarian_gap.csv", seed_gap_summary)
    statistical_tests = paired_statistical_tests(rows, seed_gap_summary)
    write_csv(args.out / "dispatch_statistical_tests.csv", statistical_tests)
    time_integrals = temporal_integrals(robot_trace_rows, objective_trace_rows)
    write_csv(args.out / "dispatch_time_integrals.csv", time_integrals)
    plot_summary(summary, args.out / "dispatch_policy_comparison.png")
    plot_baseline_deltas(deltas, args.out / "dispatch_policy_baseline_delta.png")
    plot_runs(rows, args.out / "dispatch_policy_scatter.png")
    plot_objective_traces(objective_trace_rows, args.out / "dispatch_objective_j_vs_t.png")
    plot_regret_traces(objective_trace_rows, args.out / "dispatch_hungarian_regret_vs_t.png")
    plot_battery_traces(robot_trace_rows, args.out / "dispatch_battery_life_vs_t.png")
    plot_trajectory_sample(robot_trace_rows, args.out / "dispatch_xy_trajectories_seed0_balanced.png")
    plot_ieee_metric_ci(summary, args.out / "dispatch_ieee_metric_ci.png")
    plot_pareto_energy_wait(summary, args.out / "dispatch_pareto_energy_wait.png")
    plot_optimality_heatmap(gap_summary, args.out / "dispatch_optimality_heatmap.png")
    plot_regret_boxplot(seed_gap_summary, args.out / "dispatch_regret_boxplot.png")
    plot_battery_quantile_bands(robot_trace_rows, args.out / "dispatch_battery_quantile_bands.png")
    plot_regret_ecdf(objective_trace_rows, args.out / "dispatch_regret_ecdf.png")
    plot_robot_state_timeline(robot_trace_rows, args.out / "dispatch_robot_state_timeline_seed0_target_skew.png")
    write_markdown_report(summary, deltas, gap_summary, args.out / "README.md")
    print(f"wrote {args.out}")
    return 0


def build_case_scene(base_scene: dict[str, Any], case: str) -> dict[str, Any]:
    scene = copy.deepcopy(base_scene)
    if case == "balanced":
        return scene
    if case == "battery_stress":
        batteries = (74.0, 68.0, 62.0, 56.0, 72.0, 66.0, 60.0, 54.0)
        for robot, battery in zip(scene["robots"], batteries, strict=True):
            robot["battery_initial_pct"] = battery
        scene["amr"]["battery_low_pct"] = 24.0
        scene["amr"]["battery_resume_pct"] = 82.0
        scene["amr"]["battery_move_drain_pct_per_m"] = 2.45
        scene["amr"]["battery_load_extra_pct_per_m"] = 1.10
        scene["amr"]["box_respawn_s"] = 1.2
        return scene
    if case == "target_skew":
        for box in scene["boxes"]:
            box["target"] = "target_descarga_este" if box["drop"] == "caida_cajas_nw" else "target_descarga_oeste"
        scene["amr"]["box_respawn_s"] = 1.0
        scene["amr"]["battery_move_drain_pct_per_m"] = 2.55
        scene["amr"]["battery_load_extra_pct_per_m"] = 1.15
        return scene
    if case == "scarce_robots":
        for idx, robot in enumerate(scene["robots"]):
            robot["release_delay_s"] = 0.0 if idx < 4 else 45.0
            robot["battery_initial_pct"] = [96.0, 86.0, 76.0, 66.0, 92.0, 82.0, 72.0, 62.0][idx]
        scene["amr"]["box_respawn_s"] = 0.85
        scene["amr"]["battery_move_drain_pct_per_m"] = 2.35
        scene["amr"]["battery_load_extra_pct_per_m"] = 1.05
        return scene
    raise SystemExit(f"Unknown case {case!r}. Known: {', '.join(DEFAULT_CASES)}")


def run_policy(
    scene: dict[str, Any],
    case: str,
    policy: str,
    seed: int,
    horizon_s: float,
    dt_s: float,
    trace_interval_s: float,
    collect_trace: bool,
) -> RunMetrics:
    rng = random.Random(seed)
    zones = {z["name"]: z for z in scene["zones"]}
    targets = list(scene["targets"])
    target_lookup = {name: idx for idx, name in enumerate(targets)}
    amr = scene["amr"]
    scale = float(amr.get("sim_speed_multiplier", 1.0))
    max_speed = float(amr["max_speed_mps"]) * scale
    arrival = float(amr["arrival_radius_m"])
    drop_arrival = float(amr["drop_alignment_radius_m"])
    low = float(amr["battery_low_pct"])
    resume = float(amr["battery_resume_pct"])
    move_drain = float(amr["battery_move_drain_pct_per_m"])
    load_extra = float(amr["battery_load_extra_pct_per_m"])
    idle_drain = float(amr["battery_idle_drain_pct_per_s"])
    charge_rate = float(amr["battery_charge_pct_per_s"])
    pickup_wait = 1.20 / scale
    unload_wait = 1.25 / scale
    respawn_wait = float(amr["box_respawn_s"]) / scale
    hard_clearance = float(amr["hard_clearance_m"])

    robots = {
        r["name"]: RobotState(
            name=r["name"],
            base=r["base"],
            pos=[float(r["position"][0]), float(r["position"][1])],
            battery=float(r.get("battery_initial_pct", 100.0)),
            release_delay=float(r.get("release_delay_s", 0.0)),
        )
        for r in scene["robots"]
    }
    boxes = {}
    for b in scene["boxes"]:
        target = str(b["target"])
        boxes[b["name"]] = BoxState(
            name=b["name"],
            drop=b["drop"],
            target=target,
            target_index=target_lookup.get(target, 0),
            slot_offset=(float(b.get("slot_offset", [0.0, 0.0])[0]), float(b.get("slot_offset", [0.0, 0.0])[1])),
        )
    metrics = RunMetrics(case=case, policy=policy, seed=seed)
    last_assignment = -99.0
    next_trace = 0.0
    t = 0.0
    while t <= horizon_s:
        for box in boxes.values():
            if box.state == "cooldown" and t >= box.respawn_at:
                box.state = "waiting"
                box.assigned_robot = None
                box.carrier = None
                box.wait_since = t
                box.target_index = (box.target_index + 1 + (1 if rng.random() < 0.18 else 0)) % len(targets)
                box.target = targets[box.target_index]

        for robot in robots.values():
            update_mission(robot, boxes, zones, targets, t, arrival, drop_arrival, pickup_wait, unload_wait, respawn_wait, low, resume, metrics)

        if t - last_assignment >= 0.75 / scale:
            last_assignment = t
            jobs = [b.name for b in boxes.values() if b.state == "waiting" and b.assigned_robot is None and t >= b.respawn_at]
            candidates = [r.name for r in robots.values() if r.state == "idle" and t >= r.release_delay and r.battery > low]
            assignments = assign(policy, candidates, jobs, robots, boxes, zones, low, move_drain, load_extra)
            if collect_trace:
                log_objective_event(
                    metrics,
                    t,
                    candidates,
                    jobs,
                    assignments,
                    robots,
                    boxes,
                    zones,
                    low,
                    move_drain,
                    load_extra,
                )
            for robot_name, box_name in assignments:
                robot = robots[robot_name]
                box = boxes[box_name]
                if robot.state == "idle" and box.state == "waiting":
                    robot.assigned_box = box_name
                    robot.state = "to_box"
                    box.state = "assigned"
                    box.assigned_robot = robot_name
                    metrics.assignments += 1
                    metrics.assignment_cost += assignment_cost(robot, box, zones, low, move_drain, load_extra)

        positions = [r.pos for r in robots.values()]
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                d = distance(positions[i], positions[j])
                metrics.min_distance_m = min(metrics.min_distance_m, d)
                if d < hard_clearance:
                    metrics.collision_warnings += 1

        for robot in robots.values():
            target = robot_target(robot, boxes, zones, targets)
            moved = move_robot(robot, target, max_speed, dt_s, scene)
            drain = idle_drain * dt_s
            if robot.state == "charging":
                robot.battery = min(100.0, robot.battery + charge_rate * dt_s)
                drain = 0.0
            else:
                drain += moved * move_drain
                if robot.carrying:
                    drain += moved * load_extra
                robot.battery = max(0.0, robot.battery - drain)
                robot.energy_used_pct += drain
                metrics.energy_used_pct += drain
            robot.distance_m += moved
            metrics.total_distance_m += moved
        if collect_trace and t + 1.0e-9 >= next_trace:
            log_robot_trace(metrics, t, robots)
            next_trace += max(trace_interval_s, dt_s)
        t += dt_s
    metrics.charge_cycles = sum(r.charge_cycles for r in robots.values())
    return metrics


def log_robot_trace(metrics: RunMetrics, t: float, robots: dict[str, RobotState]) -> None:
    for robot in robots.values():
        metrics.robot_trace.append(
            {
                "case": metrics.case,
                "policy": metrics.policy,
                "seed": metrics.seed,
                "t_s": round(t, 4),
                "robot": robot.name,
                "x_m": round(robot.pos[0], 5),
                "y_m": round(robot.pos[1], 5),
                "battery_pct": round(robot.battery, 5),
                "battery_life_pct": round(robot.battery, 5),
                "state": robot.state,
                "assigned_box": robot.assigned_box or "",
                "carrying": int(robot.carrying),
                "distance_m": round(robot.distance_m, 5),
                "energy_used_pct": round(robot.energy_used_pct, 5),
                "charge_cycles": robot.charge_cycles,
            }
        )


def log_objective_event(
    metrics: RunMetrics,
    t: float,
    candidates: list[str],
    jobs: list[str],
    assignments: list[tuple[str, str]],
    robots: dict[str, RobotState],
    boxes: dict[str, BoxState],
    zones: dict[str, dict[str, Any]],
    low: float,
    move_drain: float,
    load_extra: float,
) -> None:
    optimal = hungarian_assign(candidates, jobs, robots, boxes, zones, low, move_drain, load_extra)
    optimal_set = set(optimal)
    policy_cost = assignment_set_cost(assignments, robots, boxes, zones, low, move_drain, load_extra)
    optimal_cost = assignment_set_cost(optimal, robots, boxes, zones, low, move_drain, load_extra)
    selected_count = len(assignments)
    optimal_count = len(optimal)
    count_gap = optimal_count - selected_count
    raw_delta = policy_cost - optimal_cost
    cost_gap = max(0.0, raw_delta)
    regret = max(0, count_gap) * MISSED_ASSIGNMENT_PENALTY + cost_gap
    gap_pct = cost_gap / optimal_cost * 100.0 if optimal_cost > 1.0e-9 and selected_count == optimal_count else 0.0
    stats = pairwise_fitness_stats(candidates, jobs, robots, boxes, zones, low, move_drain, load_extra)
    matching_pairs = sum(1 for item in assignments if item in optimal_set)
    metrics.objective_trace.append(
        {
            "case": metrics.case,
            "policy": metrics.policy,
            "seed": metrics.seed,
            "t_s": round(t, 4),
            "candidate_count": len(candidates),
            "job_count": len(jobs),
            "assignment_count": selected_count,
            "hungarian_assignment_count": optimal_count,
            "assignment_count_gap": count_gap,
            "matching_hungarian_pairs": matching_pairs,
            "j_policy": round(policy_cost, 6),
            "j_hungarian_opt": round(optimal_cost, 6),
            "j_raw_delta": round(raw_delta, 6),
            "j_gap_abs": round(cost_gap, 6),
            "j_gap_pct": round(gap_pct, 6),
            "j_regret": round(regret, 6),
            "fitness_mean": round(stats["fitness_mean"], 8),
            "fitness_min": round(stats["fitness_min"], 8),
            "fitness_max": round(stats["fitness_max"], 8),
            "cost_mean": round(stats["cost_mean"], 6),
            "energy_mean": round(stats["energy_mean"], 6),
        }
    )
    for robot_name, box_name in assignments:
        robot = robots[robot_name]
        box = boxes[box_name]
        cost = assignment_cost(robot, box, zones, low, move_drain, load_extra)
        energy = assignment_energy(robot, box, zones, move_drain, load_extra)
        pickup = pickup_xy(box, zones)
        target = zone_xy(zones[box.target])
        metrics.assignment_trace.append(
            {
                "case": metrics.case,
                "policy": metrics.policy,
                "seed": metrics.seed,
                "t_s": round(t, 4),
                "robot": robot_name,
                "box": box_name,
                "target": box.target,
                "robot_x_m": round(robot.pos[0], 5),
                "robot_y_m": round(robot.pos[1], 5),
                "pickup_x_m": round(pickup[0], 5),
                "pickup_y_m": round(pickup[1], 5),
                "target_x_m": round(target[0], 5),
                "target_y_m": round(target[1], 5),
                "battery_pct": round(robot.battery, 5),
                "fitness": round(fitness_from_cost(cost), 8),
                "cost_cij": round(cost, 6),
                "energy_required_pct": round(energy, 6),
                "is_hungarian_optimal_pair": int((robot_name, box_name) in optimal_set),
            }
        )


def assignment_set_cost(
    assignments: list[tuple[str, str]],
    robots: dict[str, RobotState],
    boxes: dict[str, BoxState],
    zones: dict[str, dict[str, Any]],
    low: float,
    move_drain: float,
    load_extra: float,
) -> float:
    total = 0.0
    for robot_name, box_name in assignments:
        if robot_name not in robots or box_name not in boxes:
            continue
        cost = assignment_cost(robots[robot_name], boxes[box_name], zones, low, move_drain, load_extra)
        if cost >= 1.0e8:
            total += MISSED_ASSIGNMENT_PENALTY
        else:
            total += cost
    return total


def pairwise_fitness_stats(
    candidates: list[str],
    jobs: list[str],
    robots: dict[str, RobotState],
    boxes: dict[str, BoxState],
    zones: dict[str, dict[str, Any]],
    low: float,
    move_drain: float,
    load_extra: float,
) -> dict[str, float]:
    costs: list[float] = []
    fitness: list[float] = []
    energies: list[float] = []
    for robot_name in candidates:
        for box_name in jobs:
            robot = robots[robot_name]
            box = boxes[box_name]
            cost = assignment_cost(robot, box, zones, low, move_drain, load_extra)
            if cost >= 1.0e8:
                continue
            energy = assignment_energy(robot, box, zones, move_drain, load_extra)
            costs.append(cost)
            fitness.append(fitness_from_cost(cost))
            energies.append(energy)
    if not costs:
        return {"cost_mean": 0.0, "fitness_mean": 0.0, "fitness_min": 0.0, "fitness_max": 0.0, "energy_mean": 0.0}
    return {
        "cost_mean": sum(costs) / len(costs),
        "fitness_mean": sum(fitness) / len(fitness),
        "fitness_min": min(fitness),
        "fitness_max": max(fitness),
        "energy_mean": sum(energies) / len(energies),
    }


def fitness_from_cost(cost: float) -> float:
    return 0.0 if cost >= 1.0e8 else 1.0 / (1.0 + cost)


def update_mission(
    robot: RobotState,
    boxes: dict[str, BoxState],
    zones: dict[str, dict[str, Any]],
    targets: list[str],
    t: float,
    arrival: float,
    drop_arrival: float,
    pickup_wait: float,
    unload_wait: float,
    respawn_wait: float,
    low: float,
    resume: float,
    metrics: RunMetrics,
) -> None:
    if robot.state == "charging":
        if robot.battery >= resume:
            robot.state = "idle"
        return
    if robot.state == "to_charge":
        if distance(robot.pos, zone_xy(zones[robot.base])) <= arrival:
            robot.state = "charging"
            robot.charge_cycles += 1
        return
    if robot.battery <= low and not robot.carrying:
        release_box(robot, boxes)
        robot.state = "to_charge"
        return
    if robot.state == "idle" or t < robot.release_delay:
        return
    box = boxes.get(robot.assigned_box or "")
    if not box:
        robot.assigned_box = None
        robot.state = "idle"
        return
    if robot.state == "to_box" and distance(robot.pos, pickup_xy(box, zones)) <= drop_arrival:
        robot.pos = list(pickup_xy(box, zones))
        robot.state = "pickup_wait"
        robot.wait_until = t + pickup_wait
        box.state = "pickup_wait"
        box.carrier = robot.name
        box.wait_until = robot.wait_until
        metrics.wait_samples.append(max(0.0, t - box.wait_since))
    elif robot.state == "pickup_wait" and t >= robot.wait_until:
        robot.state = "to_unload"
        robot.carrying = True
        box.state = "carrying"
    elif robot.state == "to_unload" and distance(robot.pos, zone_xy(zones[box.target])) <= arrival:
        robot.state = "unload_wait"
        robot.wait_until = t + unload_wait
        box.state = "unload_wait"
        box.wait_until = robot.wait_until
    elif robot.state == "unload_wait" and t >= robot.wait_until:
        metrics.delivered += 1
        robot.carrying = False
        robot.assigned_box = None
        box.state = "cooldown"
        box.assigned_robot = None
        box.carrier = None
        box.respawn_at = t + respawn_wait
        robot.state = "to_charge" if robot.battery <= resume else "idle"


def release_box(robot: RobotState, boxes: dict[str, BoxState]) -> None:
    if robot.assigned_box and robot.assigned_box in boxes:
        box = boxes[robot.assigned_box]
        if box.state == "assigned":
            box.state = "waiting"
            box.assigned_robot = None
    robot.assigned_box = None


def robot_target(robot: RobotState, boxes: dict[str, BoxState], zones: dict[str, dict[str, Any]], targets: list[str]) -> tuple[float, float]:
    box = boxes.get(robot.assigned_box or "")
    if robot.state in {"to_box", "pickup_wait"} and box:
        return pickup_xy(box, zones)
    if robot.state in {"to_unload", "unload_wait"} and box:
        return zone_xy(zones[box.target])
    if robot.state in {"to_charge", "charging"}:
        return zone_xy(zones[robot.base])
    return tuple(robot.pos)


def move_robot(robot: RobotState, target: tuple[float, float], max_speed: float, dt_s: float, scene: dict[str, Any]) -> float:
    if robot.state in {"idle", "pickup_wait", "unload_wait", "charging"}:
        return 0.0
    dx = target[0] - robot.pos[0]
    dy = target[1] - robot.pos[1]
    d = math.hypot(dx, dy)
    if d <= 1.0e-9:
        return 0.0
    step = min(d, max_speed * max(0.20, min(1.0, d / 0.90)) * dt_s)
    robot.pos[0] += dx / d * step
    robot.pos[1] += dy / d * step
    hx = float(scene["dimensions_m"]["width"]) / 2.0 - 0.55
    hy = float(scene["dimensions_m"]["depth"]) / 2.0 - 0.55
    robot.pos[0] = max(-hx, min(hx, robot.pos[0]))
    robot.pos[1] = max(-hy, min(hy, robot.pos[1]))
    return step


def assign(
    policy: str,
    candidates: list[str],
    jobs: list[str],
    robots: dict[str, RobotState],
    boxes: dict[str, BoxState],
    zones: dict[str, dict[str, Any]],
    low: float,
    move_drain: float,
    load_extra: float,
) -> list[tuple[str, str]]:
    if policy == BASELINE_POLICY:
        return fifo_nearest_assign(candidates, jobs, robots, boxes, zones, low, move_drain, load_extra)
    if policy == "distributed_greedy":
        return greedy_assign(candidates, jobs, robots, boxes, zones, low, move_drain, load_extra)
    if policy == "replicator_distributed":
        return replicator_assign(candidates, jobs, robots, boxes, zones, low, move_drain, load_extra)
    return hungarian_assign(candidates, jobs, robots, boxes, zones, low, move_drain, load_extra)


def fifo_nearest_assign(
    candidates: list[str],
    jobs: list[str],
    robots: dict[str, RobotState],
    boxes: dict[str, BoxState],
    zones: dict[str, dict[str, Any]],
    low: float,
    move_drain: float,
    load_extra: float,
) -> list[tuple[str, str]]:
    """Naive baseline: FIFO jobs, nearest feasible robot to pickup.

    It respects battery feasibility so comparisons stay physically meaningful,
    but it ignores the target/return cost when ranking alternatives.
    """
    used: set[str] = set()
    out: list[tuple[str, str]] = []
    for job in jobs:
        pickup = pickup_xy(boxes[job], zones)
        available = [
            r
            for r in candidates
            if r not in used and robots[r].battery - assignment_energy(robots[r], boxes[job], zones, move_drain, load_extra) >= low
        ]
        if not available:
            continue
        robot_name = min(available, key=lambda r: distance(robots[r].pos, pickup))
        used.add(robot_name)
        out.append((robot_name, job))
    return out


def hungarian_assign(
    candidates: list[str],
    jobs: list[str],
    robots: dict[str, RobotState],
    boxes: dict[str, BoxState],
    zones: dict[str, dict[str, Any]],
    low: float,
    move_drain: float,
    load_extra: float,
) -> list[tuple[str, str]]:
    best: list[tuple[str, str]] = []
    best_count = -1
    best_cost = float("inf")
    used: set[str] = set()
    cur: list[tuple[str, str]] = []

    def rec(job_index: int, cost: float) -> None:
        nonlocal best, best_count, best_cost
        if job_index >= len(jobs) or len(cur) == len(candidates):
            if len(cur) > best_count or (len(cur) == best_count and cost < best_cost):
                best_count = len(cur)
                best_cost = cost
                best = list(cur)
            return
        rec(job_index + 1, cost)
        job = jobs[job_index]
        for robot_name in candidates:
            if robot_name in used:
                continue
            c = assignment_cost(robots[robot_name], boxes[job], zones, low, move_drain, load_extra)
            if c >= 1.0e8:
                continue
            used.add(robot_name)
            cur.append((robot_name, job))
            rec(job_index + 1, cost + c)
            cur.pop()
            used.remove(robot_name)

    rec(0, 0.0)
    return best


def greedy_assign(
    candidates: list[str],
    jobs: list[str],
    robots: dict[str, RobotState],
    boxes: dict[str, BoxState],
    zones: dict[str, dict[str, Any]],
    low: float,
    move_drain: float,
    load_extra: float,
) -> list[tuple[str, str]]:
    pairs = [
        (assignment_cost(robots[r], boxes[j], zones, low, move_drain, load_extra), r, j)
        for r in candidates
        for j in jobs
    ]
    pairs = [(c, r, j) for c, r, j in pairs if c < 1.0e8]
    pairs.sort()
    used_r: set[str] = set()
    used_j: set[str] = set()
    out: list[tuple[str, str]] = []
    for _, r, j in pairs:
        if r not in used_r and j not in used_j:
            used_r.add(r)
            used_j.add(j)
            out.append((r, j))
    return out


def replicator_assign(
    candidates: list[str],
    jobs: list[str],
    robots: dict[str, RobotState],
    boxes: dict[str, BoxState],
    zones: dict[str, dict[str, Any]],
    low: float,
    move_drain: float,
    load_extra: float,
) -> list[tuple[str, str]]:
    utilities: dict[tuple[str, str], float] = {}
    weights: dict[tuple[str, str], float] = {}
    for r in candidates:
        feasible = []
        for j in jobs:
            c = assignment_cost(robots[r], boxes[j], zones, low, move_drain, load_extra)
            u = 1.0 / (1.0 + c) if c < 1.0e8 else 0.0
            utilities[(r, j)] = u
            if u > 0.0:
                feasible.append(j)
        for j in jobs:
            weights[(r, j)] = 1.0 / len(feasible) if j in feasible else 0.0
    for _ in range(18):
        demand = {j: sum(weights[(r, j)] for r in candidates) for j in jobs}
        for r in candidates:
            avg = sum(weights[(r, j)] * utilities[(r, j)] / (1.0 + max(0.0, demand[j] - 1.0)) for j in jobs)
            next_w = {}
            denom = 0.0
            for j in jobs:
                fitness = utilities[(r, j)] / (1.0 + max(0.0, demand[j] - 1.0))
                w = max(0.0, weights[(r, j)] * (1.0 + 1.15 * (fitness - avg)))
                next_w[j] = w
                denom += w
            if denom > 0.0:
                for j in jobs:
                    weights[(r, j)] = next_w[j] / denom
    pairs = sorted(
        ((weights[(r, j)] * utilities[(r, j)], r, j) for r in candidates for j in jobs),
        reverse=True,
    )
    used_r: set[str] = set()
    used_j: set[str] = set()
    out: list[tuple[str, str]] = []
    for score, r, j in pairs:
        if score <= 0.0:
            continue
        if r not in used_r and j not in used_j:
            used_r.add(r)
            used_j.add(j)
            out.append((r, j))
    return out


def assignment_cost(
    robot: RobotState,
    box: BoxState,
    zones: dict[str, dict[str, Any]],
    low: float,
    move_drain: float,
    load_extra: float,
) -> float:
    energy = assignment_energy(robot, box, zones, move_drain, load_extra)
    if robot.battery - energy < low:
        return 1.0e9
    pickup = pickup_xy(box, zones)
    unload = zone_xy(zones[box.target])
    base = zone_xy(zones[robot.base])
    empty = distance(robot.pos, pickup)
    loaded = distance(pickup, unload)
    home = distance(unload, base)
    return empty + loaded + 0.35 * home + 0.035 * (100.0 - robot.battery)


def assignment_energy(
    robot: RobotState,
    box: BoxState,
    zones: dict[str, dict[str, Any]],
    move_drain: float,
    load_extra: float,
) -> float:
    pickup = pickup_xy(box, zones)
    unload = zone_xy(zones[box.target])
    base = zone_xy(zones[robot.base])
    empty = distance(robot.pos, pickup)
    loaded = distance(pickup, unload)
    home = distance(unload, base)
    return (empty + loaded + home) * move_drain + loaded * load_extra


def pickup_xy(box: BoxState, zones: dict[str, dict[str, Any]]) -> tuple[float, float]:
    x, y = zone_xy(zones[box.drop])
    return x + box.slot_offset[0], y + box.slot_offset[1]


def zone_xy(zone: dict[str, Any]) -> tuple[float, float]:
    return float(zone["center"][0]), float(zone["center"][1])


def distance(a: tuple[float, float] | list[float], b: tuple[float, float] | list[float]) -> float:
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    cases = sorted({str(r["case"]) for r in rows})
    for case in cases:
        for policy in POLICIES:
            group = [r for r in rows if r["case"] == case and r["policy"] == policy]
            if not group:
                continue
            item: dict[str, Any] = {"case": case, "policy": policy, "n": len(group)}
            for key in (
                "delivered",
                "total_distance_m",
                "energy_used_pct",
                "charge_cycles",
                "assignments",
                "assignment_cost",
                "avg_wait_s",
                "min_distance_m",
                "collision_warnings",
            ):
                values = [float(r[key]) for r in group]
                mean = sum(values) / len(values)
                var = sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1)
                item[f"{key}_mean"] = round(mean, 4)
                item[f"{key}_std"] = round(math.sqrt(var), 4)
            out.append(item)
    return out


def baseline_deltas(summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    cases = sorted({str(r["case"]) for r in summary})
    for case in cases:
        baseline = next((r for r in summary if r["case"] == case and r["policy"] == BASELINE_POLICY), None)
        if not baseline:
            continue
        for row in summary:
            if row["case"] != case or row["policy"] == BASELINE_POLICY:
                continue
            item: dict[str, Any] = {"case": case, "baseline": BASELINE_POLICY, "policy": row["policy"]}
            for metric in ("delivered", "avg_wait_s", "energy_used_pct", "assignment_cost", "charge_cycles"):
                base_value = float(baseline[f"{metric}_mean"])
                value = float(row[f"{metric}_mean"])
                delta = value - base_value
                item[f"{metric}_delta"] = round(delta, 4)
                item[f"{metric}_delta_pct"] = round(delta / base_value * 100.0, 4) if abs(base_value) > 1.0e-9 else 0.0
            out.append(item)
    return out


def objective_gap_summary(objective_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    keys = sorted({(str(r["case"]), str(r["policy"])) for r in objective_rows})
    for case, policy in keys:
        group = [r for r in objective_rows if r["case"] == case and r["policy"] == policy]
        active = [r for r in group if int(r["hungarian_assignment_count"]) > 0]
        if not active:
            out.append(
                {
                    "case": case,
                    "policy": policy,
                    "events": len(group),
                    "active_events": 0,
                    "j_policy_mean": 0.0,
                    "j_hungarian_opt_mean": 0.0,
                    "j_gap_abs_mean": 0.0,
                    "j_gap_pct_mean": 0.0,
                    "j_regret_mean": 0.0,
                    "assignment_count_gap_mean": 0.0,
                    "hungarian_pair_match_rate": 0.0,
                }
            )
            continue
        opt_pairs = sum(int(r["hungarian_assignment_count"]) for r in active)
        match_pairs = sum(int(r["matching_hungarian_pairs"]) for r in active)
        out.append(
            {
                "case": case,
                "policy": policy,
                "events": len(group),
                "active_events": len(active),
                "j_policy_mean": round(mean(active, "j_policy"), 6),
                "j_hungarian_opt_mean": round(mean(active, "j_hungarian_opt"), 6),
                "j_gap_abs_mean": round(mean(active, "j_gap_abs"), 6),
                "j_gap_pct_mean": round(mean(active, "j_gap_pct"), 6),
                "j_regret_mean": round(mean(active, "j_regret"), 6),
                "assignment_count_gap_mean": round(mean(active, "assignment_count_gap"), 6),
                "hungarian_pair_match_rate": round(match_pairs / opt_pairs if opt_pairs else 0.0, 6),
            }
        )
    return out


def policy_confidence_intervals(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    metrics = (
        "delivered",
        "total_distance_m",
        "energy_used_pct",
        "charge_cycles",
        "assignments",
        "assignment_cost",
        "avg_wait_s",
        "min_distance_m",
        "collision_warnings",
    )
    for case in sorted({str(r["case"]) for r in rows}):
        for policy in POLICIES:
            group = [r for r in rows if str(r["case"]) == case and str(r["policy"]) == policy]
            if not group:
                continue
            for metric in metrics:
                stats = sample_stats([float(r[metric]) for r in group])
                out.append(
                    {
                        "case": case,
                        "policy": policy,
                        "metric": metric,
                        "n": stats["n"],
                        "mean": round(stats["mean"], 6),
                        "std": round(stats["std"], 6),
                        "sem": round(stats["sem"], 6),
                        "ci95_half_width": round(stats["ci95"], 6),
                        "ci95_low": round(stats["mean"] - stats["ci95"], 6),
                        "ci95_high": round(stats["mean"] + stats["ci95"], 6),
                    }
                )
    return out


def seed_objective_gap_summary(objective_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    keys = sorted({(str(r["case"]), str(r["policy"]), int(r["seed"])) for r in objective_rows})
    for case, policy, seed in keys:
        group = sorted(
            [r for r in objective_rows if str(r["case"]) == case and str(r["policy"]) == policy and int(r["seed"]) == seed],
            key=lambda r: float(r["t_s"]),
        )
        active = [r for r in group if int(r["hungarian_assignment_count"]) > 0]
        if not active:
            out.append(
                {
                    "case": case,
                    "policy": policy,
                    "seed": seed,
                    "events": len(group),
                    "active_events": 0,
                    "j_policy_mean": 0.0,
                    "j_hungarian_opt_mean": 0.0,
                    "j_gap_abs_mean": 0.0,
                    "j_gap_pct_mean": 0.0,
                    "j_regret_mean": 0.0,
                    "j_regret_max": 0.0,
                    "assignment_count_gap_mean": 0.0,
                    "hungarian_pair_match_rate": 0.0,
                    "j_regret_auc": 0.0,
                    "j_gap_auc": 0.0,
                }
            )
            continue
        opt_pairs = sum(int(r["hungarian_assignment_count"]) for r in active)
        match_pairs = sum(int(r["matching_hungarian_pairs"]) for r in active)
        out.append(
            {
                "case": case,
                "policy": policy,
                "seed": seed,
                "events": len(group),
                "active_events": len(active),
                "j_policy_mean": round(mean(active, "j_policy"), 6),
                "j_hungarian_opt_mean": round(mean(active, "j_hungarian_opt"), 6),
                "j_gap_abs_mean": round(mean(active, "j_gap_abs"), 6),
                "j_gap_pct_mean": round(mean(active, "j_gap_pct"), 6),
                "j_regret_mean": round(mean(active, "j_regret"), 6),
                "j_regret_max": round(max(float(r["j_regret"]) for r in active), 6),
                "assignment_count_gap_mean": round(mean(active, "assignment_count_gap"), 6),
                "hungarian_pair_match_rate": round(match_pairs / opt_pairs if opt_pairs else 0.0, 6),
                "j_regret_auc": round(temporal_auc(active, "j_regret"), 6),
                "j_gap_auc": round(temporal_auc(active, "j_gap_abs"), 6),
            }
        )
    return out


def paired_statistical_tests(rows: list[dict[str, Any]], seed_gap_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    out.extend(
        paired_tests_from_records(
            rows,
            metrics=(
                ("delivered", "higher"),
                ("avg_wait_s", "lower"),
                ("energy_used_pct", "lower"),
                ("assignment_cost", "lower"),
                ("charge_cycles", "lower"),
            ),
            references=(BASELINE_POLICY, "hungarian_centralized"),
        )
    )
    out.extend(
        paired_tests_from_records(
            seed_gap_rows,
            metrics=(
                ("j_regret_mean", "lower"),
                ("j_gap_pct_mean", "lower"),
                ("hungarian_pair_match_rate", "higher"),
            ),
            references=("hungarian_centralized",),
        )
    )
    return out


def paired_tests_from_records(
    records: list[dict[str, Any]],
    metrics: tuple[tuple[str, str], ...],
    references: tuple[str, ...],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    cases = sorted({str(r["case"]) for r in records})
    policies = sorted({str(r["policy"]) for r in records})
    for case in cases:
        case_rows = [r for r in records if str(r["case"]) == case]
        for reference in references:
            reference_by_seed = {int(r["seed"]): r for r in case_rows if str(r["policy"]) == reference}
            if not reference_by_seed:
                continue
            for policy in policies:
                if policy == reference:
                    continue
                policy_by_seed = {int(r["seed"]): r for r in case_rows if str(r["policy"]) == policy}
                seeds = sorted(set(reference_by_seed) & set(policy_by_seed))
                if not seeds:
                    continue
                for metric, direction in metrics:
                    deltas = [float(policy_by_seed[s][metric]) - float(reference_by_seed[s][metric]) for s in seeds]
                    stats = sample_stats(deltas)
                    if direction == "higher":
                        better = sum(1 for delta in deltas if delta > 0.0)
                    else:
                        better = sum(1 for delta in deltas if delta < 0.0)
                    cohen_dz = stats["mean"] / stats["std"] if stats["std"] > 1.0e-12 else 0.0
                    out.append(
                        {
                            "case": case,
                            "reference_policy": reference,
                            "policy": policy,
                            "metric": metric,
                            "preferred_direction": direction,
                            "n_pairs": len(seeds),
                            "mean_delta": round(stats["mean"], 6),
                            "std_delta": round(stats["std"], 6),
                            "ci95_low_delta": round(stats["mean"] - stats["ci95"], 6),
                            "ci95_high_delta": round(stats["mean"] + stats["ci95"], 6),
                            "cohen_dz": round(cohen_dz, 6),
                            "better_rate_vs_reference": round(better / len(seeds), 6),
                        }
                    )
    return out


def temporal_integrals(robot_rows: list[dict[str, Any]], objective_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: dict[tuple[str, str, int], dict[str, Any]] = {}
    for case, policy, seed in sorted({(str(r["case"]), str(r["policy"]), int(r["seed"])) for r in robot_rows}):
        group = [r for r in robot_rows if str(r["case"]) == case and str(r["policy"]) == policy and int(r["seed"]) == seed]
        by_t: dict[float, list[dict[str, Any]]] = {}
        for row in group:
            by_t.setdefault(float(row["t_s"]), []).append(row)
        avg_rows = []
        min_rows = []
        for t, rows_at_t in sorted(by_t.items()):
            batteries = [float(r["battery_pct"]) for r in rows_at_t]
            avg_rows.append({"t_s": t, "value": sum(batteries) / len(batteries)})
            min_rows.append({"t_s": t, "value": min(batteries)})
        low_samples = sum(1 for r in group if float(r["battery_pct"]) < 25.0)
        charging_samples = sum(1 for r in group if str(r["state"]) == "charging")
        key = (case, policy, seed)
        out[key] = {
            "case": case,
            "policy": policy,
            "seed": seed,
            "avg_battery_time_mean_pct": round(time_weighted_mean(avg_rows, "value"), 6),
            "min_battery_time_mean_pct": round(time_weighted_mean(min_rows, "value"), 6),
            "low_battery_sample_rate": round(low_samples / len(group) if group else 0.0, 6),
            "charging_sample_rate": round(charging_samples / len(group) if group else 0.0, 6),
        }
    for case, policy, seed in sorted({(str(r["case"]), str(r["policy"]), int(r["seed"])) for r in objective_rows}):
        group = sorted(
            [r for r in objective_rows if str(r["case"]) == case and str(r["policy"]) == policy and int(r["seed"]) == seed],
            key=lambda r: float(r["t_s"]),
        )
        active = [r for r in group if int(r["hungarian_assignment_count"]) > 0]
        key = (case, policy, seed)
        out.setdefault(key, {"case": case, "policy": policy, "seed": seed})
        out[key].update(
            {
                "decision_events": len(group),
                "active_decision_events": len(active),
                "j_policy_time_mean": round(time_weighted_mean(active, "j_policy"), 6),
                "j_hungarian_time_mean": round(time_weighted_mean(active, "j_hungarian_opt"), 6),
                "j_gap_time_mean": round(time_weighted_mean(active, "j_gap_abs"), 6),
                "j_regret_time_mean": round(time_weighted_mean(active, "j_regret"), 6),
            }
        )
    return list(out.values())


def mean(rows: list[dict[str, Any]], key: str) -> float:
    return sum(float(r[key]) for r in rows) / len(rows) if rows else 0.0


def sample_stats(values: list[float]) -> dict[str, float]:
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": 0.0, "std": 0.0, "sem": 0.0, "ci95": 0.0}
    avg = sum(values) / n
    var = sum((value - avg) ** 2 for value in values) / max(1, n - 1)
    std = math.sqrt(var)
    sem = std / math.sqrt(n) if n > 0 else 0.0
    return {"n": n, "mean": avg, "std": std, "sem": sem, "ci95": 1.96 * sem if n > 1 else 0.0}


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[int(pos)]
    weight = pos - lo
    return ordered[lo] * (1.0 - weight) + ordered[hi] * weight


def temporal_auc(rows: list[dict[str, Any]], value_key: str) -> float:
    if len(rows) < 2:
        return 0.0
    ordered = sorted(rows, key=lambda r: float(r["t_s"]))
    total = 0.0
    for prev, cur in zip(ordered, ordered[1:], strict=False):
        dt = max(0.0, float(cur["t_s"]) - float(prev["t_s"]))
        total += (float(prev[value_key]) + float(cur[value_key])) * 0.5 * dt
    return total


def time_weighted_mean(rows: list[dict[str, Any]], value_key: str) -> float:
    if not rows:
        return 0.0
    ordered = sorted(rows, key=lambda r: float(r["t_s"]))
    duration = max(0.0, float(ordered[-1]["t_s"]) - float(ordered[0]["t_s"]))
    if duration <= 1.0e-12:
        return sum(float(r[value_key]) for r in ordered) / len(ordered)
    return temporal_auc(ordered, value_key) / duration


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_figure(fig: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=FIG_DPI, bbox_inches="tight")
    if path.suffix.lower() != ".pdf":
        fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")


def plot_summary(summary: list[dict[str, Any]], path: Path) -> None:
    cases = sorted({str(r["case"]) for r in summary})
    labels = [case_label(case) for case in cases]
    fig, axes = plt.subplots(2, 2, figsize=(12.2, 7.4), dpi=150)
    specs = [
        ("delivered_mean", "delivered_std", "Entregas"),
        ("avg_wait_s_mean", "avg_wait_s_std", "Espera media (s)"),
        ("energy_used_pct_mean", "energy_used_pct_std", "Energia usada (% bateria)"),
        ("charge_cycles_mean", "charge_cycles_std", "Ciclos de carga"),
    ]
    colors = policy_colors()
    width = 0.19
    x = list(range(len(cases)))
    offsets = {policy: (idx - (len(POLICIES) - 1) / 2.0) * width for idx, policy in enumerate(POLICIES)}
    for ax, (mean_key, std_key, title) in zip(axes.ravel(), specs, strict=True):
        for policy in POLICIES:
            means = []
            stds = []
            for case in cases:
                row = next(r for r in summary if r["case"] == case and r["policy"] == policy)
                means.append(float(row[mean_key]))
                stds.append(float(row[std_key]))
            ax.bar(
                [i + offsets[policy] for i in x],
                means,
                width=width,
                yerr=stds,
                color=colors[policy],
                alpha=0.86,
                capsize=3,
                label=short_label(policy),
            )
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=12)
        ax.grid(axis="y", color="#d0d0d0", linewidth=0.7)
    handles, legend_labels = axes.ravel()[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", ncol=len(POLICIES), frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save_figure(fig, path)
    plt.close(fig)


def plot_baseline_deltas(deltas: list[dict[str, Any]], path: Path) -> None:
    cases = sorted({str(r["case"]) for r in deltas})
    labels = [case_label(case) for case in cases]
    policies = [p for p in POLICIES if p != BASELINE_POLICY]
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.6), dpi=150)
    specs = [
        ("delivered_delta_pct", "Entregas vs baseline (%)"),
        ("avg_wait_s_delta_pct", "Espera vs baseline (%)"),
        ("energy_used_pct_delta_pct", "Energia vs baseline (%)"),
    ]
    colors = policy_colors()
    width = 0.23
    x = list(range(len(cases)))
    offsets = {policy: (idx - (len(policies) - 1) / 2.0) * width for idx, policy in enumerate(policies)}
    for ax, (key, title) in zip(axes, specs, strict=True):
        for policy in policies:
            values = []
            for case in cases:
                row = next(r for r in deltas if r["case"] == case and r["policy"] == policy)
                values.append(float(row[key]))
            ax.bar([i + offsets[policy] for i in x], values, width=width, color=colors[policy], alpha=0.86, label=short_label(policy))
        ax.axhline(0.0, color="#333333", linewidth=1.0)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=14)
        ax.grid(axis="y", color="#d0d0d0", linewidth=0.7)
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", ncol=len(policies), frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    save_figure(fig, path)
    plt.close(fig)


def plot_runs(rows: list[dict[str, Any]], path: Path) -> None:
    cases = sorted({str(r["case"]) for r in rows})
    fig, axes = plt.subplots(2, 2, figsize=(10.8, 8.0), dpi=150)
    colors = policy_colors()
    for ax, case in zip(axes.ravel(), cases, strict=False):
        for policy in POLICIES:
            group = [r for r in rows if r["case"] == case and r["policy"] == policy]
            ax.scatter(
                [float(r["energy_used_pct"]) for r in group],
                [float(r["delivered"]) for r in group],
                label=short_label(policy),
                color=colors[policy],
                alpha=0.72,
                s=28,
            )
        ax.set_title(case_label(case))
        ax.set_xlabel("Energia usada (% bateria acumulada)")
        ax.set_ylabel("Entregas")
        ax.grid(color="#d0d0d0", linewidth=0.7)
    handles, legend_labels = axes.ravel()[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", ncol=len(POLICIES), frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save_figure(fig, path)
    plt.close(fig)


def plot_objective_traces(objective_rows: list[dict[str, Any]], path: Path) -> None:
    plot_time_grid(
        objective_rows,
        path,
        value_key="j_policy",
        title="Funcion objetivo J(t)",
        ylabel="J(t)",
        policies=CONTROLLER_POLICIES,
        active_only=True,
    )


def plot_regret_traces(objective_rows: list[dict[str, Any]], path: Path) -> None:
    plot_time_grid(
        objective_rows,
        path,
        value_key="j_regret",
        title="Regret vs optimo Hungarian",
        ylabel="Regret J(t)",
        policies=("distributed_greedy", "replicator_distributed"),
        active_only=True,
    )


def plot_battery_traces(robot_rows: list[dict[str, Any]], path: Path) -> None:
    plot_time_grid(
        robot_rows,
        path,
        value_key="battery_pct",
        title="Battery life promedio",
        ylabel="Battery (%)",
        policies=CONTROLLER_POLICIES,
        active_only=False,
    )


def plot_time_grid(
    rows: list[dict[str, Any]],
    path: Path,
    value_key: str,
    title: str,
    ylabel: str,
    policies: tuple[str, ...],
    active_only: bool,
) -> None:
    if not rows:
        return
    cases = sorted({str(r["case"]) for r in rows})
    fig, axes = plt.subplots(2, 2, figsize=(12.0, 7.6), dpi=150)
    colors = policy_colors()
    for ax, case in zip(axes.ravel(), cases, strict=False):
        case_rows = [r for r in rows if str(r["case"]) == case]
        for policy in policies:
            policy_rows = [r for r in case_rows if str(r["policy"]) == policy]
            if active_only:
                policy_rows = [r for r in policy_rows if int(float(r.get("job_count", 1))) > 0 and int(float(r.get("candidate_count", 1))) > 0]
            xs, ys = binned_mean(policy_rows, value_key, bin_s=5.0)
            if xs:
                ax.plot(xs, ys, color=colors[policy], linewidth=1.7, label=short_label(policy))
        ax.set_title(case_label(case))
        ax.set_xlabel("t (s)")
        ax.set_ylabel(ylabel)
        ax.grid(color="#d0d0d0", linewidth=0.7)
    handles, labels = axes.ravel()[0].get_legend_handles_labels()
    _ = title
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.005), ncol=max(1, len(policies)), frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save_figure(fig, path)
    plt.close(fig)


def binned_mean(rows: list[dict[str, Any]], value_key: str, bin_s: float) -> tuple[list[float], list[float]]:
    bins: dict[float, list[float]] = {}
    for row in rows:
        t = float(row["t_s"])
        bucket = math.floor(t / bin_s) * bin_s
        bins.setdefault(bucket, []).append(float(row[value_key]))
    xs = sorted(bins)
    ys = [sum(bins[x]) / len(bins[x]) for x in xs]
    return xs, ys


def plot_trajectory_sample(robot_rows: list[dict[str, Any]], path: Path) -> None:
    rows = [r for r in robot_rows if str(r["case"]) == "balanced" and int(r["seed"]) == 0]
    if not rows:
        return
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.4), dpi=150)
    colors = policy_colors()
    for ax, policy in zip(axes, CONTROLLER_POLICIES, strict=True):
        policy_rows = [r for r in rows if str(r["policy"]) == policy]
        robots = sorted({str(r["robot"]) for r in policy_rows})
        for robot in robots:
            track = sorted((r for r in policy_rows if str(r["robot"]) == robot), key=lambda r: float(r["t_s"]))
            ax.plot([float(r["x_m"]) for r in track], [float(r["y_m"]) for r in track], linewidth=1.0, alpha=0.68)
            if track:
                ax.scatter([float(track[0]["x_m"])], [float(track[0]["y_m"])], color=colors[policy], s=12)
        ax.set_title(short_label(policy))
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        ax.set_aspect("equal", adjustable="box")
        ax.grid(color="#d0d0d0", linewidth=0.7)
    fig.suptitle("Trayectorias XY - balanced seed 0")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    save_figure(fig, path)
    plt.close(fig)


def plot_ieee_metric_ci(summary: list[dict[str, Any]], path: Path) -> None:
    cases = sorted({str(r["case"]) for r in summary})
    labels = [case_label(case) for case in cases]
    fig, axes = plt.subplots(2, 2, figsize=(12.0, 7.2))
    specs = [
        ("delivered_mean", "delivered_std", "n", "Delivered boxes", "higher"),
        ("avg_wait_s_mean", "avg_wait_s_std", "n", "Mean wait (s)", "lower"),
        ("energy_used_pct_mean", "energy_used_pct_std", "n", "Energy used (% battery)", "lower"),
        ("assignment_cost_mean", "assignment_cost_std", "n", "Assignment objective", "lower"),
    ]
    colors = policy_colors()
    width = 0.18
    x = list(range(len(cases)))
    offsets = {policy: (idx - (len(POLICIES) - 1) / 2.0) * width for idx, policy in enumerate(POLICIES)}
    for ax, (mean_key, std_key, n_key, ylabel, direction) in zip(axes.ravel(), specs, strict=True):
        for policy in POLICIES:
            means = []
            ci95 = []
            for case in cases:
                row = next(r for r in summary if str(r["case"]) == case and str(r["policy"]) == policy)
                n = max(1, int(row[n_key]))
                means.append(float(row[mean_key]))
                ci95.append(1.96 * float(row[std_key]) / math.sqrt(n) if n > 1 else 0.0)
            ax.bar(
                [i + offsets[policy] for i in x],
                means,
                width=width,
                yerr=ci95,
                color=colors[policy],
                edgecolor="#202020",
                linewidth=0.35,
                alpha=0.88,
                capsize=2.5,
                label=short_label(policy),
            )
        ax.set_ylabel(ylabel)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=12)
        ax.grid(axis="y", color="#d7d7d7")
        if direction == "lower":
            ax.annotate(
                "lower is better",
                xy=(0.98, 0.12),
                xytext=(0.70, 0.30),
                xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops={"arrowstyle": "->", "lw": 0.8, "color": "#333333"},
                ha="right",
                va="center",
                color="#333333",
            )
        else:
            ax.annotate(
                "higher is better",
                xy=(0.98, 0.88),
                xytext=(0.70, 0.70),
                xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops={"arrowstyle": "->", "lw": 0.8, "color": "#333333"},
                ha="right",
                va="center",
                color="#333333",
            )
    handles, legend_labels = axes.ravel()[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 1.005), ncol=len(POLICIES), frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save_figure(fig, path)
    plt.close(fig)


def plot_pareto_energy_wait(summary: list[dict[str, Any]], path: Path) -> None:
    cases = sorted({str(r["case"]) for r in summary})
    fig, axes = plt.subplots(2, 2, figsize=(11.6, 7.6))
    colors = policy_colors()
    for ax, case in zip(axes.ravel(), cases, strict=False):
        points = [r for r in summary if str(r["case"]) == case]
        for row in points:
            policy = str(row["policy"])
            energy = float(row["energy_used_pct_mean"])
            wait = float(row["avg_wait_s_mean"])
            delivered = float(row["delivered_mean"])
            dominated = is_dominated(row, points)
            ax.scatter(
                [energy],
                [wait],
                s=34 + delivered * 1.5,
                color=colors[policy],
                edgecolor="#111111" if not dominated else "#f0f0f0",
                linewidth=1.2 if not dominated else 0.45,
                alpha=0.88,
                label=short_label(policy),
            )
        ax.set_title(case_label(case))
        ax.set_xlabel("Energy used (% battery)")
        ax.set_ylabel("Mean wait (s)")
        ax.margins(x=0.12, y=0.18)
        ax.grid(color="#d7d7d7")
        ax.annotate(
            "Pareto direction",
            xy=(0.10, 0.15),
            xytext=(0.35, 0.38),
            xycoords="axes fraction",
            textcoords="axes fraction",
            arrowprops={"arrowstyle": "->", "lw": 1.0, "color": "#333333"},
            ha="center",
            color="#333333",
        )
    handles, legend_labels = axes.ravel()[0].get_legend_handles_labels()
    by_label = dict(zip(legend_labels, handles, strict=False))
    fig.legend(by_label.values(), by_label.keys(), loc="upper center", bbox_to_anchor=(0.5, 1.005), ncol=len(POLICIES), frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save_figure(fig, path)
    plt.close(fig)


def is_dominated(row: dict[str, Any], points: list[dict[str, Any]]) -> bool:
    energy = float(row["energy_used_pct_mean"])
    wait = float(row["avg_wait_s_mean"])
    delivered = float(row["delivered_mean"])
    for other in points:
        if other is row:
            continue
        other_energy = float(other["energy_used_pct_mean"])
        other_wait = float(other["avg_wait_s_mean"])
        other_delivered = float(other["delivered_mean"])
        no_worse = other_energy <= energy and other_wait <= wait and other_delivered >= delivered
        strictly_better = other_energy < energy or other_wait < wait or other_delivered > delivered
        if no_worse and strictly_better:
            return True
    return False


def plot_optimality_heatmap(gap_summary: list[dict[str, Any]], path: Path) -> None:
    rows = [r for r in gap_summary if str(r["policy"]) in {"distributed_greedy", "replicator_distributed"}]
    if not rows:
        return
    cases = sorted({str(r["case"]) for r in rows})
    policies = ("distributed_greedy", "replicator_distributed")
    matrix = []
    regret = []
    for case in cases:
        matrix.append([])
        regret.append([])
        for policy in policies:
            row = next((r for r in rows if str(r["case"]) == case and str(r["policy"]) == policy), None)
            matrix[-1].append(100.0 * float(row["hungarian_pair_match_rate"]) if row else 0.0)
            regret[-1].append(float(row["j_regret_mean"]) if row else 0.0)
    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    image = ax.imshow(matrix, cmap="YlGnBu", vmin=0.0, vmax=100.0, aspect="auto")
    ax.set_xticks(range(len(policies)))
    ax.set_xticklabels([short_label(p) for p in policies])
    ax.set_yticks(range(len(cases)))
    ax.set_yticklabels([case_label(case) for case in cases])
    ax.set_title("Closeness to instantaneous Hungarian optimum")
    for y, case in enumerate(cases):
        for x, _policy in enumerate(policies):
            ax.text(
                x,
                y,
                f"{matrix[y][x]:.1f}%\nR={regret[y][x]:.2f}",
                ha="center",
                va="center",
                color="#f7f7f7" if matrix[y][x] > 65 else "#0b1f2a",
                fontsize=8,
            )
    worst_y, worst_x = min(
        ((y, x) for y in range(len(cases)) for x in range(len(policies))),
        key=lambda item: matrix[item[0]][item[1]],
    )
    ax.annotate(
        "largest gap",
        xy=(worst_x, worst_y),
        xytext=(min(len(policies) - 0.35, worst_x + 0.75), max(-0.35, worst_y - 0.70)),
        arrowprops={"arrowstyle": "->", "lw": 0.9, "color": "#f7f7f7"},
        ha="center",
        color="#f7f7f7",
        bbox={"boxstyle": "round,pad=0.18", "facecolor": "#243447", "edgecolor": "none", "alpha": 0.72},
    )
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Hungarian pair match (%)")
    fig.tight_layout()
    save_figure(fig, path)
    plt.close(fig)


def plot_regret_boxplot(seed_gap_rows: list[dict[str, Any]], path: Path) -> None:
    rows = [r for r in seed_gap_rows if str(r["policy"]) in CONTROLLER_POLICIES]
    if not rows:
        return
    cases = sorted({str(r["case"]) for r in rows})
    policies = CONTROLLER_POLICIES
    colors = policy_colors()
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    positions = []
    labels = []
    box_data = []
    box_colors = []
    width = 0.22
    for case_idx, case in enumerate(cases):
        for policy_idx, policy in enumerate(policies):
            group = [float(r["j_regret_mean"]) for r in rows if str(r["case"]) == case and str(r["policy"]) == policy]
            if not group:
                continue
            positions.append(case_idx + (policy_idx - 1) * width)
            labels.append(short_label(policy))
            box_data.append(group)
            box_colors.append(colors[policy])
    box = ax.boxplot(box_data, positions=positions, widths=0.17, patch_artist=True, showfliers=True)
    for patch, color in zip(box["boxes"], box_colors, strict=False):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)
        patch.set_edgecolor("#222222")
    for median in box["medians"]:
        median.set_color("#111111")
        median.set_linewidth(1.1)
    ax.set_xticks(range(len(cases)))
    ax.set_xticklabels([case_label(case) for case in cases], rotation=10)
    ax.set_ylabel("Mean regret vs Hungarian")
    ax.grid(axis="y", color="#d7d7d7")
    legend_handles = [
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=colors[p], markeredgecolor="#222222", markersize=8, label=short_label(p))
        for p in policies
    ]
    ax.legend(handles=legend_handles, loc="upper left", frameon=False, ncol=len(policies))
    ax.annotate(
        "missed assignments are penalized",
        xy=(0.78, 0.80),
        xytext=(0.42, 0.90),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops={"arrowstyle": "->", "lw": 0.9, "color": "#333333"},
        ha="center",
        color="#333333",
        bbox={"boxstyle": "round,pad=0.18", "facecolor": "#ffffff", "edgecolor": "none", "alpha": 0.76},
    )
    fig.tight_layout()
    save_figure(fig, path)
    plt.close(fig)


def plot_battery_quantile_bands(robot_rows: list[dict[str, Any]], path: Path) -> None:
    if not robot_rows:
        return
    cases = sorted({str(r["case"]) for r in robot_rows})
    fig, axes = plt.subplots(2, 2, figsize=(12.0, 7.4))
    colors = policy_colors()
    for ax, case in zip(axes.ravel(), cases, strict=False):
        case_rows = [r for r in robot_rows if str(r["case"]) == case]
        for policy in CONTROLLER_POLICIES:
            xs, q25, q50, q75 = binned_quantiles(
                [r for r in case_rows if str(r["policy"]) == policy],
                "battery_pct",
                bin_s=5.0,
            )
            if not xs:
                continue
            color = colors[policy]
            ax.plot(xs, q50, color=color, label=short_label(policy))
            ax.fill_between(xs, q25, q75, color=color, alpha=0.16, linewidth=0.0)
        ax.axhline(25.0, color="#7a1f1f", linestyle="--", linewidth=0.9)
        ax.set_title(case_label(case))
        ax.set_xlabel("t (s)")
        ax.set_ylabel("Battery (%)")
        ax.set_ylim(0, 105)
        ax.grid(color="#d7d7d7")
        ax.annotate(
            "low-battery guard",
            xy=(0.76, 25.0),
            xytext=(0.55, 44.0),
            xycoords=("axes fraction", "data"),
            textcoords=("axes fraction", "data"),
            arrowprops={"arrowstyle": "->", "lw": 0.8, "color": "#7a1f1f"},
            color="#7a1f1f",
        )
    handles, legend_labels = axes.ravel()[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 1.005), ncol=len(CONTROLLER_POLICIES), frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save_figure(fig, path)
    plt.close(fig)


def plot_regret_ecdf(objective_rows: list[dict[str, Any]], path: Path) -> None:
    rows = [
        r
        for r in objective_rows
        if str(r["policy"]) in {"distributed_greedy", "replicator_distributed"}
        and int(float(r.get("job_count", 0))) > 0
        and int(float(r.get("candidate_count", 0))) > 0
    ]
    if not rows:
        return
    cases = sorted({str(r["case"]) for r in rows})
    colors = policy_colors()
    fig, axes = plt.subplots(2, 2, figsize=(11.6, 7.4))
    for ax, case in zip(axes.ravel(), cases, strict=False):
        for policy in ("distributed_greedy", "replicator_distributed"):
            values = sorted(float(r["j_regret"]) for r in rows if str(r["case"]) == case and str(r["policy"]) == policy)
            if not values:
                continue
            y = [(idx + 1) / len(values) for idx in range(len(values))]
            ax.step(values, y, where="post", color=colors[policy], label=short_label(policy))
        ax.set_xscale("symlog", linthresh=1.0)
        ax.set_ylim(0, 1.02)
        ax.set_title(case_label(case))
        ax.set_xlabel("Regret per decision event")
        ax.set_ylabel("ECDF")
        ax.grid(color="#d7d7d7")
        ax.annotate(
            "right tail = rare bad decisions",
            xy=(0.82, 0.72),
            xytext=(0.48, 0.50),
            xycoords="axes fraction",
            textcoords="axes fraction",
            arrowprops={"arrowstyle": "->", "lw": 0.8, "color": "#333333"},
            color="#333333",
        )
    handles, legend_labels = axes.ravel()[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 1.005), ncol=2, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save_figure(fig, path)
    plt.close(fig)


def plot_robot_state_timeline(robot_rows: list[dict[str, Any]], path: Path) -> None:
    case = "target_skew"
    seed = 0
    rows = [r for r in robot_rows if str(r["case"]) == case and int(r["seed"]) == seed and str(r["policy"]) == "replicator_distributed"]
    if not rows:
        rows = [r for r in robot_rows if int(r["seed"]) == seed and str(r["policy"]) == "replicator_distributed"]
    if not rows:
        return
    robots = sorted({str(r["robot"]) for r in rows})
    state_colors = {
        "idle": "#b7bdc6",
        "to_box": "#2f80ed",
        "pickup_wait": "#56ccf2",
        "to_unload": "#27ae60",
        "unload_wait": "#6fcf97",
        "to_charge": "#f2994a",
        "charging": "#eb5757",
    }
    fig, ax = plt.subplots(figsize=(12.0, 4.8))
    for idx, robot in enumerate(robots):
        track = sorted((r for r in rows if str(r["robot"]) == robot), key=lambda r: float(r["t_s"]))
        for start, duration, state in state_segments(track):
            ax.broken_barh([(start, duration)], (idx - 0.38, 0.76), facecolors=state_colors.get(state, "#999999"), edgecolors="none")
    ax.set_yticks(range(len(robots)))
    ax.set_yticklabels(robots)
    ax.set_xlabel("t (s)")
    ax.set_title(f"Robot state timeline - {case_label(str(rows[0]['case']))}, seed {seed}, Replicator")
    ax.grid(axis="x", color="#d7d7d7")
    legend_handles = [
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=color, markersize=8, label=state)
        for state, color in state_colors.items()
    ]
    ax.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=4, frameon=False)
    ax.annotate(
        "blue/green blocks show active transport",
        xy=(0.30, 0.88),
        xytext=(0.08, 1.08),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops={"arrowstyle": "->", "lw": 0.8, "color": "#333333"},
        color="#333333",
    )
    fig.tight_layout()
    save_figure(fig, path)
    plt.close(fig)


def binned_quantiles(rows: list[dict[str, Any]], value_key: str, bin_s: float) -> tuple[list[float], list[float], list[float], list[float]]:
    bins: dict[float, list[float]] = {}
    for row in rows:
        t = float(row["t_s"])
        bucket = math.floor(t / bin_s) * bin_s
        bins.setdefault(bucket, []).append(float(row[value_key]))
    xs = sorted(bins)
    q25 = [percentile(bins[x], 0.25) for x in xs]
    q50 = [percentile(bins[x], 0.50) for x in xs]
    q75 = [percentile(bins[x], 0.75) for x in xs]
    return xs, q25, q50, q75


def state_segments(track: list[dict[str, Any]]) -> list[tuple[float, float, str]]:
    if not track:
        return []
    segments: list[tuple[float, float, str]] = []
    start = float(track[0]["t_s"])
    prev_t = start
    state = str(track[0]["state"])
    sample_dt = 1.0
    if len(track) > 1:
        sample_dt = max(0.1, float(track[1]["t_s"]) - float(track[0]["t_s"]))
    for row in track[1:]:
        t = float(row["t_s"])
        row_state = str(row["state"])
        if row_state != state:
            segments.append((start, max(sample_dt, prev_t - start + sample_dt), state))
            start = t
            state = row_state
        prev_t = t
    segments.append((start, max(sample_dt, prev_t - start + sample_dt), state))
    return segments


def write_markdown_report(
    summary: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
    gap_summary: list[dict[str, Any]],
    path: Path,
) -> None:
    lines = [
        "# SP0 dispatch benchmark",
        "",
        "Layout used: 8 Pioneer AMR, 6 simultaneous homogeneous box tasks, 3 unload targets, 2x motion speed, battery-aware assignment.",
        "",
        "The previous balanced-only result was expected to be close because the scene is symmetric and saturated with available robots. This report adds a naive FIFO-nearest baseline and stress cases.",
        "",
        "Fitness and objective definitions:",
        "",
        "- Pair objective: `c_ij = d(robot_i,pickup_j) + d(pickup_j,target_j) + 0.35*d(target_j,base_i) + 0.035*(100-battery_i)`.",
        "- Pair fitness: `f_ij = 1/(1+c_ij)` for feasible battery assignments; infeasible pairs use `f_ij=0`.",
        "- Controller objective: `J(t)=sum(c_ij)` over assignments selected at decision time `t`.",
        "- Hungarian optimum: `J*_H(t)` is recomputed at the same state, candidates and pending jobs. `j_regret` adds a large penalty for missed assignments.",
        "",
        "## Summary",
        "",
        "| Case | Policy | Delivered | Avg wait s | Energy used pct | Assignment cost | Charge cycles |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary:
        lines.append(
            "| {case} | {policy} | {delivered:.4f} | {wait:.4f} | {energy:.4f} | {cost:.4f} | {charge:.4f} |".format(
                case=case_label(str(row["case"])),
                policy=short_label(str(row["policy"])),
                delivered=float(row["delivered_mean"]),
                wait=float(row["avg_wait_s_mean"]),
                energy=float(row["energy_used_pct_mean"]),
                cost=float(row["assignment_cost_mean"]),
                charge=float(row["charge_cycles_mean"]),
            )
        )
    lines.extend(
        [
            "",
            "## Delta vs FIFO-nearest baseline",
            "",
            "| Case | Policy | Delivered delta % | Wait delta % | Energy delta % | Assignment cost delta % |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in deltas:
        lines.append(
            "| {case} | {policy} | {delivered:.4f} | {wait:.4f} | {energy:.4f} | {cost:.4f} |".format(
                case=case_label(str(row["case"])),
                policy=short_label(str(row["policy"])),
                delivered=float(row["delivered_delta_pct"]),
                wait=float(row["avg_wait_s_delta_pct"]),
                energy=float(row["energy_used_pct_delta_pct"]),
                cost=float(row["assignment_cost_delta_pct"]),
            )
        )
    lines.extend(
        [
            "",
            "## Gap vs instantaneous Hungarian optimum",
            "",
            "| Case | Policy | J mean | J*_H mean | J gap mean | Regret mean | Assignment count gap | Hungarian pair match |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in gap_summary:
        if str(row["policy"]) == "hungarian_centralized":
            continue
        lines.append(
            "| {case} | {policy} | {j:.4f} | {jh:.4f} | {gap:.4f} | {regret:.4f} | {count_gap:.4f} | {match:.4f} |".format(
                case=case_label(str(row["case"])),
                policy=short_label(str(row["policy"])),
                j=float(row["j_policy_mean"]),
                jh=float(row["j_hungarian_opt_mean"]),
                gap=float(row["j_gap_abs_mean"]),
                regret=float(row["j_regret_mean"]),
                count_gap=float(row["assignment_count_gap_mean"]),
                match=float(row["hungarian_pair_match_rate"]),
            )
        )
    lines.extend(
        [
            "",
            "Interpretation: when the case is balanced, all cost-aware policies remain close. The useful comparison is against `FIFO nearest`, which ignores target and return-energy cost. Stress cases expose whether the cost-aware dispatchers reduce assignment cost, energy, or wait.",
            "",
            "Files:",
            "",
            "- `dispatch_policy_runs.csv`: per-seed raw runs.",
            "- `dispatch_policy_summary.csv`: mean/std by case and policy.",
            "- `dispatch_policy_baseline_delta.csv`: percentage deltas vs FIFO-nearest baseline.",
            "- `dispatch_policy_ci.csv`: mean, standard error and 95% confidence intervals by metric.",
            "- `dispatch_seed_hungarian_gap.csv`: per-seed distance to the instantaneous Hungarian optimum.",
            "- `dispatch_statistical_tests.csv`: paired per-seed deltas, 95% CI, Cohen dz and better-rate tests.",
            "- `dispatch_time_integrals.csv`: time-weighted battery, objective and regret integrals.",
            "- `dispatch_robot_trace.csv`: sampled robot `x_m`, `y_m`, state and battery life over time.",
            "- `dispatch_objective_trace.csv`: `J(t)`, `J*_H(t)`, gap/regret and fitness stats per decision event.",
            "- `dispatch_assignment_trace.csv`: selected robot-box pairs with cost, fitness and battery at assignment time.",
            "- `dispatch_hungarian_gap_summary.csv`: aggregate distance to instantaneous Hungarian optimum.",
            "- `dispatch_policy_comparison.png`: grouped comparison by case.",
            "- `dispatch_policy_baseline_delta.png`: deltas vs baseline.",
            "- `dispatch_policy_scatter.png`: delivery vs cumulative energy scatter.",
            "- `dispatch_objective_j_vs_t.png`: objective function over time for the three controllers.",
            "- `dispatch_hungarian_regret_vs_t.png`: greedy/replicator regret against Hungarian over time.",
            "- `dispatch_battery_life_vs_t.png`: average battery life over time.",
            "- `dispatch_xy_trajectories_seed0_balanced.png`: sampled XY trajectories for the three controllers.",
            "- `dispatch_ieee_metric_ci.png/.pdf`: publication-style metric panel with 95% CI.",
            "- `dispatch_pareto_energy_wait.png/.pdf`: energy-wait Pareto map with callout arrows.",
            "- `dispatch_optimality_heatmap.png/.pdf`: Hungarian match-rate heatmap with regret annotations.",
            "- `dispatch_regret_boxplot.png/.pdf`: per-seed regret distribution.",
            "- `dispatch_battery_quantile_bands.png/.pdf`: median and IQR battery traces.",
            "- `dispatch_regret_ecdf.png/.pdf`: empirical regret distribution with right-tail callouts.",
            "- `dispatch_robot_state_timeline_seed0_target_skew.png/.pdf`: robot state timeline sample.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def policy_colors() -> dict[str, str]:
    return {
        BASELINE_POLICY: "#8a8f98",
        "hungarian_centralized": "#2f80ed",
        "distributed_greedy": "#27ae60",
        "replicator_distributed": "#f2994a",
    }


def case_label(case: str) -> str:
    return {
        "balanced": "Balanced",
        "battery_stress": "Battery stress",
        "target_skew": "Target skew",
        "scarce_robots": "Scarce robots",
    }.get(case, case)


def short_label(policy: str) -> str:
    return {
        BASELINE_POLICY: "FIFO nearest",
        "hungarian_centralized": "Hungarian",
        "distributed_greedy": "Greedy dist.",
        "replicator_distributed": "Replicator",
    }[policy]


if __name__ == "__main__":
    raise SystemExit(main())

"""Cumulative certificate decisions and reduced-order load simulation."""

from __future__ import annotations

import itertools
import math
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import lsq_linear

from viu_mrob_tfm.control.explicit_law import (
    CircularHazard,
    ExplicitControlGains,
    closed_form_hocbf_projection,
    required_wrench_pd,
    rotation,
    wrap_angle,
)

from .model import (
    CertificateStage,
    CoalitionDecision,
    FailureCode,
    PhysicalWorld,
    PROTOCOL_VERSION,
    stable_token,
)


STAGE_ORDER = tuple(CertificateStage)
WRENCH_EPSILON = 0.16
LOAD_MASS_KG = 18.0
LOAD_INERTIA_KGM2 = 5.2
LOAD_DAMPING = np.diag([1.5, 1.5, 0.9])
DT_S = 0.1
DURATION_S = 22.0
LOAD_SAFETY_RADIUS_M = 0.82


@dataclass(slots=True)
class WrenchFit:
    normalized_residual: float
    achieved: np.ndarray
    forces: np.ndarray


def run_variant(
    world: PhysicalWorld,
    stage: CertificateStage | str,
    *,
    retain_trajectory: bool = False,
    protocol_version: str = PROTOCOL_VERSION,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Execute one cumulative variant and retain every certificate outcome."""

    selected_stage = CertificateStage(stage)
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    decision = decision_for_stage(world, selected_stage)
    quorum_ok = len(decision.selected) >= world.quorum
    capacity_value = effective_capacity(world, decision.selected)
    capacity_ok = capacity_value + 1e-9 >= world.capacity_demand
    static_fit = wrench_fit(world, decision, world.wrench_demand)
    wrench_ok = static_fit.normalized_residual <= WRENCH_EPSILON
    first_failed = first_failed_certificate(quorum_ok, capacity_ok, wrench_ok)
    accepted = stage_acceptance(selected_stage, quorum_ok, capacity_ok, wrench_ok)
    simulation, trajectory = simulate_load(world, selected_stage, decision)
    final_success = bool(
        quorum_ok
        and capacity_ok
        and wrench_ok
        and simulation["target_reached"]
        and not simulation["collision"]
        and not simulation["dropout_unrecovered"]
    )
    failure = classify_failure(
        quorum_ok=quorum_ok,
        capacity_ok=capacity_ok,
        wrench_ok=wrench_ok,
        simulation=simulation,
    )
    runtime_wall = time.perf_counter() - started_wall
    runtime_cpu = time.process_time() - started_cpu
    row: dict[str, Any] = {
        "protocol_version": protocol_version,
        "run_id": stable_token(protocol_version, world.world_hash, selected_stage.value),
        "task_token": stable_token(world.world_hash, selected_stage.value, "task"),
        "world_id": world.world_id,
        "world_hash": world.world_hash,
        "world_seed": world.seed,
        "scenario_family": world.family,
        "stage": selected_stage.value,
        "method_id": selected_stage.value,
        "n_robots": world.n_robots,
        "selected_robots": len(decision.selected),
        "selected_robot_ids": json_list(decision.selected),
        "selected_slot_ids": json_list(decision.slot_by_robot),
        "recovered_robot": int(
            simulation.get("recovered_robot_dynamic", decision.recovered_robot)
        ),
        "quorum_required": world.quorum,
        "integer_quorum_ok": bool(quorum_ok),
        "capacity_demand": world.capacity_demand,
        "effective_capacity": capacity_value,
        "capacity_ok": bool(capacity_ok),
        "static_wrench_residual": static_fit.normalized_residual,
        "wrench_ok": bool(wrench_ok),
        "accepted_by_stage": bool(accepted),
        "first_failed_certificate": first_failed,
        "physical_false_positive": bool(accepted and not final_success),
        "final_physical_success": final_success,
        "success": final_success,
        "failure_code": failure.value,
        "runtime_wall_s": float(runtime_wall),
        "runtime_cpu_s": float(runtime_cpu),
        "runtime_s": float(runtime_wall),
        **simulation,
    }
    if not retain_trajectory:
        trajectory = []
    return row, trajectory


def decision_for_stage(world: PhysicalWorld, stage: CertificateStage) -> CoalitionDecision:
    raw = _raw_preference(world)
    if stage == CertificateStage.RAW_PREF:
        return raw
    qr = _integer_qr(world, raw)
    if stage == CertificateStage.INTEGER_QR:
        return qr
    capacity = _capacity_closure(world, qr)
    if stage == CertificateStage.CAPACITY:
        return capacity
    wrench = _pair_wrench_closure(world, capacity)
    if stage == CertificateStage.WRENCH_PAIR:
        return wrench
    return _mechanics_closure(world, capacity, wrench)


def _raw_preference(world: PhysicalWorld) -> CoalitionDecision:
    distances = np.linalg.norm(world.robot_positions - world.load_start[:2], axis=1)
    utility = 1.4 * world.robot_health + 0.07 * world.robot_capacity - 0.28 * distances
    threshold = float(np.quantile(utility, 0.55))
    selected = tuple(int(idx) for idx in np.flatnonzero(utility >= threshold))
    selected = selected or (int(np.argmax(utility)),)
    slots = tuple(range(len(selected)))
    return CoalitionDecision(selected=selected, slot_by_robot=slots, messages=world.n_robots)


def _integer_qr(world: PhysicalWorld, raw: CoalitionDecision) -> CoalitionDecision:
    chosen = list(raw.selected)
    distances = np.linalg.norm(world.robot_positions - world.load_start[:2], axis=1)
    candidates = sorted(
        (idx for idx in range(world.n_robots) if idx not in chosen),
        key=lambda idx: (float(distances[idx]), idx),
    )
    while len(chosen) < world.quorum and candidates:
        chosen.append(candidates.pop(0))
    chosen = chosen[: len(world.slot_offsets)]
    return CoalitionDecision(
        selected=tuple(chosen),
        slot_by_robot=tuple(range(len(chosen))),
        messages=raw.messages + len(candidates) + len(chosen),
    )


def _capacity_closure(world: PhysicalWorld, qr: CoalitionDecision) -> CoalitionDecision:
    chosen = list(qr.selected)
    distances = np.linalg.norm(world.robot_positions - world.load_start[:2], axis=1)
    candidates = sorted(
        (idx for idx in range(world.n_robots) if idx not in chosen),
        key=lambda idx: (
            -float(world.robot_capacity[idx] * world.robot_health[idx])
            / max(1.0 + float(distances[idx]), 1e-9),
            idx,
        ),
    )
    while effective_capacity(world, chosen) < world.capacity_demand and candidates:
        chosen.append(candidates.pop(0))
    chosen = chosen[: len(world.slot_offsets)]
    return CoalitionDecision(
        selected=tuple(chosen),
        slot_by_robot=tuple(range(len(chosen))),
        messages=qr.messages + 2 * world.n_robots,
    )


def _pair_wrench_closure(world: PhysicalWorld, initial: CoalitionDecision) -> CoalitionDecision:
    """Bounded one/two-robot neighborhood with greedy slot complementarity."""

    base = tuple(initial.selected)
    candidates: set[tuple[int, ...]] = {tuple(sorted(base))}
    idle = [idx for idx in range(world.n_robots) if idx not in base]
    for idx in idle:
        candidates.add(tuple(sorted((*base, idx))))
    for first, second in itertools.combinations(idle, 2):
        candidates.add(tuple(sorted((*base, first, second))))
    if len(base) > world.quorum:
        for removed in base:
            kept = tuple(idx for idx in base if idx != removed)
            if len(kept) >= world.quorum:
                candidates.add(tuple(sorted(kept)))

    best: CoalitionDecision | None = None
    best_key = (math.inf, math.inf, math.inf, ())
    distances = np.linalg.norm(world.robot_positions - world.load_start[:2], axis=1)
    for selected in candidates:
        if len(selected) > len(world.slot_offsets):
            continue
        slots = _greedy_complementary_slots(world, selected)
        proposal = CoalitionDecision(selected=selected, slot_by_robot=slots)
        fit = wrench_fit(world, proposal, world.wrench_demand)
        capacity_deficit = max(world.capacity_demand - effective_capacity(world, selected), 0.0)
        travel = float(np.sum(distances[list(selected)]))
        key = (fit.normalized_residual + 0.02 * capacity_deficit, travel, len(selected), selected)
        if key < best_key:
            best_key = key
            best = proposal
    assert best is not None
    return CoalitionDecision(
        selected=best.selected,
        slot_by_robot=best.slot_by_robot,
        messages=initial.messages + len(candidates) * 2,
    )


def _mechanics_closure(
    world: PhysicalWorld,
    capacity: CoalitionDecision,
    wrench: CoalitionDecision,
) -> CoalitionDecision:
    """Preserve static certificates while restoring dynamic control authority.

    The wrench-local search may remove a robot because the static residual is
    unchanged.  Mechanics cannot make that reduction for free: the union keeps
    the certified wrench geometry and the capacity-stage traction reserve.
    """

    selected = tuple(sorted(set(capacity.selected) | set(wrench.selected)))
    selected = selected[: len(world.slot_offsets)]
    slots = _greedy_complementary_slots(world, selected)
    return CoalitionDecision(
        selected=selected,
        slot_by_robot=slots,
        messages=wrench.messages + 2 * len(selected),
    )

def _greedy_complementary_slots(world: PhysicalWorld, selected: tuple[int, ...]) -> tuple[int, ...]:
    chosen_slots: list[int] = []
    for robot in selected:
        best_slot = None
        best_residual = math.inf
        for slot in range(len(world.slot_offsets)):
            if slot in chosen_slots:
                continue
            proposal = CoalitionDecision(
                selected=tuple(selected[: len(chosen_slots) + 1]),
                slot_by_robot=tuple((*chosen_slots, slot)),
            )
            fit = wrench_fit(world, proposal, world.wrench_demand)
            distance_penalty = 1e-3 * float(
                np.linalg.norm(world.robot_positions[robot] - world.load_start[:2])
            )
            if fit.normalized_residual + distance_penalty < best_residual:
                best_residual = fit.normalized_residual + distance_penalty
                best_slot = slot
        assert best_slot is not None
        chosen_slots.append(best_slot)
    return tuple(chosen_slots)


def effective_capacity(world: PhysicalWorld, selected: tuple[int, ...] | list[int]) -> float:
    if not selected:
        return 0.0
    indices = np.asarray(selected, dtype=int)
    return float(np.sum(world.robot_capacity[indices] * world.robot_health[indices]))


def wrench_fit(
    world: PhysicalWorld,
    decision: CoalitionDecision,
    demanded_wrench: np.ndarray,
    *,
    active: set[int] | None = None,
    theta: float = 0.0,
    health_estimate: np.ndarray | None = None,
    signed_actuation: bool = False,
) -> WrenchFit:
    slot_map = decision.slot_map()
    selected = [idx for idx in decision.selected if active is None or idx in active]
    if not selected:
        demand = np.asarray(demanded_wrench, dtype=float)
        return WrenchFit(1.0, np.zeros(3), np.zeros(0))
    rot = rotation(theta)
    columns: list[np.ndarray] = []
    upper: list[float] = []
    health = world.robot_health if health_estimate is None else health_estimate
    for robot in selected:
        slot = slot_map[robot]
        offset = rot @ world.slot_offsets[slot]
        direction = rot @ world.slot_normals[slot]
        torque = offset[0] * direction[1] - offset[1] * direction[0]
        columns.append(np.array([direction[0], direction[1], torque]))
        upper.append(float(world.robot_force_limit[robot] * max(health[robot], 0.05)))
    matrix = np.column_stack(columns)
    demand = np.asarray(demanded_wrench, dtype=float)
    upper_bound = np.asarray(upper)
    lower_bound = -upper_bound if signed_actuation else np.zeros(len(upper))
    result = lsq_linear(
        matrix,
        demand,
        bounds=(lower_bound, upper_bound),
        lsmr_tol="auto",
    )
    achieved = matrix @ result.x
    residual = float(np.linalg.norm(achieved - demand) / max(np.linalg.norm(demand), 1e-9))
    return WrenchFit(residual, achieved, np.asarray(result.x))


def simulate_load(
    world: PhysicalWorld,
    stage: CertificateStage,
    original_decision: CoalitionDecision,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    q = world.load_start.astype(float).copy()
    qd = np.zeros(3, dtype=float)
    decision = original_decision
    active = set(decision.selected)
    latest_health = world.robot_health.copy()
    queues: dict[int, list[tuple[int, float]]] = {idx: [] for idx in range(world.n_robots)}
    last_seen = np.zeros(world.n_robots, dtype=int)
    rng = np.random.default_rng(world.seed + 4049 * (STAGE_ORDER.index(stage) + 1))
    target_reached = False
    collision = False
    dropout_unrecovered = False
    recovery_count = 0
    recovery_attempted = False
    recovered_robot = -1
    messages = int(decision.messages)
    delivered_step = -1
    safety_interventions = 0
    energy_balance_residuals: list[float] = []
    wrench_residuals: list[float] = []
    trajectory: list[dict[str, Any]] = []
    previous_energy = kinetic_energy(qd)
    dropout_step = int(world.dropout_time_s / DT_S) if math.isfinite(world.dropout_time_s) else 10**9

    for step in range(int(DURATION_S / DT_S) + 1):
        t_s = step * DT_S
        if step == dropout_step and world.dropout_robot in active:
            active.remove(world.dropout_robot)
        if stage == CertificateStage.ROBUST_LOCAL:
            messages += _update_messages(world, step, active, latest_health, last_seen, queues, rng)
            if (
                not recovery_attempted
                and world.dropout_robot in original_decision.selected
                and step >= dropout_step + max(2, world.delay_steps)
                and world.dropout_robot not in active
            ):
                # One dropout is one recovery event.  The old implementation
                # retriggered this branch on every subsequent step and could
                # recruit several idle robots for the same failure.
                recovery_attempted = True
                replacement = _replacement_robot(world, decision, active)
                slot_map = decision.slot_map()
                vacated_slot = slot_map.get(world.dropout_robot)
                if replacement >= 0 and vacated_slot is not None:
                    selected = tuple(idx for idx in decision.selected if idx != world.dropout_robot) + (replacement,)
                    slots = tuple(
                        slot_map[idx] for idx in decision.selected if idx != world.dropout_robot
                    ) + (vacated_slot,)
                    decision = CoalitionDecision(
                        selected=selected,
                        slot_by_robot=slots,
                        messages=messages,
                        recovered_robot=replacement,
                    )
                    active.add(replacement)
                    recovery_count += 1
                    recovered_robot = replacement
        elif step >= dropout_step and world.dropout_robot in original_decision.selected:
            dropout_unrecovered = True

        control_target = _control_target(world, stage, q)
        pose_error = control_target - q
        pose_error[2] = wrap_angle(pose_error[2])
        total_limit = float(np.sum(world.robot_force_limit[list(active)])) if active else 1.0
        desired, _ = required_wrench_pd(
            mass_total_kg=LOAD_MASS_KG,
            inertia_total_kgm2=LOAD_INERTIA_KGM2,
            pose=q,
            twist=qd,
            target_pose=control_target,
            gains=ExplicitControlGains(
                load_position_bandwidth=0.85,
                load_orientation_bandwidth=0.9,
                safety_k1=2.4,
                safety_k2=2.4,
            ),
            force_limit_sum_n=total_limit,
        )
        if stage in {CertificateStage.MECHANICS_SAFE, CertificateStage.ROBUST_LOCAL}:
            nominal_accel = desired[:2] / LOAD_MASS_KG
            safe_accel = closed_form_hocbf_projection(
                nominal_accel,
                q[:2],
                qd[:2],
                [
                    CircularHazard(
                        center_xy=world.obstacle_center,
                        velocity_xy=np.zeros(2),
                        radius_m=world.obstacle_radius,
                    )
                ],
                LOAD_SAFETY_RADIUS_M,
                gains=ExplicitControlGains(safety_k1=2.4, safety_k2=2.4),
                passes=8,
            )
            if float(np.linalg.norm(safe_accel - nominal_accel)) > 1e-8:
                safety_interventions += 1
            desired[:2] = LOAD_MASS_KG * safe_accel

        health_for_control = latest_health if stage == CertificateStage.ROBUST_LOCAL else world.robot_health
        fit = wrench_fit(
            world,
            decision,
            desired,
            active=active,
            theta=float(q[2]),
            health_estimate=health_for_control,
            # Rigid grasps transmit bounded push/pull traction after the
            # unilateral static contact certificate has been established.
            signed_actuation=True,
        )
        wrench_residuals.append(fit.normalized_residual)
        qdd = np.linalg.solve(
            np.diag([LOAD_MASS_KG, LOAD_MASS_KG, LOAD_INERTIA_KGM2]),
            fit.achieved - LOAD_DAMPING @ qd,
        )
        qd += DT_S * qdd
        qd[:2] = np.clip(qd[:2], -1.25, 1.25)
        qd[2] = float(np.clip(qd[2], -0.9, 0.9))
        q += DT_S * qd
        q[2] = wrap_angle(float(q[2]))
        clearance = float(
            np.linalg.norm(q[:2] - world.obstacle_center)
            - world.obstacle_radius
            - LOAD_SAFETY_RADIUS_M
        )
        collision = collision or clearance < 0.0
        energy = kinetic_energy(qd)
        power = float(np.dot(fit.achieved, qd) - qd @ LOAD_DAMPING @ qd)
        energy_balance_residuals.append(abs((energy - previous_energy) - DT_S * power))
        previous_energy = energy
        pos_error = float(np.linalg.norm(world.load_target[:2] - q[:2]))
        theta_error = abs(wrap_angle(float(world.load_target[2] - q[2])))
        if pos_error <= 0.45 and theta_error <= 0.28:
            target_reached = True
            delivered_step = step
        trajectory.append(
            {
                "time_s": t_s,
                "x": float(q[0]),
                "y": float(q[1]),
                "theta": float(q[2]),
                "vx": float(qd[0]),
                "vy": float(qd[1]),
                "omega": float(qd[2]),
                "clearance_m": clearance,
                "wrench_residual": fit.normalized_residual,
                "active_robots": len(active),
                "target_reached": target_reached,
            }
        )
        if target_reached:
            break

    min_clearance = min((row["clearance_m"] for row in trajectory), default=math.nan)
    final_position_error = float(np.linalg.norm(world.load_target[:2] - q[:2]))
    final_orientation_error = abs(wrap_angle(float(world.load_target[2] - q[2])))
    time_to_solution = delivered_step * DT_S if delivered_step >= 0 else DURATION_S
    return (
        {
            "target_reached": bool(target_reached),
            "collision": bool(collision),
            "dropout_unrecovered": bool(dropout_unrecovered and recovery_count == 0),
            "recovery_count": int(recovery_count),
            "recovered_robot_dynamic": int(recovered_robot),
            "final_selected_robot_ids": json_list(tuple(sorted(active))),
            "final_selected_slot_ids": json_list(decision.slot_by_robot),
            "final_selected_robots": int(len(active)),
            "time_to_solution_s": float(time_to_solution),
            "time_censored": bool(not target_reached),
            "final_position_error_m": final_position_error,
            "final_orientation_error_rad": final_orientation_error,
            "minimum_clearance_m": float(min_clearance),
            "mean_dynamic_wrench_residual": float(np.mean(wrench_residuals)),
            "p95_dynamic_wrench_residual": float(np.quantile(wrench_residuals, 0.95)),
            "mean_energy_balance_residual": float(np.mean(energy_balance_residuals)),
            "safety_intervention_count": int(safety_interventions),
            "messages": int(messages),
            "bytes": int(messages * 48),
        },
        trajectory,
    )


def _control_target(
    world: PhysicalWorld,
    stage: CertificateStage,
    q: np.ndarray,
) -> np.ndarray:
    """Return a nominal target before the HOCBF safety filter.

    Only mechanics-aware stages receive a deterministic obstacle waypoint.
    The waypoint is not a safety certificate: safety remains the responsibility
    of the HOCBF projection and is verified directly on the trajectory.
    """

    if (
        world.family != "obstacle_network_dropout"
        or stage not in {CertificateStage.MECHANICS_SAFE, CertificateStage.ROBUST_LOCAL}
        or q[0] > world.obstacle_center[0] + world.obstacle_radius + 0.75
    ):
        return world.load_target
    side = 1.0 if world.seed % 2 == 0 else -1.0
    waypoint = world.load_target.copy()
    waypoint[0] = world.obstacle_center[0] + world.obstacle_radius + 0.90
    waypoint[1] = world.obstacle_center[1] + side * (
        world.obstacle_radius + LOAD_SAFETY_RADIUS_M + 0.75
    )
    waypoint[2] = 0.5 * world.load_target[2]
    return waypoint

def _update_messages(
    world: PhysicalWorld,
    step: int,
    active: set[int],
    latest_health: np.ndarray,
    last_seen: np.ndarray,
    queues: dict[int, list[tuple[int, float]]],
    rng: np.random.Generator,
) -> int:
    sent = 0
    for robot in range(world.n_robots):
        if robot in active and rng.random() >= world.packet_loss:
            queues[robot].append((step + world.delay_steps, float(world.robot_health[robot])))
            sent += 1
        delivered = [item for item in queues[robot] if item[0] <= step]
        queues[robot][:] = [item for item in queues[robot] if item[0] > step]
        if delivered:
            latest_health[robot] = delivered[-1][1]
            last_seen[robot] = step
        elif step - int(last_seen[robot]) > max(5, 2 * world.delay_steps):
            latest_health[robot] = 0.05
    return sent


def _replacement_robot(world: PhysicalWorld, decision: CoalitionDecision, active: set[int]) -> int:
    idle = [idx for idx in range(world.n_robots) if idx not in decision.selected and idx not in active]
    if not idle:
        return -1
    return max(
        idle,
        key=lambda idx: (
            float(world.robot_capacity[idx] * world.robot_health[idx]),
            -float(np.linalg.norm(world.robot_positions[idx] - world.load_start[:2])),
        ),
    )


def kinetic_energy(qd: np.ndarray) -> float:
    return float(
        0.5 * LOAD_MASS_KG * np.dot(qd[:2], qd[:2])
        + 0.5 * LOAD_INERTIA_KGM2 * qd[2] ** 2
    )


def stage_acceptance(
    stage: CertificateStage, quorum_ok: bool, capacity_ok: bool, wrench_ok: bool
) -> bool:
    if stage == CertificateStage.RAW_PREF:
        return True
    if stage == CertificateStage.INTEGER_QR:
        return quorum_ok
    if stage == CertificateStage.CAPACITY:
        return quorum_ok and capacity_ok
    return quorum_ok and capacity_ok and wrench_ok


def first_failed_certificate(quorum_ok: bool, capacity_ok: bool, wrench_ok: bool) -> str:
    if not quorum_ok:
        return "INTEGER_QR"
    if not capacity_ok:
        return "CAPACITY"
    if not wrench_ok:
        return "WRENCH_PAIR"
    return "NONE"


def classify_failure(
    *,
    quorum_ok: bool,
    capacity_ok: bool,
    wrench_ok: bool,
    simulation: dict[str, Any],
) -> FailureCode:
    if not quorum_ok:
        return FailureCode.INCOMPLETE_QUORUM
    if not capacity_ok:
        return FailureCode.CAPACITY_DEFICIT
    if not wrench_ok:
        return FailureCode.WRENCH_INFEASIBLE
    if simulation["collision"]:
        return FailureCode.COLLISION
    if simulation["dropout_unrecovered"]:
        return FailureCode.DROPOUT_UNRECOVERED
    if not simulation["target_reached"]:
        return FailureCode.TARGET_NOT_REACHED
    if simulation["final_orientation_error_rad"] > 0.28:
        return FailureCode.POSE_INVALID
    return FailureCode.NONE


def json_list(values: tuple[int, ...]) -> str:
    return "[" + ",".join(str(value) for value in values) + "]"

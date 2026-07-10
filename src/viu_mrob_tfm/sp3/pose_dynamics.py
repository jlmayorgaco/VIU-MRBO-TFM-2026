"""Planar Euler-Lagrange pose transport demo for SP3."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from scipy.optimize import lsq_linear

from viu_mrob_tfm.sp3.methods import SP3Assignment
from viu_mrob_tfm.sp3.scenario import SP3Problem


@dataclass(frozen=True, slots=True)
class PoseTransportConfig:
    load_index: int = 0
    initial_theta_rad: float = math.radians(-28.0)
    target_xy: tuple[float, float] = (2.2, 1.25)
    target_theta_rad: float = math.radians(58.0)
    dt: float = 0.04
    steps: int = 320
    kp_pos: float = 34.0
    kd_pos: float = 22.0
    kp_theta: float = 28.0
    kd_theta: float = 60.0
    linear_damping: float = 7.5
    angular_damping: float = 60.0
    force_command_limit_n: float = 95.0
    torque_command_limit_nm: float = 45.0
    recruit_fraction: float = 0.24
    complete_uncovered_slots: bool = True


@dataclass(frozen=True, slots=True)
class PoseTransportFrame:
    step: int
    time_s: float
    q: np.ndarray
    qd: np.ndarray
    desired_wrench: np.ndarray
    achieved_wrench: np.ndarray
    residual_norm: float
    lambdas: np.ndarray
    hamiltonian: float
    kinetic_energy: float
    potential_energy: float
    robot_positions: np.ndarray
    slot_positions: np.ndarray
    slot_directions: np.ndarray
    game_payoffs: np.ndarray


@dataclass(frozen=True, slots=True)
class PoseTransportResult:
    config: PoseTransportConfig
    assignment: SP3Assignment
    frames: tuple[PoseTransportFrame, ...]
    mass_kg: float
    inertia_kg_m2: float
    final_position_error_m: float
    final_orientation_error_rad: float
    initial_hamiltonian: float
    final_hamiltonian: float
    mean_residual_norm: float
    max_torque_nm: float
    slot_coverage_ratio: float


def complete_pose_assignment(problem: SP3Problem, assignment: SP3Assignment, load_idx: int = 0) -> SP3Assignment:
    """Fill uncovered slots with nearest idle AMRs for the pose transport demo."""

    labels = np.asarray(assignment.labels, dtype=int).copy()
    slots = np.asarray(assignment.slot_labels, dtype=int).copy()
    load = problem.world.loads[load_idx]
    used_slots = {int(value) - 1 for value in slots[labels == load_idx + 1] if int(value) > 0}
    idle = {idx for idx, label in enumerate(labels) if int(label) == 0}
    for slot_idx, slot in enumerate(problem.load_slots[load_idx]):
        if slot_idx in used_slots or not idle:
            continue
        slot_xy = load.pickup + slot.offset_xy
        robot_idx = min(idle, key=lambda idx: float(np.linalg.norm(problem.world.robots[idx].position - slot_xy)))
        labels[robot_idx] = load_idx + 1
        slots[robot_idx] = slot_idx + 1
        idle.remove(robot_idx)
        used_slots.add(slot_idx)
    return SP3Assignment(labels=labels, slot_labels=slots, method=f"{assignment.method}_pose_slots")


def simulate_pose_transport(problem: SP3Problem, assignment: SP3Assignment, config: PoseTransportConfig | None = None) -> PoseTransportResult:
    """Simulate rigid payload translation/rotation under bounded AMR contact forces."""

    cfg = config or PoseTransportConfig()
    load_idx = int(cfg.load_index)
    load = problem.world.loads[load_idx]
    if cfg.complete_uncovered_slots:
        assignment = complete_pose_assignment(problem, assignment, load_idx)
    pairs = _assigned_pairs(problem, assignment, load_idx)

    mass = float(max(load.mass_kg, 1e-6))
    inertia = float(mass * (load.length_m**2 + load.width_m**2) / 12.0)
    m_matrix = np.diag([mass, mass, inertia])
    damping = np.diag([cfg.linear_damping, cfg.linear_damping, cfg.angular_damping])
    q = np.array([float(load.pickup[0]), float(load.pickup[1]), float(cfg.initial_theta_rad)], dtype=float)
    qd = np.zeros(3, dtype=float)
    target = np.array([float(cfg.target_xy[0]), float(cfg.target_xy[1]), float(cfg.target_theta_rad)], dtype=float)
    frames: list[PoseTransportFrame] = []

    for step in range(max(1, int(cfg.steps)) + 1):
        slot_positions, slot_directions, g_matrix, force_limits = _contact_geometry(problem, assignment, load_idx, q)
        desired = _desired_wrench(q, qd, target, cfg)
        lambdas = _bounded_wrench_projection(g_matrix, desired, force_limits, cfg)
        achieved = g_matrix @ lambdas if lambdas.size else np.zeros(3, dtype=float)
        residual = _normalized_residual(desired, achieved, cfg)
        robot_positions = _robot_positions_from_slots(slot_positions, slot_directions)
        payoffs = _vector_game_payoffs(g_matrix, desired - achieved, lambdas, force_limits, cfg)
        kinetic, potential, hamiltonian = _energies(q, qd, target, m_matrix, cfg)
        frames.append(
            PoseTransportFrame(
                step=step,
                time_s=step * cfg.dt,
                q=q.copy(),
                qd=qd.copy(),
                desired_wrench=desired.copy(),
                achieved_wrench=achieved.copy(),
                residual_norm=float(residual),
                lambdas=lambdas.copy(),
                hamiltonian=float(hamiltonian),
                kinetic_energy=float(kinetic),
                potential_energy=float(potential),
                robot_positions=robot_positions.copy(),
                slot_positions=slot_positions.copy(),
                slot_directions=slot_directions.copy(),
                game_payoffs=payoffs.copy(),
            )
        )
        if step >= int(cfg.steps):
            break
        qdd = np.linalg.solve(m_matrix, achieved - damping @ qd)
        qd = qd + cfg.dt * qdd
        q = q + cfg.dt * qd
        q[2] = _wrap_angle(float(q[2]))

    final = frames[-1]
    initial = frames[0]
    pos_error = float(np.linalg.norm(target[:2] - final.q[:2]))
    theta_error = abs(_wrap_angle(float(target[2] - final.q[2])))
    residuals = np.asarray([frame.residual_norm for frame in frames], dtype=float)
    max_torque = float(np.max(np.abs([frame.achieved_wrench[2] for frame in frames]))) if frames else 0.0
    covered = len({slot_idx for _robot_idx, slot_idx in pairs})
    slot_coverage = float(covered / max(len(problem.load_slots[load_idx]), 1))
    return PoseTransportResult(
        config=cfg,
        assignment=assignment,
        frames=tuple(frames),
        mass_kg=mass,
        inertia_kg_m2=inertia,
        final_position_error_m=pos_error,
        final_orientation_error_rad=theta_error,
        initial_hamiltonian=float(initial.hamiltonian),
        final_hamiltonian=float(final.hamiltonian),
        mean_residual_norm=float(np.mean(residuals)) if residuals.size else 0.0,
        max_torque_nm=max_torque,
        slot_coverage_ratio=slot_coverage,
    )


def pose_transport_summary(result: PoseTransportResult) -> dict[str, Any]:
    return {
        "frames": len(result.frames),
        "mass_kg": result.mass_kg,
        "inertia_kg_m2": result.inertia_kg_m2,
        "final_position_error_m": result.final_position_error_m,
        "final_orientation_error_deg": math.degrees(result.final_orientation_error_rad),
        "initial_hamiltonian": result.initial_hamiltonian,
        "final_hamiltonian": result.final_hamiltonian,
        "hamiltonian_drop": result.initial_hamiltonian - result.final_hamiltonian,
        "mean_residual_norm": result.mean_residual_norm,
        "max_torque_nm": result.max_torque_nm,
        "slot_coverage_ratio": result.slot_coverage_ratio,
        "assigned_robots": int(np.sum(result.assignment.labels > 0)),
    }


def pose_transport_rows(result: PoseTransportResult) -> list[dict[str, Any]]:
    rows = []
    for frame in result.frames:
        rows.append(
            {
                "step": frame.step,
                "time_s": frame.time_s,
                "x_m": float(frame.q[0]),
                "y_m": float(frame.q[1]),
                "theta_rad": float(frame.q[2]),
                "theta_deg": math.degrees(float(frame.q[2])),
                "vx_m_s": float(frame.qd[0]),
                "vy_m_s": float(frame.qd[1]),
                "omega_rad_s": float(frame.qd[2]),
                "desired_fx_n": float(frame.desired_wrench[0]),
                "desired_fy_n": float(frame.desired_wrench[1]),
                "desired_tau_nm": float(frame.desired_wrench[2]),
                "achieved_fx_n": float(frame.achieved_wrench[0]),
                "achieved_fy_n": float(frame.achieved_wrench[1]),
                "achieved_tau_nm": float(frame.achieved_wrench[2]),
                "residual_norm": float(frame.residual_norm),
                "hamiltonian": float(frame.hamiltonian),
                "kinetic_energy": float(frame.kinetic_energy),
                "potential_energy": float(frame.potential_energy),
                "lambda_sum_n": float(np.sum(frame.lambdas)),
                "lambda_max_n": float(np.max(frame.lambdas)) if frame.lambdas.size else 0.0,
                "payoff_sum": float(np.sum(frame.game_payoffs)),
            }
        )
    return rows


def save_pose_transport_snapshot(problem: SP3Problem, result: PoseTransportResult, path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(7.8, 7.2))
    _draw_pose_frame(ax, problem, result, len(result.frames) - 1, title, recruit_progress=1.0)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_pose_transport_video(
    problem: SP3Problem,
    result: PoseTransportResult,
    path: Path,
    title: str,
    *,
    fps: int = 12,
    frame_stride: int = 1,
    duration_s: float = 30.0,
    final_hold_s: float = 8.0,
) -> bool:
    fig, ax = plt.subplots(figsize=(7.8, 7.2))
    stride = max(1, int(frame_stride))
    sim_indices = list(range(0, len(result.frames), stride))
    if sim_indices[-1] != len(result.frames) - 1:
        sim_indices.append(len(result.frames) - 1)
    target_motion_frames = max(2, int(round(max(duration_s - final_hold_s, 1.0) * max(fps, 1))))
    if len(sim_indices) < target_motion_frames and len(result.frames) > 1:
        sim_indices = np.linspace(0, len(result.frames) - 1, min(target_motion_frames, len(result.frames))).astype(int).tolist()
        if sim_indices[-1] != len(result.frames) - 1:
            sim_indices.append(len(result.frames) - 1)
    recruit_frames = max(8, int(round(float(result.config.recruit_fraction) * len(sim_indices))))
    hold_frames = max(0, int(round(max(final_hold_s, 0.0) * max(fps, 1))))
    total_frames = recruit_frames + len(sim_indices) + hold_frames

    def draw(frame_idx: int) -> list[object]:
        ax.clear()
        if frame_idx < recruit_frames:
            progress = frame_idx / max(recruit_frames - 1, 1)
            _draw_pose_frame(ax, problem, result, 0, f"{title} | recruitment {progress:.2f}", recruit_progress=progress)
        elif frame_idx >= recruit_frames + len(sim_indices):
            sim_idx = len(result.frames) - 1
            frame = result.frames[sim_idx]
            _draw_pose_frame(ax, problem, result, sim_idx, f"{title} | FINAL t={frame.time_s:.2f}s", recruit_progress=1.0)
        else:
            sim_idx = sim_indices[min(frame_idx - recruit_frames, len(sim_indices) - 1)]
            frame = result.frames[sim_idx]
            _draw_pose_frame(ax, problem, result, sim_idx, f"{title} | t={frame.time_s:.2f}s", recruit_progress=1.0)
        return []

    animation = FuncAnimation(fig, draw, frames=total_frames, interval=1000 / max(fps, 1), blit=False)
    try:
        animation.save(path, fps=fps, dpi=145)
        ok = True
    except Exception:
        ok = False
    finally:
        plt.close(fig)
    return ok


def _assigned_pairs(problem: SP3Problem, assignment: SP3Assignment, load_idx: int) -> list[tuple[int, int]]:
    pairs = []
    for robot_idx, label in enumerate(np.asarray(assignment.labels, dtype=int)):
        if int(label) != load_idx + 1:
            continue
        slot_idx = int(assignment.slot_labels[robot_idx]) - 1
        if 0 <= slot_idx < len(problem.load_slots[load_idx]):
            pairs.append((int(robot_idx), slot_idx))
    return pairs


def _contact_geometry(
    problem: SP3Problem,
    assignment: SP3Assignment,
    load_idx: int,
    q: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rotation = _rotation(float(q[2]))
    pairs = _assigned_pairs(problem, assignment, load_idx)
    positions = []
    directions = []
    columns = []
    force_limits = []
    for robot_idx, slot_idx in pairs:
        slot = problem.load_slots[load_idx][slot_idx]
        offset = rotation @ slot.offset_xy
        direction = rotation @ slot.direction_xy
        positions.append(q[:2] + offset)
        directions.append(direction)
        torque = float(offset[0] * direction[1] - offset[1] * direction[0])
        columns.append(np.array([direction[0], direction[1], torque], dtype=float))
        force_limits.append(float(problem.world.robots[robot_idx].spec.capacity.force_limit_n))
    if not columns:
        return np.zeros((0, 2)), np.zeros((0, 2)), np.zeros((3, 0)), np.zeros(0)
    return np.vstack(positions), np.vstack(directions), np.column_stack(columns), np.asarray(force_limits, dtype=float)


def _bounded_wrench_projection(g_matrix: np.ndarray, desired: np.ndarray, force_limits: np.ndarray, cfg: PoseTransportConfig) -> np.ndarray:
    if g_matrix.shape[1] == 0:
        return np.zeros(0, dtype=float)
    scale = np.diag([1.0 / max(cfg.force_command_limit_n, 1e-9), 1.0 / max(cfg.force_command_limit_n, 1e-9), 1.0 / max(cfg.torque_command_limit_nm, 1e-9)])
    result = lsq_linear(scale @ g_matrix, scale @ desired, bounds=(np.zeros(g_matrix.shape[1]), force_limits), lsmr_tol="auto", max_iter=100)
    return np.asarray(result.x if result.success else np.zeros(g_matrix.shape[1]), dtype=float)


def _desired_wrench(q: np.ndarray, qd: np.ndarray, target: np.ndarray, cfg: PoseTransportConfig) -> np.ndarray:
    pos_error = target[:2] - q[:2]
    theta_error = _wrap_angle(float(target[2] - q[2]))
    force = cfg.kp_pos * pos_error - cfg.kd_pos * qd[:2]
    force_norm = float(np.linalg.norm(force))
    if force_norm > cfg.force_command_limit_n:
        force = force * (cfg.force_command_limit_n / force_norm)
    tau = cfg.kp_theta * theta_error - cfg.kd_theta * float(qd[2])
    tau = float(np.clip(tau, -cfg.torque_command_limit_nm, cfg.torque_command_limit_nm))
    return np.array([force[0], force[1], tau], dtype=float)


def _normalized_residual(desired: np.ndarray, achieved: np.ndarray, cfg: PoseTransportConfig) -> float:
    error = achieved - desired
    return float(
        np.linalg.norm(
            np.array(
                [
                    error[0] / max(cfg.force_command_limit_n, 1e-9),
                    error[1] / max(cfg.force_command_limit_n, 1e-9),
                    error[2] / max(cfg.torque_command_limit_nm, 1e-9),
                ],
                dtype=float,
            )
        )
    )


def _vector_game_payoffs(g_matrix: np.ndarray, residual: np.ndarray, lambdas: np.ndarray, force_limits: np.ndarray, cfg: PoseTransportConfig) -> np.ndarray:
    if g_matrix.shape[1] == 0:
        return np.zeros(0, dtype=float)
    scaled = np.array([residual[0] / max(cfg.force_command_limit_n, 1e-9), residual[1] / max(cfg.force_command_limit_n, 1e-9), residual[2] / max(cfg.torque_command_limit_nm, 1e-9)], dtype=float)
    norm = float(np.linalg.norm(scaled))
    eta = scaled / norm if norm > 1e-12 else np.zeros(3, dtype=float)
    support = force_limits * np.maximum(0.0, eta @ g_matrix)
    effort = 0.08 * np.square(lambdas / np.maximum(force_limits, 1e-9))
    return support - effort


def _energies(q: np.ndarray, qd: np.ndarray, target: np.ndarray, m_matrix: np.ndarray, cfg: PoseTransportConfig) -> tuple[float, float, float]:
    pos_error = target[:2] - q[:2]
    theta_error = _wrap_angle(float(target[2] - q[2]))
    kinetic = 0.5 * float(qd.T @ m_matrix @ qd)
    potential = 0.5 * cfg.kp_pos * float(pos_error.T @ pos_error) + 0.5 * cfg.kp_theta * theta_error * theta_error
    return kinetic, potential, kinetic + potential


def _robot_positions_from_slots(slot_positions: np.ndarray, slot_directions: np.ndarray) -> np.ndarray:
    if slot_positions.size == 0:
        return np.zeros((0, 2), dtype=float)
    return slot_positions - 0.28 * slot_directions


def _draw_pose_frame(ax: plt.Axes, problem: SP3Problem, result: PoseTransportResult, frame_idx: int, title: str, *, recruit_progress: float) -> None:
    frame = result.frames[frame_idx]
    load = problem.world.loads[result.config.load_index]
    initial_q = result.frames[0].q
    target_q = np.array([result.config.target_xy[0], result.config.target_xy[1], result.config.target_theta_rad], dtype=float)
    half = 0.5 * problem.world.map.size_m
    pad = 1.5
    ax.set_xlim(min(-half, target_q[0] - pad), max(half, target_q[0] + pad))
    ax.set_ylim(min(-half, target_q[1] - pad), max(half, target_q[1] + pad))
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.18)
    ax.set_title(title, fontsize=9)
    _draw_payload(ax, load.length_m, load.width_m, initial_q, edge="#64748b", face="none", linestyle="--", label="initial")
    _draw_payload(ax, load.length_m, load.width_m, target_q, edge="#15803d", face="none", linestyle=":", label="target")
    _draw_payload(ax, load.length_m, load.width_m, frame.q, edge="#1f2937", face="#8ecae6", linestyle="-", label="payload")
    ax.scatter(target_q[0], target_q[1], marker="*", s=120, color="#15803d", edgecolor="black", linewidth=0.5)

    start_positions = np.vstack([robot.position for robot in problem.world.robots])
    assigned_robot_indices = [idx for idx, label in enumerate(result.assignment.labels) if int(label) == result.config.load_index + 1]
    robot_positions = frame.robot_positions
    for local_idx, robot_idx in enumerate(assigned_robot_indices[: len(robot_positions)]):
        start = start_positions[robot_idx]
        contact = robot_positions[local_idx]
        robot_xy = start + recruit_progress * (contact - start)
        ax.plot([start[0], contact[0]], [start[1], contact[1]], "--", color="#64748b", alpha=0.35)
        ax.scatter(robot_xy[0], robot_xy[1], s=62, color="#f59e0b", edgecolor="black", linewidth=0.7, zorder=4)
        lam = float(frame.lambdas[local_idx]) if local_idx < len(frame.lambdas) else 0.0
        if recruit_progress >= 0.99 and local_idx < len(frame.slot_directions):
            direction = frame.slot_directions[local_idx]
            ax.arrow(robot_xy[0], robot_xy[1], 0.018 * lam * direction[0], 0.018 * lam * direction[1], color="#b91c1c", width=0.018, head_width=0.16, alpha=0.9)
        ax.annotate(f"R{robot_idx + 1}\n{lam:.0f}N", robot_xy, xytext=(4, -15), textcoords="offset points", fontsize=6)

    for slot_idx, slot_xy in enumerate(frame.slot_positions):
        ax.scatter(slot_xy[0], slot_xy[1], marker="x", s=60, color="#1d4ed8", linewidth=1.6)

    tau = float(frame.achieved_wrench[2])
    theta = np.linspace(0.0, np.sign(tau) * 1.25 * np.pi, 48) if abs(tau) > 1e-9 else np.linspace(0.0, 0.1, 2)
    ax.plot(frame.q[0] + 0.65 * np.cos(theta), frame.q[1] + 0.65 * np.sin(theta), color="#7c2d12", linewidth=1.5)
    ax.text(
        0.02,
        0.98,
        "\n".join(
            [
                "Euler-Lagrange: M qdd + D qd = G(q) lambda",
                f"q=({frame.q[0]:.2f},{frame.q[1]:.2f},{math.degrees(frame.q[2]):.1f} deg)",
                f"target=({target_q[0]:.2f},{target_q[1]:.2f},{math.degrees(target_q[2]):.1f} deg)",
                f"tau des/ach={frame.desired_wrench[2]:.1f}/{frame.achieved_wrench[2]:.1f} Nm",
                f"H={frame.hamiltonian:.2f} | residual={frame.residual_norm:.3f}",
            ]
        ),
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=7,
        bbox={"facecolor": "white", "alpha": 0.82, "edgecolor": "#cbd5e1", "linewidth": 0.6},
    )
    ax.legend(loc="lower right", fontsize=7)


def _draw_payload(ax: plt.Axes, length: float, width: float, q: np.ndarray, *, edge: str, face: str, linestyle: str, label: str) -> None:
    corners = np.array(
        [
            [-0.5 * length, -0.5 * width],
            [0.5 * length, -0.5 * width],
            [0.5 * length, 0.5 * width],
            [-0.5 * length, 0.5 * width],
            [-0.5 * length, -0.5 * width],
        ],
        dtype=float,
    )
    rotated = corners @ _rotation(float(q[2])).T + q[:2]
    ax.fill(rotated[:, 0], rotated[:, 1], facecolor=face, edgecolor=edge, linewidth=1.8, linestyle=linestyle, alpha=0.28 if face != "none" else 1.0, label=label)
    heading = _rotation(float(q[2])) @ np.array([0.75 * length, 0.0])
    ax.arrow(q[0], q[1], heading[0] * 0.28, heading[1] * 0.28, color=edge, width=0.015, head_width=0.13, alpha=0.9)


def _rotation(theta: float) -> np.ndarray:
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=float)


def _wrap_angle(value: float) -> float:
    return (float(value) + math.pi) % (2.0 * math.pi) - math.pi

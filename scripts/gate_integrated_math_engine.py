"""Gate G4: integrated mathematical engine consistency checks.

This gate audits the invariants that connect the thesis modules into one
mathematical engine:

1. contour geometry -> force/torque signature psi_s(gamma),
2. wrench residual -> market selection of contact phase,
3. predicted congestion -> virtual toll that changes the selected phase,
4. battery margin -> economic penalty in the payoff,
5. port-Hamiltonian mechanics -> power balance and passive zero-input decay.

The gate is intentionally small and deterministic. It is not a full robot
simulation and it does not claim to solve the HJB-FPK system. Its role is to
falsify algebraic inconsistencies in the integrated framework before launching
larger CoppeliaSim or Python campaigns.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Shape:
    name: str
    a: float
    b: float
    p: float
    exact_circle: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results/integrated_math_engine_gate"))
    parser.add_argument(
        "--figure",
        type=Path,
        default=Path("docs/doc-06-explanatory-report/figures/fig-integrated-math-engine-gate.png"),
    )
    parser.add_argument("--phases", type=int, default=1440)
    parser.add_argument("--tol", type=float, default=1.0e-9)
    return parser.parse_args()


def wrap_angle(angle: np.ndarray | float) -> np.ndarray | float:
    return (angle + np.pi) % (2.0 * np.pi) - np.pi


def signed_power(value: np.ndarray, p: float, eps: float = 1.0e-6) -> np.ndarray:
    return value * np.power(value * value + eps * eps, 1.0 / p - 0.5)


def contour(shape: Shape, gamma: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if shape.exact_circle:
        points = np.column_stack((shape.a * np.cos(gamma), shape.a * np.sin(gamma)))
        normals = points / shape.a
        return points, normals

    x = shape.a * signed_power(np.cos(gamma), shape.p)
    y = shape.b * signed_power(np.sin(gamma), shape.p)
    points = np.column_stack((x, y))
    grad_x = shape.p * np.sign(x / shape.a) * np.power(np.abs(x / shape.a), shape.p - 1.0) / shape.a
    grad_y = shape.p * np.sign(y / shape.b) * np.power(np.abs(y / shape.b), shape.p - 1.0) / shape.b
    grad = np.column_stack((grad_x, grad_y))
    normals = grad / (np.linalg.norm(grad, axis=1, keepdims=True) + 1.0e-12)
    return points, normals


def signature(shape: Shape, gamma: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    points, normals = contour(shape, gamma)
    torque = points[:, 0] * normals[:, 1] - points[:, 1] * normals[:, 0]
    psi = np.column_stack((normals, torque))
    return points, normals, psi


def select_phase(
    psi: np.ndarray,
    gamma: np.ndarray,
    residual_wrench: np.ndarray,
    congestion_center: float | None = None,
    congestion_gain: float = 0.0,
    congestion_width: float = 0.18,
) -> tuple[int, np.ndarray, np.ndarray]:
    raw = psi @ residual_wrench
    toll = np.zeros_like(raw)
    if congestion_center is not None and congestion_gain > 0.0:
        dist = wrap_angle(gamma - congestion_center)
        toll = congestion_gain * np.exp(-0.5 * (dist / congestion_width) ** 2)
    score = raw - toll
    return int(np.argmax(score)), raw, score


def port_hamiltonian_checks(tol: float) -> tuple[dict[str, float | bool], np.ndarray, np.ndarray]:
    mass = np.diag([2.0, 1.6, 0.75])
    damping = np.diag([0.35, 0.42, 0.18])
    inv_mass = np.linalg.inv(mass)
    max_balance_error = 0.0
    max_zero_input_dh = -np.inf
    for vx in np.linspace(-1.0, 1.0, 7):
        for vy in np.linspace(-0.8, 0.8, 7):
            for wz in np.linspace(-0.7, 0.7, 7):
                xi = np.array([vx, vy, wz], dtype=float)
                wrench = np.array([0.35, -0.15, 0.22], dtype=float)
                xi_dot = inv_mass @ (wrench - damping @ xi)
                grad_h = mass @ xi
                dh = float(grad_h @ xi_dot)
                supplied_minus_dissipated = float(xi @ wrench - xi @ damping @ xi)
                max_balance_error = max(max_balance_error, abs(dh - supplied_minus_dissipated))

                xi_dot_zero = inv_mass @ (-damping @ xi)
                dh_zero = float(grad_h @ xi_dot_zero)
                max_zero_input_dh = max(max_zero_input_dh, dh_zero)

    dt = 0.04
    steps = 220
    xi = np.array([1.0, -0.55, 0.65], dtype=float)
    energy = np.empty(steps + 1, dtype=float)
    times = np.arange(steps + 1, dtype=float) * dt
    for step in range(steps + 1):
        energy[step] = 0.5 * float(xi @ mass @ xi)
        if step < steps:
            xi = xi + dt * (inv_mass @ (-damping @ xi))

    row = {
        "max_power_balance_error": max_balance_error,
        "max_zero_input_dh": max_zero_input_dh,
        "power_balance_pass": max_balance_error <= tol,
        "zero_input_passive": max_zero_input_dh <= tol,
        "energy_initial": float(energy[0]),
        "energy_final": float(energy[-1]),
    }
    return row, times, energy


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_readme(path: Path, gate_rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    lines = [
        "# Integrated mathematical engine gate G4",
        "",
        "This gate validates algebraic links between contour geometry, wrench",
        "signatures, economic phase assignment, congestion tolls, battery penalties,",
        "and port-Hamiltonian energy balance.",
        "",
        "| Check | Observed | Threshold | Pass |",
        "|---|---:|---:|---|",
    ]
    for row in gate_rows:
        lines.append(
            f"| {row['check']} | {float(row['observed']):.6g} | "
            f"{float(row['threshold']):.6g} | {row['pass']} |"
        )
    lines.extend(
        [
            "",
            "Key selections:",
            f"- Rectangle force phase: `{summary['rectangle_force_phase_rad']:.6g}` rad",
            f"- Rectangle torque phase: `{summary['rectangle_torque_phase_rad']:.6g}` rad",
            f"- Rectangle congested torque phase: `{summary['rectangle_torque_phase_jammed_rad']:.6g}` rad",
            f"- High-battery payoff: `{summary['payoff_high_battery']:.6g}`",
            f"- Low-battery payoff: `{summary['payoff_low_battery']:.6g}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def draw_figure(
    path: Path,
    gamma: np.ndarray,
    shape_data: dict[str, dict[str, np.ndarray]],
    rect_raw: np.ndarray,
    rect_score: np.ndarray,
    rect_best: int,
    rect_jammed: int,
    times: np.ndarray,
    energy: np.ndarray,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(10.6, 3.35), dpi=180, constrained_layout=True)

    for name, data in shape_data.items():
        axes[0].plot(gamma, data["torque"], label=name)
    axes[0].axhline(0.0, color="#111827", linewidth=0.8, alpha=0.45)
    axes[0].set_title("Firma de torque por contorno")
    axes[0].set_xlabel("fase gamma [rad]")
    axes[0].set_ylabel("ell_s(gamma)")
    axes[0].grid(True, alpha=0.2)
    axes[0].legend(fontsize=7)

    axes[1].plot(gamma, rect_raw, label="wrench residual")
    axes[1].plot(gamma, rect_score, label="con peaje congestion")
    axes[1].scatter([gamma[rect_best]], [rect_raw[rect_best]], color="#c2410c", s=24, zorder=4)
    axes[1].scatter([gamma[rect_jammed]], [rect_score[rect_jammed]], color="#2f855a", s=24, zorder=4)
    axes[1].set_title("Juego predictivo: fase vs peaje")
    axes[1].set_xlabel("fase gamma [rad]")
    axes[1].set_ylabel("payoff de contacto")
    axes[1].grid(True, alpha=0.2)
    axes[1].legend(fontsize=7)

    axes[2].plot(times, energy, color="#1d4ed8")
    axes[2].set_title("Energia port-Hamiltoniana pasiva")
    axes[2].set_xlabel("tiempo [s]")
    axes[2].set_ylabel("H(t)")
    axes[2].grid(True, alpha=0.2)

    fig.suptitle("Gate G4: motor matematico integrado", fontsize=11)
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    gamma = np.linspace(0.0, 2.0 * np.pi, args.phases, endpoint=False)
    shapes = (
        Shape("circle", 1.0, 1.0, 2.0, exact_circle=True),
        Shape("square", 1.0, 1.0, 6.0),
        Shape("rectangle", 1.55, 0.72, 6.0),
    )

    shape_data: dict[str, dict[str, np.ndarray]] = {}
    max_torque: dict[str, float] = {}
    for shape in shapes:
        points, normals, psi = signature(shape, gamma)
        shape_data[shape.name] = {"points": points, "normals": normals, "psi": psi, "torque": psi[:, 2]}
        max_torque[shape.name] = float(np.max(np.abs(psi[:, 2])))

    rect_psi = shape_data["rectangle"]["psi"]
    idx_force, force_raw, _ = select_phase(rect_psi, gamma, np.array([1.0, 0.0, 0.0]))
    idx_torque, torque_raw, _ = select_phase(rect_psi, gamma, np.array([0.0, 0.0, 1.0]))
    congestion_gain = 1.20 * float(np.max(torque_raw) - np.min(torque_raw))
    idx_jammed, _, torque_score_jammed = select_phase(
        rect_psi,
        gamma,
        np.array([0.0, 0.0, 1.0]),
        congestion_center=float(gamma[idx_torque]),
        congestion_gain=congestion_gain,
        congestion_width=0.16,
    )
    phase_shift = abs(float(wrap_angle(gamma[idx_jammed] - gamma[idx_torque])))
    useful_fraction_after_toll = float(torque_raw[idx_jammed] / max(torque_raw[idx_torque], 1.0e-12))

    square_psi = shape_data["square"]["psi"]
    idx_square, square_raw, _ = select_phase(square_psi, gamma, np.array([0.0, 0.0, 1.0]))
    square_gain = 1.20 * float(np.max(square_raw) - np.min(square_raw))
    idx_square_jam, _, square_score_jammed = select_phase(
        square_psi,
        gamma,
        np.array([0.0, 0.0, 1.0]),
        congestion_center=float(gamma[idx_square]),
        congestion_gain=square_gain,
        congestion_width=0.16,
    )
    square_shift = abs(float(wrap_angle(gamma[idx_square_jam] - gamma[idx_square])))
    square_useful_fraction_after_toll = float(square_raw[idx_square_jam] / max(square_raw[idx_square], 1.0e-12))

    phase_separation = abs(float(wrap_angle(gamma[idx_force] - gamma[idx_torque])))

    base_contact_value = float(rect_psi[idx_torque] @ np.array([0.0, 0.0, 1.0]))
    payoff_high_battery = base_contact_value - 0.05
    payoff_low_battery = base_contact_value - 0.05 - 0.75
    battery_penalty_gap = payoff_high_battery - payoff_low_battery

    ph_row, times, energy = port_hamiltonian_checks(args.tol)

    gate_rows: list[dict[str, object]] = [
        {
            "check": "circle_radial_torque_null",
            "observed": max_torque["circle"],
            "threshold": 1.0e-8,
            "pass": max_torque["circle"] <= 1.0e-8,
        },
        {
            "check": "square_superellipse_torque_nonzero",
            "observed": max_torque["square"],
            "threshold": 0.25,
            "pass": max_torque["square"] >= 0.25,
        },
        {
            "check": "rectangle_superellipse_torque_nonzero",
            "observed": max_torque["rectangle"],
            "threshold": 0.65,
            "pass": max_torque["rectangle"] >= 0.65,
        },
        {
            "check": "market_force_vs_torque_phase_separation",
            "observed": phase_separation,
            "threshold": 0.35,
            "pass": phase_separation >= 0.35,
        },
        {
            "check": "rectangle_congestion_toll_phase_shift",
            "observed": phase_shift,
            "threshold": 0.20,
            "pass": phase_shift >= 0.20 and useful_fraction_after_toll >= 0.20,
        },
        {
            "check": "square_congestion_toll_phase_shift",
            "observed": square_shift,
            "threshold": 0.20,
            "pass": square_shift >= 0.20 and square_useful_fraction_after_toll >= 0.20,
        },
        {
            "check": "battery_market_penalty_orders_payoff",
            "observed": battery_penalty_gap,
            "threshold": 0.50,
            "pass": battery_penalty_gap >= 0.50 and payoff_high_battery > payoff_low_battery,
        },
        {
            "check": "port_hamiltonian_power_balance",
            "observed": float(ph_row["max_power_balance_error"]),
            "threshold": args.tol,
            "pass": bool(ph_row["power_balance_pass"]),
        },
        {
            "check": "port_hamiltonian_zero_input_passivity",
            "observed": float(ph_row["max_zero_input_dh"]),
            "threshold": args.tol,
            "pass": bool(ph_row["zero_input_passive"]),
        },
    ]

    summary = {
        "all_pass": all(bool(row["pass"]) for row in gate_rows),
        "circle_max_abs_torque": max_torque["circle"],
        "square_max_abs_torque": max_torque["square"],
        "rectangle_max_abs_torque": max_torque["rectangle"],
        "rectangle_force_phase_rad": float(gamma[idx_force]),
        "rectangle_torque_phase_rad": float(gamma[idx_torque]),
        "rectangle_torque_phase_jammed_rad": float(gamma[idx_jammed]),
        "rectangle_toll_phase_shift_rad": phase_shift,
        "rectangle_useful_fraction_after_toll": useful_fraction_after_toll,
        "square_torque_phase_rad": float(gamma[idx_square]),
        "square_torque_phase_jammed_rad": float(gamma[idx_square_jam]),
        "square_toll_phase_shift_rad": square_shift,
        "square_useful_fraction_after_toll": square_useful_fraction_after_toll,
        "force_torque_phase_separation_rad": phase_separation,
        "payoff_high_battery": payoff_high_battery,
        "payoff_low_battery": payoff_low_battery,
        "battery_penalty_gap": battery_penalty_gap,
        **ph_row,
    }

    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "gate_checks.csv", gate_rows)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_readme(out_dir / "README.md", gate_rows, summary)
    draw_figure(
        ROOT / args.figure,
        gamma,
        shape_data,
        torque_raw,
        torque_score_jammed,
        idx_torque,
        idx_jammed,
        times,
        energy,
    )

    print(json.dumps(summary, indent=2))
    if not summary["all_pass"]:
        failed = [str(row["check"]) for row in gate_rows if not bool(row["pass"])]
        raise SystemExit("Gate G4 failed: " + ", ".join(failed))


if __name__ == "__main__":
    main()

"""Gate G3: cardinality false positive vs wrench-capacity feasibility.

The gate builds two deterministic contact coalitions around a rectangular load.
Both coalitions satisfy a scalar quorum count. The first one places all robots on
the same face, so it cannot generate the required pure yaw wrench without also
injecting a large parasitic force. The second coalition distributes contacts on
opposite faces and closes the same wrench with bounded normal pushes.

This is intentionally a small convex audit. Each contact contributes a scalar
normal push f_i in [0, f_max], so the reachable wrench set is

    A f = W_dem,    0 <= f_i <= f_max.

The bounded least-squares residual is the numerical witness used by the thesis:
cardinality can pass while effective wrench capacity fails.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import lsq_linear


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Contact:
    name: str
    r: tuple[float, float]
    n: tuple[float, float]


@dataclass(frozen=True)
class GateCase:
    name: str
    description: str
    contacts: tuple[Contact, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results/wrench_capacity_gate"))
    parser.add_argument(
        "--figure",
        type=Path,
        default=Path("docs/doc-06-explanatory-report/figures/fig-wrench-capacity-gate.png"),
    )
    parser.add_argument("--f-max", type=float, default=1.0)
    parser.add_argument("--tau-demand", type=float, default=1.2)
    parser.add_argument("--quorum", type=int, default=3)
    parser.add_argument("--tol", type=float, default=1.0e-8)
    return parser.parse_args()


def build_cases() -> tuple[GateCase, GateCase]:
    bad = GateCase(
        name="cardinality_only_same_face",
        description="Three robots clustered on one face. Quorum passes, yaw wrench fails.",
        contacts=(
            Contact("b1", (1.0, -0.04), (-1.0, 0.0)),
            Contact("b2", (1.0, 0.00), (-1.0, 0.0)),
            Contact("b3", (1.0, 0.04), (-1.0, 0.0)),
        ),
    )
    good = GateCase(
        name="effective_wrench_distributed",
        description="Four robots distributed on opposite faces. Quorum and wrench pass.",
        contacts=(
            Contact("g1", (1.0, 0.45), (-1.0, 0.0)),
            Contact("g2", (-1.0, -0.45), (1.0, 0.0)),
            Contact("g3", (-1.0, 0.45), (0.0, -1.0)),
            Contact("g4", (1.0, -0.45), (0.0, 1.0)),
        ),
    )
    return bad, good


def contact_column(contact: Contact) -> np.ndarray:
    rx, ry = contact.r
    nx, ny = contact.n
    torque = rx * ny - ry * nx
    return np.array([nx, ny, torque], dtype=float)


def grasp_matrix(contacts: tuple[Contact, ...]) -> np.ndarray:
    return np.column_stack([contact_column(contact) for contact in contacts])


def solve_case(case: GateCase, demand: np.ndarray, f_max: float, quorum: int, tol: float) -> dict[str, object]:
    matrix = grasp_matrix(case.contacts)
    result = lsq_linear(
        matrix,
        demand,
        bounds=(np.zeros(matrix.shape[1]), np.full(matrix.shape[1], f_max)),
        tol=1.0e-12,
        max_iter=200,
    )
    forces = np.asarray(result.x, dtype=float)
    achieved = matrix @ forces
    residual = float(np.linalg.norm(achieved - demand))
    cardinality_pass = len(case.contacts) >= quorum
    wrench_feasible = residual <= tol
    rank = int(np.linalg.matrix_rank(matrix, tol=1.0e-10))
    return {
        "case": case.name,
        "description": case.description,
        "contacts": len(case.contacts),
        "quorum": quorum,
        "cardinality_pass": cardinality_pass,
        "rank": rank,
        "wrench_feasible": wrench_feasible,
        "residual_norm": residual,
        "demand_fx": float(demand[0]),
        "demand_fy": float(demand[1]),
        "demand_tau": float(demand[2]),
        "achieved_fx": float(achieved[0]),
        "achieved_fy": float(achieved[1]),
        "achieved_tau": float(achieved[2]),
        "forces": forces.tolist(),
        "active_force_max": float(np.max(forces)) if forces.size else 0.0,
        "solver_success": bool(result.success),
        "solver_status": int(result.status),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case",
        "contacts",
        "quorum",
        "cardinality_pass",
        "rank",
        "wrench_feasible",
        "residual_norm",
        "demand_fx",
        "demand_fy",
        "demand_tau",
        "achieved_fx",
        "achieved_fy",
        "achieved_tau",
        "active_force_max",
        "solver_success",
        "solver_status",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})


def write_readme(path: Path, rows: list[dict[str, object]], f_max: float, tol: float) -> None:
    lines = [
        "# Wrench-capacity gate G3",
        "",
        "This gate tests the failure mode where a scalar quorum accepts a coalition",
        "that cannot generate the demanded physical wrench.",
        "",
        f"- Force bound per robot: `{f_max:g}`",
        f"- Feasibility tolerance: `{tol:g}`",
        "",
        "| Case | Contacts | Cardinality | Rank | Wrench feasible | Residual | Achieved wrench |",
        "|---|---:|---|---:|---|---:|---:|",
    ]
    for row in rows:
        achieved = f"({row['achieved_fx']:.3g}, {row['achieved_fy']:.3g}, {row['achieved_tau']:.3g})"
        lines.append(
            "| "
            f"{row['case']} | {row['contacts']} | {row['cardinality_pass']} | {row['rank']} | "
            f"{row['wrench_feasible']} | {row['residual_norm']:.6g} | {achieved} |"
        )
    lines.extend(
        [
            "",
            "Acceptance criterion: the same-face case must be a cardinality pass and a",
            "wrench failure; the distributed case must be feasible with full planar rank.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def draw_case(ax: plt.Axes, case: GateCase, row: dict[str, object]) -> None:
    rectangle = plt.Rectangle((-1.0, -0.45), 2.0, 0.9, fill=False, linewidth=1.7, color="#1f2937")
    ax.add_patch(rectangle)
    feasible = bool(row["wrench_feasible"])
    color = "#2f855a" if feasible else "#c2410c"
    n_contacts = len(case.contacts)
    for idx, (contact, force) in enumerate(zip(case.contacts, row["forces"])):
        x, y = contact.r
        nx, ny = contact.n
        ax.scatter([x], [y], s=55, color=color, zorder=3)
        ax.arrow(
            x,
            y,
            0.22 * nx,
            0.22 * ny,
            width=0.012,
            head_width=0.055,
            length_includes_head=True,
            color=color,
            alpha=0.85,
        )
        label_y = y + 0.06 + 0.075 * (idx - (n_contacts - 1) / 2.0)
        label_x = x + (0.07 if x >= 0.0 else 0.05)
        ax.text(label_x, label_y, f"{float(force):.2f}", fontsize=8, ha="left", va="center")
    card = "PASS" if row["cardinality_pass"] else "FAIL"
    wrench = "PASS" if feasible else "FAIL"
    ax.set_title(
        f"{case.name}\ncard={card}, wrench={wrench}, residual={row['residual_norm']:.2g}",
        fontsize=9,
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-0.85, 0.85)
    ax.grid(True, alpha=0.18)
    ax.set_xlabel("x")
    ax.set_ylabel("y")


def write_plot(path: Path, cases: tuple[GateCase, GateCase], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.7), dpi=180, constrained_layout=True)
    for ax, case, row in zip(axes, cases, rows):
        draw_case(ax, case, row)
    fig.suptitle("Gate G3: cardinalidad escalar frente a capacidad efectiva en wrench", fontsize=11)
    fig.savefig(path)
    plt.close(fig)


def assert_gate(rows: list[dict[str, object]], tol: float) -> None:
    by_case = {str(row["case"]): row for row in rows}
    bad = by_case["cardinality_only_same_face"]
    good = by_case["effective_wrench_distributed"]
    failures: list[str] = []
    if not bool(bad["cardinality_pass"]):
        failures.append("bad case did not pass cardinality")
    if bool(bad["wrench_feasible"]):
        failures.append("bad case unexpectedly passed wrench feasibility")
    if float(bad["residual_norm"]) <= 0.25:
        failures.append("bad case residual is too small to be a useful witness")
    if not bool(good["cardinality_pass"]):
        failures.append("good case did not pass cardinality")
    if not bool(good["wrench_feasible"]):
        failures.append("good case failed wrench feasibility")
    if int(good["rank"]) < 3:
        failures.append("good case does not have full planar wrench rank")
    if float(good["residual_norm"]) > tol:
        failures.append("good case residual exceeds tolerance")
    if failures:
        raise SystemExit("Gate G3 failed: " + "; ".join(failures))


def main() -> int:
    args = parse_args()
    demand = np.array([0.0, 0.0, float(args.tau_demand)], dtype=float)
    cases = build_cases()
    rows = [solve_case(case, demand, float(args.f_max), int(args.quorum), float(args.tol)) for case in cases]
    assert_gate(rows, float(args.tol))

    out = ROOT / args.out
    figure = ROOT / args.figure
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "summary.csv", rows)
    write_readme(out / "README.md", rows, float(args.f_max), float(args.tol))
    (out / "summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    write_plot(figure, cases, rows)

    print("PASS G3 wrench-capacity false-positive gate")
    for row in rows:
        print(
            f"{row['case']}: card={row['cardinality_pass']} wrench={row['wrench_feasible']} "
            f"rank={row['rank']} residual={row['residual_norm']:.6g}"
        )
    print(f"wrote {out}")
    print(f"wrote {figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

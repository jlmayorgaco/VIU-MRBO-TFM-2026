"""Reproducible smoke campaign for the canonical SP2 reduced models."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import yaml
from matplotlib.colors import ListedColormap

from .caging import verify_grid_caging
from .communication import (
    canonical_message_bytes,
    leader_follower_update,
    virtual_structure_update,
)
from .kinematics import (
    DifferentialDrive,
    certify_formation_twist,
    independent_speed_only_feasible,
)
from .mechanics import (
    aggregate_force_only_feasible,
    certify_planar_wrench,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _drives(config: dict[str, object]) -> list[DifferentialDrive]:
    limits = list(config["max_wheel_speed_rad_s"])
    return [
        DifferentialDrive(
            robot_id=f"r{index + 1}",
            wheel_radius_m=float(config["wheel_radius_m"]),
            track_width_m=float(config["track_width_m"]),
            max_wheel_speed_rad_s=float(limit),
        )
        for index, limit in enumerate(limits)
    ]


def _cardinal_offsets(radius: float) -> np.ndarray:
    return float(radius) * np.asarray(
        [[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]]
    )


def _run_n1(config: dict[str, object]) -> pd.DataFrame:
    drives = _drives(config)
    rows: list[dict[str, object]] = []
    speed = float(config["forward_speed_mps"])
    for radius in config["formation_radii_m"]:
        offsets = _cardinal_offsets(float(radius))
        for omega in np.linspace(
            0.0,
            float(config["max_omega_rad_s"]),
            int(config["omega_samples"]),
        ):
            twist = np.asarray([speed, 0.0, float(omega)])
            certificate = certify_formation_twist(drives, offsets, twist)
            naive = independent_speed_only_feasible(drives, offsets, twist)
            rows.append(
                {
                    "radius_m": float(radius),
                    "forward_speed_mps": speed,
                    "omega_rad_s": float(omega),
                    "curvature_per_m": float(omega / speed),
                    "joint_feasible": int(certificate.feasible),
                    "naive_feasible": int(naive),
                    "false_feasible": int(naive and not certificate.feasible),
                    "limiting_robot": certificate.limiting_robot_id,
                    "max_wheel_utilization": certificate.max_utilization,
                    "certificate_reason": certificate.reason,
                }
            )
    return pd.DataFrame(rows)


def _run_n2(config: dict[str, object]) -> tuple[pd.DataFrame, pd.DataFrame]:
    force_limits = np.asarray(config["force_limits_n"], dtype=float)
    analytic_scenarios = [
        (
            "balanced_force",
            _cardinal_offsets(0.45),
            np.asarray([12.0, 0.0, 0.0]),
        ),
        (
            "balanced_moment",
            _cardinal_offsets(0.45),
            np.asarray([0.0, 0.0, 6.0]),
        ),
        (
            "coincident_moment_counterexample",
            np.zeros((4, 2)),
            np.asarray([0.0, 0.0, 2.0]),
        ),
    ]
    analytic_rows: list[dict[str, object]] = []
    for scenario, offsets, wrench in analytic_scenarios:
        certificate = certify_planar_wrench(offsets, force_limits, wrench)
        analytic_rows.append(
            {
                "scenario": scenario,
                "oracle_feasible": int(certificate.feasible),
                "aggregate_feasible": int(
                    aggregate_force_only_feasible(force_limits, wrench)
                ),
                "false_feasible": int(
                    aggregate_force_only_feasible(force_limits, wrench)
                    and not certificate.feasible
                ),
                "utilization": certificate.utilization,
                "residual_norm": certificate.residual_norm,
                "status": certificate.status,
            }
        )

    phase_rows: list[dict[str, object]] = []
    for dispersion in config["dispersion_m"]:
        for pressure in config["pressure_levels"]:
            for seed in config["seeds"]:
                rng = np.random.default_rng(int(seed))
                angles = np.linspace(0.0, 2.0 * np.pi, 4, endpoint=False)
                angles += rng.normal(0.0, 0.035, size=4)
                radii = float(dispersion) * rng.uniform(0.9, 1.1, size=4)
                offsets = np.column_stack((radii * np.cos(angles), radii * np.sin(angles)))
                wrench = np.asarray(
                    [
                        float(pressure) * 16.0,
                        0.0,
                        float(pressure) * 6.0,
                    ]
                )
                certificate = certify_planar_wrench(offsets, force_limits, wrench)
                phase_rows.append(
                    {
                        "dispersion_m": float(dispersion),
                        "pressure": float(pressure),
                        "seed": int(seed),
                        "feasible": int(certificate.feasible),
                        "utilization": certificate.utilization,
                        "residual_norm": certificate.residual_norm,
                    }
                )
    return pd.DataFrame(analytic_rows), pd.DataFrame(phase_rows)


def _run_n3(config: dict[str, object]) -> pd.DataFrame:
    robots = int(config["robots"])
    updates = int(config["updates"])
    rows: list[dict[str, object]] = []
    for sequence in range(updates):
        leader = leader_follower_update(
            coalition_id="coalition-17",
            membership_version=3,
            sequence=sequence,
            pose=[1.2, -0.4, 0.3],
            twist=[0.22, 0.0, 0.08],
        )
        leader_bytes = canonical_message_bytes(leader)
        rows.append(
            {
                "architecture": "leader_follower",
                "sequence": sequence,
                "messages": robots - 1,
                "bytes": (robots - 1) * leader_bytes,
                "bytes_per_message": leader_bytes,
            }
        )
        virtual_total = 0
        for robot in range(robots):
            message = virtual_structure_update(
                coalition_id="coalition-17",
                membership_version=3,
                sequence=sequence,
                robot_id=f"r{robot + 1}",
                pose_estimate=[1.2, -0.4, 0.3],
                twist_estimate=[0.22, 0.0, 0.08],
                covariance_diagonal=[0.0025, 0.0025, 0.0004],
            )
            virtual_total += 2 * canonical_message_bytes(message)
        rows.append(
            {
                "architecture": "virtual_structure",
                "sequence": sequence,
                "messages": 2 * robots,
                "bytes": virtual_total,
                "bytes_per_message": virtual_total / (2 * robots),
            }
        )
    return pd.DataFrame(rows)


def _run_caging(config: dict[str, object]) -> pd.DataFrame:
    size = int(config["grid_size"])
    center = (size // 2, size // 2)
    closed = np.zeros((size, size), dtype=bool)
    closed[1:-1, 1:-1] = True
    open_grid = closed.copy()
    open_grid[0, center[1]] = True
    results = [
        (
            "closed_ring",
            verify_grid_caging(
                closed,
                center,
                resolution_label=str(config["resolution_label"]),
            ),
        ),
        (
            "one_cell_gap",
            verify_grid_caging(
                open_grid,
                center,
                resolution_label=str(config["resolution_label"]),
            ),
        ),
    ]
    return pd.DataFrame(
        [
            {
                "scenario": scenario,
                "status": result.status,
                "escape_found": int(result.escape_found),
                "visited_cells": result.visited_cells,
                "path_length": len(result.path),
                "resolution_label": result.resolution_label,
            }
            for scenario, result in results
        ]
    )


def _plot_n1(frame: pd.DataFrame, path: Path) -> None:
    summary_rows = []
    for radius, group in frame.groupby("radius_m"):
        joint = group.loc[group["joint_feasible"] == 1, "omega_rad_s"]
        naive = group.loc[group["naive_feasible"] == 1, "omega_rad_s"]
        summary_rows.append(
            {
                "radius_m": radius,
                "joint": float(joint.max()) if len(joint) else 0.0,
                "naive": float(naive.max()) if len(naive) else 0.0,
            }
        )
    summary = pd.DataFrame(summary_rows)
    fig, ax = plt.subplots(figsize=(7.3, 4.25))
    ax.plot(
        summary["radius_m"],
        summary["joint"],
        "o-",
        label="Comprobación conjunta",
    )
    ax.plot(
        summary["radius_m"],
        summary["naive"],
        "s--",
        label="Seguimiento independiente",
    )
    ax.fill_between(
        summary["radius_m"],
        summary["joint"],
        summary["naive"],
        color="#E07A24",
        alpha=0.16,
        label="Aceptado solo por el comparador",
    )
    ax.set_xlabel("Radio máximo de la formación [m]")
    ax.set_ylabel("Velocidad angular máxima [rad/s]")
    ax.grid(alpha=0.22)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _plot_n2(frame: pd.DataFrame, path: Path) -> None:
    phase = frame.pivot_table(
        index="dispersion_m",
        columns="pressure",
        values="feasible",
        aggfunc="mean",
    )
    feasible_counts = frame.pivot_table(
        index="dispersion_m",
        columns="pressure",
        values="feasible",
        aggfunc="sum",
    )
    sample_counts = frame.pivot_table(
        index="dispersion_m",
        columns="pressure",
        values="feasible",
        aggfunc="count",
    )
    fig, ax = plt.subplots(figsize=(7.3, 4.25))
    image = ax.imshow(
        phase.to_numpy(),
        origin="lower",
        aspect="auto",
        vmin=0.0,
        vmax=1.0,
        cmap=ListedColormap(["#B54A3A", "#E07A24"]),
        interpolation="nearest",
    )
    for row in range(phase.shape[0]):
        for column in range(phase.shape[1]):
            accepted = int(feasible_counts.iloc[row, column])
            total = int(sample_counts.iloc[row, column])
            color = "white" if phase.iloc[row, column] < 0.5 else "#222222"
            ax.text(
                column,
                row,
                f"{accepted}/{total}",
                ha="center",
                va="center",
                fontsize=8.5,
                color=color,
            )
    ax.set_xticks(
        range(len(phase.columns)),
        [f"{value:.1f}".replace(".", ",") for value in phase.columns],
    )
    ax.set_yticks(
        range(len(phase.index)),
        [f"{value:.2f}".replace(".", ",") for value in phase.index],
    )
    ax.set_xlabel(r"Escala de demanda $\pi$")
    ax.set_ylabel("Dispersión radial [m]")
    colorbar = fig.colorbar(image, ax=ax, ticks=[0.0, 1.0])
    colorbar.ax.set_yticklabels(["inviable", "viable"])
    colorbar.set_label("Casos admisibles")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _plot_n3(frame: pd.DataFrame, path: Path) -> None:
    totals = frame.groupby("architecture", as_index=False)[["messages", "bytes"]].sum()
    labels = ["Líder-seguidor", "Estructura virtual"]
    order = ["leader_follower", "virtual_structure"]
    totals = totals.set_index("architecture").loc[order]
    fig, axes = plt.subplots(1, 2, figsize=(7.3, 3.55))
    colors = ["#353535", "#E07A24"]
    axes[0].bar(labels, totals["messages"], color=colors)
    axes[0].set_ylabel("Mensajes protocolarios")
    axes[1].bar(labels, totals["bytes"] / 1000.0, color=colors)
    axes[1].set_ylabel("Datos serializados [kB]")
    for ax in axes:
        ax.tick_params(axis="x", rotation=12)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _tex_number(value: float, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}".replace(".", r"{,}")


def _tex_scientific(value: float, digits: int = 2) -> str:
    if value == 0.0:
        return "0"
    exponent = int(np.floor(np.log10(abs(value))))
    mantissa = value / (10.0**exponent)
    return rf"{_tex_number(mantissa, digits)}\times 10^{{{exponent}}}"


def _write_metrics(
    path: Path,
    n1: pd.DataFrame,
    n2_analytic: pd.DataFrame,
    n2_phase: pd.DataFrame,
    n3: pd.DataFrame,
    caging: pd.DataFrame,
) -> dict[str, object]:
    n1_limits = (
        n1.loc[n1["joint_feasible"] == 1]
        .groupby("radius_m")["omega_rad_s"]
        .max()
    )
    n3_totals = n3.groupby("architecture")[["messages", "bytes"]].sum()
    finite_residuals = n2_phase.loc[
        np.isfinite(n2_phase["residual_norm"]), "residual_norm"
    ]
    metrics: dict[str, object] = {
        "n1_rows": len(n1),
        "n1_false_feasible": int(n1["false_feasible"].sum()),
        "n1_min_radius_omega": float(n1_limits.iloc[0]),
        "n1_max_radius_omega": float(n1_limits.iloc[-1]),
        "n2_counterexamples": int(n2_analytic["false_feasible"].sum()),
        "n2_phase_rows": len(n2_phase),
        "n2_feasible_rows": int(n2_phase["feasible"].sum()),
        "n2_infeasible_rows": int((1 - n2_phase["feasible"]).sum()),
        "n2_max_finite_residual": (
            float(finite_residuals.max()) if len(finite_residuals) else 0.0
        ),
        "n3_leader_messages": int(n3_totals.loc["leader_follower", "messages"]),
        "n3_virtual_messages": int(n3_totals.loc["virtual_structure", "messages"]),
        "n3_leader_bytes": int(n3_totals.loc["leader_follower", "bytes"]),
        "n3_virtual_bytes": int(n3_totals.loc["virtual_structure", "bytes"]),
        "caging_closed_status": str(
            caging.set_index("scenario").loc["closed_ring", "status"]
        ),
        "caging_gap_status": str(
            caging.set_index("scenario").loc["one_cell_gap", "status"]
        ),
    }
    macros = {
        "SPTwoNOneRows": str(metrics["n1_rows"]),
        "SPTwoNOneFalse": str(metrics["n1_false_feasible"]),
        "SPTwoNOneSmallOmega": _tex_number(metrics["n1_min_radius_omega"], 2),
        "SPTwoNOneLargeOmega": _tex_number(metrics["n1_max_radius_omega"], 2),
        "SPTwoNTwoCounterexamples": str(metrics["n2_counterexamples"]),
        "SPTwoNTwoRows": str(metrics["n2_phase_rows"]),
        "SPTwoNTwoFeasible": str(metrics["n2_feasible_rows"]),
        "SPTwoNTwoInfeasible": str(metrics["n2_infeasible_rows"]),
        "SPTwoNTwoResidual": _tex_scientific(
            float(metrics["n2_max_finite_residual"]), 2
        ),
        "SPTwoNThreeLeaderMessages": str(metrics["n3_leader_messages"]),
        "SPTwoNThreeVirtualMessages": str(metrics["n3_virtual_messages"]),
        "SPTwoNThreeLeaderBytes": str(metrics["n3_leader_bytes"]),
        "SPTwoNThreeVirtualBytes": str(metrics["n3_virtual_bytes"]),
        "SPTwoCagingClosed": "sin escape a la resolución fijada",
        "SPTwoCagingGap": "escape encontrado",
    }
    path.write_text(
        "\n".join(
            f"\\newcommand{{\\{name}}}{{{value}}}" for name, value in macros.items()
        )
        + "\n",
        encoding="utf-8",
    )
    return metrics


def run_sp2_canonical_config(config_path: Path) -> dict[str, object]:
    """Execute the canonical smoke campaign and return its manifest."""

    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    output = Path(config["output_dir"])
    raw = output / "raw"
    figures = output / "figures"
    generated = output / "generated"
    for directory in (raw, figures, generated):
        directory.mkdir(parents=True, exist_ok=True)

    n1 = _run_n1(config["n1"])
    n2_analytic, n2_phase = _run_n2(config["n2"])
    n3 = _run_n3(config["n3"])
    caging = _run_caging(config["sp2e"])
    n1.to_csv(raw / "n1_kinematic_envelope.csv", index=False)
    n2_analytic.to_csv(raw / "n2_analytic_cases.csv", index=False)
    n2_phase.to_csv(raw / "n2_pressure_dispersion.csv", index=False)
    n3.to_csv(raw / "n3_communication.csv", index=False)
    caging.to_csv(raw / "sp2e_caging.csv", index=False)
    _plot_n1(n1, figures / "n1_kinematic_envelope.pdf")
    _plot_n2(n2_phase, figures / "n2_pressure_dispersion.pdf")
    _plot_n3(n3, figures / "n3_communication_cost.pdf")
    metrics = _write_metrics(
        generated / "metrics.tex",
        n1,
        n2_analytic,
        n2_phase,
        n3,
        caging,
    )
    _write_json(generated / "key_metrics.json", metrics)

    checks = {
        "n1_detects_false_feasible": int(metrics["n1_false_feasible"]) > 0,
        "n1_radius_contracts_envelope": (
            float(metrics["n1_max_radius_omega"])
            <= float(metrics["n1_min_radius_omega"])
        ),
        "n2_detects_moment_counterexample": int(metrics["n2_counterexamples"]) >= 1,
        "n2_wrench_identity": float(metrics["n2_max_finite_residual"]) <= 1e-7,
        "n3_virtual_costs_more_messages": (
            int(metrics["n3_virtual_messages"]) > int(metrics["n3_leader_messages"])
        ),
        "n3_virtual_costs_more_bytes": (
            int(metrics["n3_virtual_bytes"]) > int(metrics["n3_leader_bytes"])
        ),
        "sp2e_closed_has_no_grid_escape": (
            metrics["caging_closed_status"] == "no_escape_at_resolution"
        ),
        "sp2e_gap_exposes_escape": metrics["caging_gap_status"] == "escape_found",
    }
    audit = {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "evidence_level": "implementation_smoke",
        "mechanical_scope": "planar bilateral forces with component-wise bounds",
        "caging_scope": "four-connected finite grid at declared resolution",
        "physical_validation_completed": False,
        "confirmatory_statistics_completed": False,
    }
    _write_json(output / "audit.json", audit)
    if audit["status"] != "passed":
        raise AssertionError(f"SP2 smoke audit failed: {checks}")

    environment = {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "platform": platform.platform(),
    }
    _write_json(output / "environment.json", environment)
    artifacts = sorted(
        path
        for path in output.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    manifest: dict[str, object] = {
        "experiment_id": config["experiment_id"],
        "status": "complete",
        "config": str(config_path).replace("\\", "/"),
        "evidence_level": "implementation_smoke",
        "artifacts": {
            str(path.relative_to(output)).replace("\\", "/"): {
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in artifacts
        },
    }
    _write_json(output / "manifest.json", manifest)
    return manifest


__all__ = ["run_sp2_canonical_config"]

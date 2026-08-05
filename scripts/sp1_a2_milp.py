from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter
from numpy.typing import NDArray
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


def _load_hungarian_module() -> Any:
    """Carga el generador/base real sin duplicar su implementación."""
    module_name = "sp1_a1_hungarian_for_milp_comparison"
    if module_name in sys.modules:
        return sys.modules[module_name]
    path = Path(__file__).with_name("sp1_a1_hungarian.py")
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"No se pudo cargar el baseline Hungarian: {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


HUNGARIAN = _load_hungarian_module()


# ========================================================
# === M0 Classes and Properties ==========================
# ========================================================


@dataclass(frozen=True)
class PositionedEntity:
    id: str
    x: float
    y: float

    @property
    def position(self) -> FloatArray:
        return np.array([self.x, self.y], dtype=np.float64)


@dataclass(frozen=True)
class Robot(PositionedEntity):
    capacity: float
    battery: float = 100.0
    responding: bool = True


@dataclass(frozen=True)
class Load(PositionedEntity):
    mass: float


@dataclass(frozen=True)
class Assignment:
    robot_id: str
    load_id: str
    capacity: float
    distance: float


@dataclass(frozen=True)
class SolverTimings:
    matrix_wall_ns: int
    model_wall_ns: int
    solver_wall_ns: int
    post_wall_ns: int
    total_wall_ns: int
    total_cpu_ns: int


@dataclass(frozen=True)
class MILPResult:
    assignments: list[Assignment]
    coalitions: dict[str, list[str]]
    idle_robots: list[str]
    recruited_capacity: dict[str, float]
    excess_capacity: dict[str, float]
    total_distance: float
    total_excess: float
    objective_value: float
    distance_matrix: FloatArray
    feasible: bool
    optimal: bool
    status: int
    message: str
    mip_gap: float | None
    mip_node_count: int | None
    timings: SolverTimings
    diagnostics: dict[str, Any]


@dataclass(frozen=True)
class MonteCarloConfig:
    q_bar: float
    workspace_width: float
    workspace_height: float
    mean_quota: float
    base_seed: int
    seeds_per_cell: int
    scaling_m_values: tuple[int, ...]
    scaling_deltas: tuple[float, ...]
    balance_m_values: tuple[int, ...]
    balance_deltas: tuple[float, ...]
    asymmetry_m_values: tuple[int, ...]
    asymmetry_delta: float
    quota_modes: tuple[str, ...]
    spatial_modes: tuple[str, ...]
    failure_m_values: tuple[int, ...]
    failure_deltas: tuple[float, ...]
    failure_treatments: tuple[str, ...]
    capacity_modes: tuple[str, ...]
    default_capacity_mode: str
    max_retries: int
    time_limit_seconds: float
    mip_rel_gap: float
    distance_weight: float
    excess_weight: float
    robot_use_weight: float


@dataclass(frozen=True)
class SaturationAuditConfig:
    fixed_demand_m: int = 120
    fixed_demand_n_values: tuple[int, ...] = (
        120,
        160,
        220,
        300,
        400,
        550,
        750,
        1000,
        1400,
        1900,
        2600,
        3500,
        4800,
    )
    joint_m_values: tuple[int, ...] = (
        40,
        60,
        90,
        130,
        190,
        280,
        420,
        620,
        900,
        1200,
    )
    joint_delta: float = 0.20
    timeout_probe_n_values: tuple[int, ...] = (400, 800, 1600, 3200)
    timeout_probe_seconds: tuple[float, ...] = (2.0, 5.0, 20.0)
    replicates: int = 3
    main_timeout_seconds: float = 5.0
    q_bar: float = 5.0
    mean_quota: float = 3.0
    workspace_width: float = 100.0
    workspace_height: float = 100.0
    base_seed: int = 20260729
    quota_mode: str = "moderate"
    spatial_mode: str = "uniform"
    capacity_mode: str = "moderate"
    mip_rel_gap: float = 0.0
    distance_weight: float = 1.0
    excess_weight: float = 0.25
    robot_use_weight: float = 1e-3


class InfeasibleCoalitionError(RuntimeError):
    """Raised when no assignment can satisfy all mandatory loads."""


# ===============================================================
# == Model utilities ============================================
# ===============================================================


def validate_scenario(
    robots: list[Robot],
    loads: list[Load],
    compatibility: NDArray[np.bool_] | None = None,
) -> None:
    if not robots:
        raise ValueError("Debe existir al menos un robot.")
    if not loads:
        raise ValueError("Debe existir al menos una carga.")

    robot_ids = [robot.id for robot in robots]
    load_ids = [load.id for load in loads]
    if len(robot_ids) != len(set(robot_ids)):
        raise ValueError("Los identificadores de robot deben ser únicos.")
    if len(load_ids) != len(set(load_ids)):
        raise ValueError("Los identificadores de carga deben ser únicos.")

    for robot in robots:
        if robot.capacity <= 0:
            raise ValueError(f"La capacidad de {robot.id} debe ser positiva.")
        if not np.isfinite(robot.capacity):
            raise ValueError(f"La capacidad de {robot.id} debe ser finita.")

    for load in loads:
        if load.mass <= 0:
            raise ValueError(f"La masa de {load.id} debe ser positiva.")
        if not np.isfinite(load.mass):
            raise ValueError(f"La masa de {load.id} debe ser finita.")

    if compatibility is not None:
        expected_shape = (len(robots), len(loads))
        if compatibility.shape != expected_shape:
            raise ValueError(
                "compatibility debe tener shape "
                f"{expected_shape}, no {compatibility.shape}."
            )

    # Condición necesaria rápida. No reemplaza la prueba exacta del MILP.
    total_capacity = sum(robot.capacity for robot in robots)
    total_demand = sum(load.mass for load in loads)
    if total_capacity + 1e-12 < total_demand:
        raise InfeasibleCoalitionError(
            "Capacidad total insuficiente para cargas obligatorias: "
            f"capacidad={total_capacity:.3f}, demanda={total_demand:.3f}."
        )


def build_distance_matrix(
    robots: list[Robot],
    loads: list[Load],
    external_cost_matrix: FloatArray | None = None,
) -> FloatArray:
    """Builds C[i,k], Euclidean by default or externally supplied."""
    if external_cost_matrix is not None:
        matrix = np.asarray(external_cost_matrix, dtype=np.float64)
        expected_shape = (len(robots), len(loads))
        if matrix.shape != expected_shape:
            raise ValueError(
                f"external_cost_matrix debe tener shape {expected_shape}."
            )
        if not np.all(np.isfinite(matrix)) or np.any(matrix < 0):
            raise ValueError("La matriz externa debe ser finita y no negativa.")
        return matrix.copy()

    robot_positions = np.array(
        [[robot.x, robot.y] for robot in robots], dtype=np.float64
    )
    load_positions = np.array(
        [[load.x, load.y] for load in loads], dtype=np.float64
    )
    differences = (
        robot_positions[:, np.newaxis, :]
        - load_positions[np.newaxis, :, :]
    )
    return np.linalg.norm(differences, axis=2)


def _y_index(robot_index: int, load_index: int, load_count: int) -> int:
    return robot_index * load_count + load_index


def _e_index(load_index: int, robot_count: int, load_count: int) -> int:
    return robot_count * load_count + load_index


# ===============================================================
# == MILP solver ================================================
# ===============================================================


def solve_heterogeneous_milp(
    robots: list[Robot],
    loads: list[Load],
    *,
    compatibility: NDArray[np.bool_] | None = None,
    external_cost_matrix: FloatArray | None = None,
    distance_weight: float = 1.0,
    excess_weight: float = 0.25,
    robot_use_weight: float = 1e-3,
    time_limit_seconds: float | None = None,
    mip_rel_gap: float = 0.0,
) -> MILPResult:
    """
    Exact centralized oracle for heterogeneous robot coalitions.

    Variables:
        y[i,k] in {0,1}: robot i is assigned to load k.
        e[k] >= 0: excess capacity on load k.

    Objective:
        min distance_weight * sum(d[i,k] y[i,k])
          + excess_weight * sum(e[k])
          + robot_use_weight * sum(y[i,k])

    Constraints:
        sum_k y[i,k] <= 1                           for each robot i
        sum_i q[i] y[i,k] >= mass[k]                for each load k
        sum_i q[i] y[i,k] - e[k] <= mass[k]         for each load k
        y[i,k] = 0 on incompatible pairs
    """
    total_wall_start = time.perf_counter_ns()
    total_cpu_start = time.process_time_ns()

    if distance_weight < 0 or excess_weight < 0 or robot_use_weight < 0:
        raise ValueError("Los pesos del objetivo deben ser no negativos.")
    if mip_rel_gap < 0:
        raise ValueError("mip_rel_gap debe ser no negativo.")

    validate_scenario(robots, loads, compatibility)

    robot_count = len(robots)
    load_count = len(loads)
    y_count = robot_count * load_count
    variable_count = y_count + load_count

    phase_start = time.perf_counter_ns()
    distance_matrix = build_distance_matrix(
        robots=robots,
        loads=loads,
        external_cost_matrix=external_cost_matrix,
    )
    matrix_wall_ns = time.perf_counter_ns() - phase_start

    phase_start = time.perf_counter_ns()

    # Objective coefficients.
    c = np.zeros(variable_count, dtype=np.float64)
    for i in range(robot_count):
        for k in range(load_count):
            c[_y_index(i, k, load_count)] = (
                distance_weight * distance_matrix[i, k]
                + robot_use_weight
            )
    for k in range(load_count):
        c[_e_index(k, robot_count, load_count)] = excess_weight

    # Bounds and integrality.
    lower_bounds = np.zeros(variable_count, dtype=np.float64)
    upper_bounds = np.full(variable_count, np.inf, dtype=np.float64)
    upper_bounds[:y_count] = 1.0

    if compatibility is not None:
        compatibility_array = np.asarray(compatibility, dtype=bool)
        for i in range(robot_count):
            for k in range(load_count):
                if not compatibility_array[i, k]:
                    upper_bounds[_y_index(i, k, load_count)] = 0.0

    integrality = np.zeros(variable_count, dtype=np.int32)
    integrality[:y_count] = 1

    row_indices: list[int] = []
    column_indices: list[int] = []
    coefficients: list[float] = []
    lower: list[float] = []
    upper: list[float] = []
    row_count = 0

    # Each robot serves at most one load.
    for i in range(robot_count):
        for k in range(load_count):
            row_indices.append(row_count)
            column_indices.append(_y_index(i, k, load_count))
            coefficients.append(1.0)
        lower.append(-np.inf)
        upper.append(1.0)
        row_count += 1

    # Each mandatory load receives enough heterogeneous capacity.
    for k, load in enumerate(loads):
        for i, robot in enumerate(robots):
            row_indices.append(row_count)
            column_indices.append(_y_index(i, k, load_count))
            coefficients.append(robot.capacity)
        lower.append(load.mass)
        upper.append(np.inf)
        row_count += 1

    # e[k] >= recruited_capacity[k] - mass[k].
    for k, load in enumerate(loads):
        for i, robot in enumerate(robots):
            row_indices.append(row_count)
            column_indices.append(_y_index(i, k, load_count))
            coefficients.append(robot.capacity)
        row_indices.append(row_count)
        column_indices.append(_e_index(k, robot_count, load_count))
        coefficients.append(-1.0)
        lower.append(-np.inf)
        upper.append(load.mass)
        row_count += 1

    matrix = coo_matrix(
        (
            np.asarray(coefficients, dtype=np.float64),
            (
                np.asarray(row_indices, dtype=np.int64),
                np.asarray(column_indices, dtype=np.int64),
            ),
        ),
        shape=(row_count, variable_count),
    ).tocsr()
    constraints = LinearConstraint(
        matrix,
        lb=np.asarray(lower, dtype=np.float64),
        ub=np.asarray(upper, dtype=np.float64),
    )
    bounds = Bounds(lb=lower_bounds, ub=upper_bounds)
    model_wall_ns = time.perf_counter_ns() - phase_start

    options: dict[str, Any] = {
        "disp": False,
        "presolve": True,
        "mip_rel_gap": mip_rel_gap,
    }
    if time_limit_seconds is not None:
        if time_limit_seconds <= 0:
            raise ValueError("time_limit_seconds debe ser positivo.")
        options["time_limit"] = time_limit_seconds

    phase_start = time.perf_counter_ns()
    optimization = milp(
        c=c,
        integrality=integrality,
        bounds=bounds,
        constraints=constraints,
        options=options,
    )
    solver_wall_ns = time.perf_counter_ns() - phase_start

    if optimization.x is None:
        raise InfeasibleCoalitionError(
            "El MILP no encontró una coalición factible. "
            f"status={optimization.status}; message={optimization.message}"
        )

    phase_start = time.perf_counter_ns()
    vector = np.asarray(optimization.x, dtype=np.float64)
    y_solution = vector[:y_count].reshape(robot_count, load_count)
    y_binary = y_solution >= 0.5

    assignments: list[Assignment] = []
    coalitions: dict[str, list[str]] = {load.id: [] for load in loads}
    assigned_robot_indices: set[int] = set()
    recruited_capacity: dict[str, float] = {load.id: 0.0 for load in loads}
    total_distance = 0.0

    for i, robot in enumerate(robots):
        selected_loads = np.flatnonzero(y_binary[i])
        if len(selected_loads) > 1:
            raise RuntimeError(
                f"La solución numérica asignó {robot.id} a más de una carga."
            )
        if len(selected_loads) == 0:
            continue

        k = int(selected_loads[0])
        load = loads[k]
        distance = float(distance_matrix[i, k])
        assignments.append(
            Assignment(
                robot_id=robot.id,
                load_id=load.id,
                capacity=robot.capacity,
                distance=distance,
            )
        )
        coalitions[load.id].append(robot.id)
        recruited_capacity[load.id] += robot.capacity
        assigned_robot_indices.add(i)
        total_distance += distance

    idle_robots = [
        robot.id
        for i, robot in enumerate(robots)
        if i not in assigned_robot_indices
    ]
    excess_capacity = {
        load.id: recruited_capacity[load.id] - load.mass
        for load in loads
    }
    total_excess = float(sum(excess_capacity.values()))

    feasible = all(
        recruited_capacity[load.id] + 1e-8 >= load.mass
        for load in loads
    )
    optimal = optimization.status == 0 and bool(optimization.success)

    post_wall_ns = time.perf_counter_ns() - phase_start
    total_wall_ns = time.perf_counter_ns() - total_wall_start
    total_cpu_ns = time.process_time_ns() - total_cpu_start

    objective_value = (
        distance_weight * total_distance
        + excess_weight * total_excess
        + robot_use_weight * len(assignments)
    )

    return MILPResult(
        assignments=assignments,
        coalitions=coalitions,
        idle_robots=idle_robots,
        recruited_capacity=recruited_capacity,
        excess_capacity=excess_capacity,
        total_distance=total_distance,
        total_excess=total_excess,
        objective_value=objective_value,
        distance_matrix=distance_matrix,
        feasible=feasible,
        optimal=optimal,
        status=int(optimization.status),
        message=str(optimization.message),
        mip_gap=(
            float(optimization.mip_gap)
            if getattr(optimization, "mip_gap", None) is not None
            else None
        ),
        mip_node_count=(
            int(optimization.mip_node_count)
            if getattr(optimization, "mip_node_count", None) is not None
            else None
        ),
        timings=SolverTimings(
            matrix_wall_ns=matrix_wall_ns,
            model_wall_ns=model_wall_ns,
            solver_wall_ns=solver_wall_ns,
            post_wall_ns=post_wall_ns,
            total_wall_ns=total_wall_ns,
            total_cpu_ns=total_cpu_ns,
        ),
        diagnostics={
            "robot_count": robot_count,
            "load_count": load_count,
            "binary_variable_count": y_count,
            "continuous_variable_count": load_count,
            "constraint_count": row_count,
            "constraint_nonzero_count": int(matrix.nnz),
            "constraint_matrix_bytes": int(
                matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes
            ),
            "distance_weight": distance_weight,
            "excess_weight": excess_weight,
            "robot_use_weight": robot_use_weight,
            "solver_fun": float(optimization.fun),
        },
    )


def validate_result(
    result: MILPResult,
    robots: list[Robot],
    loads: list[Load],
    compatibility: NDArray[np.bool_] | None = None,
) -> None:
    if not result.feasible:
        raise RuntimeError("La solución no cubre todas las cargas.")

    robot_by_id = {robot.id: robot for robot in robots}
    load_index = {load.id: k for k, load in enumerate(loads)}

    assigned_ids = [assignment.robot_id for assignment in result.assignments]
    if len(assigned_ids) != len(set(assigned_ids)):
        raise RuntimeError("Un robot fue asignado a más de una carga.")

    for assignment in result.assignments:
        if assignment.robot_id not in robot_by_id:
            raise RuntimeError("Aparece un robot desconocido.")
        if assignment.load_id not in load_index:
            raise RuntimeError("Aparece una carga desconocida.")
        if compatibility is not None:
            i = next(
                index
                for index, robot in enumerate(robots)
                if robot.id == assignment.robot_id
            )
            k = load_index[assignment.load_id]
            if not bool(compatibility[i, k]):
                raise RuntimeError("Se seleccionó una pareja incompatible.")

    for load in loads:
        recruited = result.recruited_capacity[load.id]
        if recruited + 1e-8 < load.mass:
            raise RuntimeError(
                f"{load.id} recibió {recruited}, pero exige {load.mass}."
            )
        expected_excess = recruited - load.mass
        if not np.isclose(result.excess_capacity[load.id], expected_excess):
            raise RuntimeError("Exceso de capacidad incoherente.")

    all_robot_ids = {robot.id for robot in robots}
    classified = set(assigned_ids) | set(result.idle_robots)
    if classified != all_robot_ids:
        raise RuntimeError("Hay robots sin clasificar o clasificados dos veces.")


# ===============================================================
# == Printing and plotting ======================================
# ===============================================================


def print_result(result: MILPResult) -> None:
    print("\n" + "=" * 72)
    print("SP1.A2 — RESULTADO MILP HETEROGÉNEO")
    print("=" * 72)

    print("\nAsignaciones:")
    for assignment in result.assignments:
        print(
            f"  {assignment.robot_id:>2} -> {assignment.load_id:<2} | "
            f"q={assignment.capacity:>5.2f} kg | "
            f"d={assignment.distance:>6.3f} m"
        )

    print("\nCoaliciones:")
    for load_id, robot_ids in result.coalitions.items():
        print(
            f"  {load_id}: {robot_ids} | "
            f"capacidad={result.recruited_capacity[load_id]:.2f} kg | "
            f"exceso={result.excess_capacity[load_id]:.2f} kg"
        )

    print(f"\nRobots libres: {result.idle_robots}")
    print(f"Factible: {result.feasible}")
    print(f"Óptimo certificado: {result.optimal}")
    print(f"Distancia total: {result.total_distance:.6f} m")
    print(f"Exceso total: {result.total_excess:.6f} kg")
    print(f"Objetivo: {result.objective_value:.6f}")
    print(f"MIP gap: {result.mip_gap}")
    print(f"Nodos B&B: {result.mip_node_count}")
    print(f"Estado: {result.status} — {result.message}")


def print_distance_matrix(
    robots: list[Robot],
    loads: list[Load],
    result: MILPResult,
) -> None:
    print("\nMATRIZ ROBOT–CARGA [m]")
    print("-" * 72)
    header = "Robot".ljust(10)
    for load in loads:
        header += load.id.rjust(14)
    print(header)
    for i, robot in enumerate(robots):
        row = f"{robot.id}(q={robot.capacity:g})".ljust(10)
        for k in range(len(loads)):
            row += f"{result.distance_matrix[i, k]:.3f}".rjust(14)
        print(row)


def plot_milp_assignment(
    robots: list[Robot],
    loads: list[Load],
    result: MILPResult,
    output_path: str | Path | None = "sp1_a2_milp.png",
    show: bool = True,
) -> None:
    figure, axis = plt.subplots(figsize=(12, 9))

    axis.scatter(
        [robot.x for robot in robots],
        [robot.y for robot in robots],
        marker="o",
        s=75,
        color="tab:blue",
        label="Robots",
        zorder=3,
    )
    axis.scatter(
        [load.x for load in loads],
        [load.y for load in loads],
        marker="X",
        s=180,
        color="tab:orange",
        label="Loads",
        zorder=4,
    )

    robot_by_id = {robot.id: robot for robot in robots}
    load_by_id = {load.id: load for load in loads}
    color_map = plt.get_cmap("tab10")
    load_color = {
        load.id: color_map(index % 10)
        for index, load in enumerate(loads)
    }

    for assignment in result.assignments:
        robot = robot_by_id[assignment.robot_id]
        load = load_by_id[assignment.load_id]
        axis.plot(
            [robot.x, load.x],
            [robot.y, load.y],
            linestyle="--",
            linewidth=1.8,
            color=load_color[load.id],
            zorder=2,
        )

    idle_set = set(result.idle_robots)
    for robot in robots:
        suffix = "\nidle" if robot.id in idle_set else ""
        axis.annotate(
            f"{robot.id}\nq={robot.capacity:g} kg{suffix}",
            xy=(robot.x, robot.y),
            xytext=(0, 9),
            textcoords="offset points",
            fontsize=10.5,
            ha="left",
            va="center",
            zorder=5,
        )

    for load in loads:
        recruited = result.recruited_capacity[load.id]
        axis.annotate(
            f"{load.id}\nm={load.mass:g} kg\nQ={recruited:g} kg",
            xy=(load.x, load.y),
            xytext=(2, 19),
            textcoords="offset points",
            fontsize=11,
            ha="left",
            va="center",
            zorder=5,
        )

    axis.set_title(
        "SP1.A2 — Heterogeneous coalition assignment by MILP",
        fontsize=16,
        pad=10,
    )
    axis.set_xlabel("x [m]", fontsize=13)
    axis.set_ylabel("y [m]", fontsize=13)
    axis.grid(visible=True, linewidth=0.8, alpha=0.30)
    axis.legend(loc="upper left", fontsize=12, frameon=True)
    axis.set_xlim(-0.45, 9.45)
    axis.set_ylim(-0.40, 6.40)
    axis.set_aspect("equal", adjustable="box")
    figure.tight_layout()

    if output_path is not None:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output, dpi=180, bbox_inches="tight")
        print(f"\nFigura guardada en: {output}")

    if show:
        plt.show()
    else:
        plt.close(figure)


# ===============================================================
# == Paired heterogeneous Monte Carlo worlds ====================
# ===============================================================


CAPACITY_MODE_SIGMA = {
    "homogeneous": 0.0,
    "low": 0.15,
    "moderate": 0.35,
    "high": 0.65,
    "extreme": 1.00,
}


def stable_seed(base_seed: int, *parts: object) -> int:
    return int(HUNGARIAN.stable_seed(base_seed, *parts))


def robot_count_from_delta(total_slots: int, delta: float) -> int:
    return int(HUNGARIAN.robot_count_from_delta(total_slots, delta))


def balance_delta(robot_count: int, slot_count: int) -> float:
    return float(HUNGARIAN.balance_delta(robot_count, slot_count))


def coefficient_of_variation(values: Sequence[float] | FloatArray) -> float:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0:
        return math.nan
    mean = float(np.mean(array))
    if mean == 0.0:
        return 0.0
    return float(np.std(array, ddof=0) / mean)


def generate_capacity_vector(
    *,
    robot_count: int,
    q_bar: float,
    mode: str,
    rng: np.random.Generator,
) -> FloatArray:
    """
    Genera capacidades positivas con suma exactamente N*q_bar.

    La normalización separa heterogeneidad de capacidad total disponible.
    """
    if robot_count <= 0:
        raise ValueError("robot_count debe ser positivo.")
    if q_bar <= 0.0:
        raise ValueError("q_bar debe ser positivo.")
    if mode not in CAPACITY_MODE_SIGMA:
        raise ValueError(f"Modo de capacidad desconocido: {mode}")
    sigma = CAPACITY_MODE_SIGMA[mode]
    if sigma == 0.0:
        return np.full(robot_count, q_bar, dtype=np.float64)

    raw = rng.lognormal(mean=0.0, sigma=sigma, size=robot_count)
    capacities = raw * (robot_count * q_bar / float(np.sum(raw)))
    capacities *= robot_count * q_bar / float(np.sum(capacities))
    if not np.all(np.isfinite(capacities)) or np.any(capacities <= 0.0):
        raise RuntimeError("Se generó una capacidad inválida.")
    return capacities.astype(np.float64)


def generate_paired_world(
    *,
    robot_count: int,
    total_slots: int,
    q_bar: float,
    mean_quota: float,
    quota_mode: str,
    spatial_mode: str,
    capacity_mode: str,
    workspace_width: float,
    workspace_height: float,
    seed: int,
) -> tuple[list[Robot], list[Load], IntArray]:
    homogeneous_robots, homogeneous_loads, quotas = HUNGARIAN.generate_world(
        robot_count=robot_count,
        total_slots=total_slots,
        q_bar=q_bar,
        mean_quota=mean_quota,
        quota_mode=quota_mode,
        spatial_mode=spatial_mode,
        workspace_width=workspace_width,
        workspace_height=workspace_height,
        seed=seed,
    )
    capacity_rng = np.random.default_rng(
        stable_seed(seed, "milp-capacities", capacity_mode)
    )
    capacities = generate_capacity_vector(
        robot_count=robot_count,
        q_bar=q_bar,
        mode=capacity_mode,
        rng=capacity_rng,
    )
    robots = [
        Robot(
            id=robot.id,
            x=robot.x,
            y=robot.y,
            capacity=float(capacities[index]),
            battery=robot.battery,
            responding=robot.responding,
        )
        for index, robot in enumerate(homogeneous_robots)
    ]
    loads = [
        Load(id=load.id, x=load.x, y=load.y, mass=load.mass)
        for load in homogeneous_loads
    ]
    if int(np.sum(quotas)) != total_slots:
        raise RuntimeError("Las cuotas pareadas no suman M.")
    if not np.isclose(
        sum(robot.capacity for robot in robots),
        robot_count * q_bar,
        rtol=0.0,
        atol=1e-9,
    ):
        raise RuntimeError("La capacidad total no conserva N*q_bar.")
    return robots, loads, np.asarray(quotas, dtype=np.int64)


def _hungarian_entities(
    robots: list[Robot],
    loads: list[Load],
    q_bar: float,
) -> tuple[list[Any], list[Any]]:
    homogeneous_robots = [
        HUNGARIAN.Robot(
            id=robot.id,
            x=robot.x,
            y=robot.y,
            capacity=q_bar,
            battery=robot.battery,
            responding=robot.responding,
        )
        for robot in robots
    ]
    homogeneous_loads = [
        HUNGARIAN.Load(id=load.id, x=load.x, y=load.y, mass=load.mass)
        for load in loads
    ]
    return homogeneous_robots, homogeneous_loads


def _quantile(values: Sequence[float], probability: float) -> float:
    array = np.asarray(values, dtype=np.float64)
    return (
        float(np.quantile(array, probability))
        if array.size
        else math.nan
    )


def _assignment_map(result: MILPResult) -> dict[str, str | None]:
    mapping = {assignment.robot_id: assignment.load_id for assignment in result.assignments}
    mapping.update({robot_id: None for robot_id in result.idle_robots})
    return mapping


def changed_assignment_fraction(
    base_assignment: dict[str, str | None] | None,
    new_result: MILPResult | None,
    surviving_robot_ids: set[str],
) -> float:
    if base_assignment is None or new_result is None:
        return math.nan
    new_assignment = _assignment_map(new_result)
    common = sorted(surviving_robot_ids & set(base_assignment) & set(new_assignment))
    if not common:
        return 0.0
    changed = sum(
        base_assignment[robot_id] != new_assignment[robot_id]
        for robot_id in common
    )
    return changed / len(common)


def estimate_centralized_communication(
    *,
    original_robots: list[Robot],
    active_robots: list[Robot],
    assigned_count: int,
    failed_count: int,
    max_retries: int,
) -> tuple[int, int, int]:
    """
    Modelo contable del oráculo: uplink de estado y downlink de decisión.

    No se interpreta como comunicación distribuida.
    """
    state_bytes = sum(
        len(
            json.dumps(
                {
                    "id": robot.id,
                    "x": robot.x,
                    "y": robot.y,
                    "capacity": robot.capacity,
                    "battery": robot.battery,
                },
                separators=(",", ":"),
            ).encode("utf-8")
        )
        for robot in active_robots
    )
    decision_bytes = assigned_count * len(
        b'{"robot_id":"R0000","load_id":"L0000"}'
    )
    retry_messages = max_retries * failed_count
    retry_bytes = retry_messages * len(b'{"retry":"R0000"}')
    logical_messages = len(active_robots) + assigned_count + retry_messages
    communication_bytes = state_bytes + decision_bytes + retry_bytes
    return logical_messages, communication_bytes, retry_messages


def solve_paired_case(
    *,
    study: str,
    seed: int,
    robots: list[Robot],
    loads: list[Load],
    quotas: IntArray,
    config: MonteCarloConfig,
    quota_mode: str,
    spatial_mode: str,
    capacity_mode: str,
    requested_delta: float,
    treatment: str = "none",
    original_robots: list[Robot] | None = None,
    failure_count: int = 0,
    failed_robot_was_assigned: bool = False,
    base_milp_result: MILPResult | None = None,
    base_assignment: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    homogeneous_robots, homogeneous_loads = _hungarian_entities(
        robots,
        loads,
        config.q_bar,
    )
    hungarian_result = HUNGARIAN.solve_hungarian(
        robots=homogeneous_robots,
        loads=homogeneous_loads,
        q_bar=config.q_bar,
        allow_partial=True,
    )

    milp_result: MILPResult | None = None
    milp_error = ""
    try:
        milp_result = solve_heterogeneous_milp(
            robots=robots,
            loads=loads,
            distance_weight=config.distance_weight,
            excess_weight=config.excess_weight,
            robot_use_weight=config.robot_use_weight,
            time_limit_seconds=config.time_limit_seconds,
            mip_rel_gap=config.mip_rel_gap,
        )
        validate_result(milp_result, robots, loads)
    except InfeasibleCoalitionError as error:
        milp_error = str(error)

    original = original_robots if original_robots is not None else robots
    total_capacity = float(sum(robot.capacity for robot in robots))
    total_demand = float(sum(load.mass for load in loads))
    workspace_diagonal = math.hypot(
        config.workspace_width,
        config.workspace_height,
    )
    capacities = np.asarray(
        [robot.capacity for robot in robots],
        dtype=np.float64,
    )
    nominal_slot_count = int(np.sum(quotas))

    hungarian_costs = [
        assignment.cost for assignment in hungarian_result.assignments
    ]
    hungarian_mean = (
        hungarian_result.total_cost / len(hungarian_costs)
        if hungarian_costs
        else math.nan
    )
    hungarian_p95 = _quantile(hungarian_costs, 0.95)

    if milp_result is not None:
        milp_distances = [
            assignment.distance for assignment in milp_result.assignments
        ]
        distances_by_load: dict[str, list[float]] = defaultdict(list)
        for assignment in milp_result.assignments:
            distances_by_load[assignment.load_id].append(assignment.distance)
        load_mean_distances = np.asarray(
            [
                float(np.mean(distances))
                for distances in distances_by_load.values()
            ],
            dtype=np.float64,
        )
        milp_assigned_count = len(milp_result.assignments)
        milp_mean = (
            milp_result.total_distance / milp_assigned_count
            if milp_assigned_count
            else math.nan
        )
        milp_p95 = _quantile(milp_distances, 0.95)
        milp_feasible = milp_result.feasible
        relative_distance_increase = (
            (milp_result.total_distance - base_milp_result.total_distance)
            / base_milp_result.total_distance
            if base_milp_result is not None
            and base_milp_result.total_distance > 0.0
            and milp_result.feasible
            else math.nan
        )
        churn = changed_assignment_fraction(
            base_assignment,
            milp_result,
            {robot.id for robot in robots},
        )
    else:
        milp_distances = []
        load_mean_distances = np.asarray([], dtype=np.float64)
        milp_assigned_count = 0
        milp_mean = math.nan
        milp_p95 = math.nan
        milp_feasible = False
        relative_distance_increase = math.nan
        churn = math.nan

    logical_messages, communication_bytes, retry_messages = (
        estimate_centralized_communication(
            original_robots=original,
            active_robots=robots,
            assigned_count=milp_assigned_count,
            failed_count=failure_count,
            max_retries=config.max_retries,
        )
    )
    both_feasible = bool(milp_feasible and hungarian_result.feasible)
    distance_ratio = (
        milp_result.total_distance / hungarian_result.total_cost
        if both_feasible
        and milp_result is not None
        and hungarian_result.total_cost > 0.0
        else math.nan
    )
    solver_ratio = (
        milp_result.timings.solver_wall_ns
        / hungarian_result.timings.solver_wall_ns
        if milp_result is not None
        and hungarian_result.timings.solver_wall_ns > 0
        else math.nan
    )
    capacity_delta = (
        (total_capacity - total_demand) / (total_capacity + total_demand)
        if total_capacity + total_demand > 0.0
        else math.nan
    )

    record: dict[str, Any] = {
        "study": study,
        "seed": seed,
        "N": len(robots),
        "N_original": len(original),
        "K": len(loads),
        "M": nominal_slot_count,
        "size_N_plus_M": len(robots) + nominal_slot_count,
        "matrix_elements": len(robots) * len(loads),
        "rho_M_over_N": (
            nominal_slot_count / len(robots) if robots else math.nan
        ),
        "requested_delta": requested_delta,
        "observed_delta": balance_delta(len(robots), nominal_slot_count),
        "capacity_delta": capacity_delta,
        "quota_mode": quota_mode,
        "spatial_mode": spatial_mode,
        "capacity_mode": capacity_mode,
        "treatment": treatment,
        "failure_count": failure_count,
        "failed_robot_was_assigned": failed_robot_was_assigned,
        "total_capacity_kg": total_capacity,
        "total_demand_kg": total_demand,
        "capacity_mean_kg": (
            float(np.mean(capacities)) if capacities.size else math.nan
        ),
        "capacity_std_kg": (
            float(np.std(capacities)) if capacities.size else math.nan
        ),
        "capacity_cv": coefficient_of_variation(capacities),
        "capacity_min_kg": (
            float(np.min(capacities)) if capacities.size else math.nan
        ),
        "capacity_max_kg": (
            float(np.max(capacities)) if capacities.size else math.nan
        ),
        "quota_cv": coefficient_of_variation(quotas),
        "quota_asymmetry_cv": coefficient_of_variation(quotas),
        "distance_matrix_asymmetry_cv": (
            coefficient_of_variation(milp_result.distance_matrix.ravel())
            if milp_result is not None
            else math.nan
        ),
        "structurally_feasible": total_capacity + 1e-12 >= total_demand,
        "milp_feasible": milp_feasible,
        "mission_feasible": milp_feasible,
        "milp_complete_load_fraction": 1.0 if milp_feasible else 0.0,
        "milp_missing_load_count": 0 if milp_feasible else len(loads),
        "milp_optimal": (
            milp_result.optimal if milp_result is not None else False
        ),
        "milp_status": (
            milp_result.status if milp_result is not None else -1
        ),
        "milp_message": (
            milp_result.message if milp_result is not None else milp_error
        ),
        "milp_mip_gap": (
            milp_result.mip_gap
            if milp_result is not None and milp_result.mip_gap is not None
            else math.nan
        ),
        "milp_node_count": (
            milp_result.mip_node_count
            if milp_result is not None
            and milp_result.mip_node_count is not None
            else 0
        ),
        "milp_assigned_robot_count": milp_assigned_count,
        "milp_idle_robot_count": (
            len(milp_result.idle_robots)
            if milp_result is not None
            else len(robots)
        ),
        "milp_robot_utilization": (
            milp_assigned_count / len(robots) if robots else math.nan
        ),
        "milp_idle_fraction": (
            (len(robots) - milp_assigned_count) / len(robots)
            if robots
            else math.nan
        ),
        "milp_total_distance": (
            milp_result.total_distance
            if milp_result is not None
            else math.nan
        ),
        "milp_mean_distance_per_assigned_robot": milp_mean,
        "milp_normalized_mean_distance_per_assigned_robot": (
            milp_mean / workspace_diagonal
            if np.isfinite(milp_mean) and workspace_diagonal > 0.0
            else math.nan
        ),
        "milp_distance_per_nominal_slot": (
            milp_result.total_distance / nominal_slot_count
            if milp_result is not None and nominal_slot_count > 0
            else math.nan
        ),
        "milp_normalized_distance_p95": (
            milp_p95 / workspace_diagonal
            if np.isfinite(milp_p95) and workspace_diagonal > 0.0
            else math.nan
        ),
        "milp_assignment_distance_p50": _quantile(milp_distances, 0.50),
        "milp_assignment_distance_p95": milp_p95,
        "milp_assignment_distance_max": (
            float(np.max(milp_distances)) if milp_distances else math.nan
        ),
        "milp_assignment_distance_std": (
            float(np.std(milp_distances)) if milp_distances else math.nan
        ),
        "milp_assignment_distance_cv": coefficient_of_variation(milp_distances),
        "milp_assignment_distance_gini": (
            float(HUNGARIAN.gini_coefficient(milp_distances))
            if milp_distances
            else math.nan
        ),
        "milp_assignment_distance_jain": (
            float(HUNGARIAN.jain_index(milp_distances))
            if milp_distances
            else math.nan
        ),
        "milp_normalized_assignment_distance_max": (
            float(np.max(milp_distances)) / workspace_diagonal
            if milp_distances and workspace_diagonal > 0.0
            else math.nan
        ),
        "milp_load_mean_distance_cv": coefficient_of_variation(
            load_mean_distances
        ),
        "milp_total_excess_kg": (
            milp_result.total_excess
            if milp_result is not None
            else math.nan
        ),
        "milp_objective_value": (
            milp_result.objective_value
            if milp_result is not None
            else math.nan
        ),
        "milp_matrix_bytes": (
            int(milp_result.distance_matrix.nbytes)
            + int(milp_result.diagnostics["constraint_matrix_bytes"])
            if milp_result is not None
            else 0
        ),
        "milp_binary_variable_count": (
            int(milp_result.diagnostics["binary_variable_count"])
            if milp_result is not None
            else len(robots) * len(loads)
        ),
        "milp_constraint_count": (
            int(milp_result.diagnostics["constraint_count"])
            if milp_result is not None
            else len(robots) + 2 * len(loads)
        ),
        "milp_solver_wall_ns": (
            milp_result.timings.solver_wall_ns
            if milp_result is not None
            else math.nan
        ),
        "milp_total_wall_ns": (
            milp_result.timings.total_wall_ns
            if milp_result is not None
            else math.nan
        ),
        "milp_total_cpu_ns": (
            milp_result.timings.total_cpu_ns
            if milp_result is not None
            else math.nan
        ),
        "milp_matrix_wall_ns": (
            milp_result.timings.matrix_wall_ns
            if milp_result is not None
            else math.nan
        ),
        "milp_model_wall_ns": (
            milp_result.timings.model_wall_ns
            if milp_result is not None
            else math.nan
        ),
        "milp_post_wall_ns": (
            milp_result.timings.post_wall_ns
            if milp_result is not None
            else math.nan
        ),
        "milp_solver_ns_per_binary_variable": (
            milp_result.timings.solver_wall_ns
            / int(milp_result.diagnostics["binary_variable_count"])
            if milp_result is not None
            and int(milp_result.diagnostics["binary_variable_count"]) > 0
            else math.nan
        ),
        "hungarian_feasible": hungarian_result.feasible,
        "hungarian_coverage": hungarian_result.coverage,
        "hungarian_assigned_robot_count": len(hungarian_result.assignments),
        "hungarian_total_distance": hungarian_result.total_cost,
        "hungarian_mean_distance_per_slot": hungarian_mean,
        "hungarian_normalized_distance_p95": (
            hungarian_p95 / workspace_diagonal
            if np.isfinite(hungarian_p95) and workspace_diagonal > 0.0
            else math.nan
        ),
        "hungarian_solver_wall_ns": hungarian_result.timings.solver_wall_ns,
        "hungarian_total_wall_ns": hungarian_result.timings.total_wall_ns,
        "hungarian_matrix_bytes": int(hungarian_result.cost_matrix.nbytes),
        "both_feasible": both_feasible,
        "same_capacity_model": capacity_mode == "homogeneous",
        "milp_to_hungarian_distance_ratio": distance_ratio,
        "milp_minus_hungarian_assigned_robots": (
            milp_assigned_count - len(hungarian_result.assignments)
            if milp_result is not None
            else math.nan
        ),
        "milp_to_hungarian_solver_ratio": solver_ratio,
        "base_milp_total_distance": (
            base_milp_result.total_distance
            if base_milp_result is not None
            else math.nan
        ),
        "relative_distance_increase": relative_distance_increase,
        "assignment_churn": churn,
        "failure_rate": (
            failure_count / len(original) if original else 0.0
        ),
        "recovery_feasible": milp_feasible,
        "central_logical_messages": logical_messages,
        "central_communication_bytes": communication_bytes,
        "central_communication_rounds": 2,
        "retry_messages": retry_messages,
        "nonresponding_count": failure_count,
    }
    return record


def select_failed_robot_ids(
    *,
    treatment: str,
    robots: list[Robot],
    base_result: MILPResult | None,
    rng: np.random.Generator,
) -> set[str] | None:
    if treatment == "no_failure":
        return set()
    all_ids = [robot.id for robot in robots]
    if treatment == "idle_robot_failure":
        if base_result is None or not base_result.idle_robots:
            return None
        return {str(rng.choice(base_result.idle_robots))}
    if treatment == "random_assigned_failure":
        if base_result is None or not base_result.assignments:
            return None
        ids = [assignment.robot_id for assignment in base_result.assignments]
        return {str(rng.choice(ids))}
    if treatment == "critical_assigned_failure":
        if base_result is None or not base_result.assignments:
            return None
        critical = max(
            base_result.assignments,
            key=lambda item: (
                item.capacity,
                item.distance,
                item.robot_id,
            ),
        )
        return {critical.robot_id}
    if treatment.startswith("random_") and treatment.endswith("_percent"):
        rate = float(treatment.removeprefix("random_").removesuffix("_percent")) / 100.0
        count = max(1, int(round(rate * len(robots))))
        selected = rng.choice(all_ids, size=min(count, len(all_ids)), replace=False)
        return {str(value) for value in selected.tolist()}
    raise ValueError(f"Tratamiento desconocido: {treatment}")


# ===============================================================
# == Monte Carlo campaigns ======================================
# ===============================================================


def run_scaling_study(config: MonteCarloConfig) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    total_cells = len(config.scaling_m_values) * len(config.scaling_deltas)
    cell = 0
    for total_slots in config.scaling_m_values:
        for requested_delta in config.scaling_deltas:
            cell += 1
            robot_count = robot_count_from_delta(total_slots, requested_delta)
            print(
                f"[MILP scaling {cell}/{total_cells}] "
                f"M={total_slots}, N={robot_count}, delta={requested_delta:+.2f}"
            )
            for replicate in range(config.seeds_per_cell):
                seed = stable_seed(
                    config.base_seed,
                    "scaling",
                    total_slots,
                    requested_delta,
                    replicate,
                )
                robots, loads, quotas = generate_paired_world(
                    robot_count=robot_count,
                    total_slots=total_slots,
                    q_bar=config.q_bar,
                    mean_quota=config.mean_quota,
                    quota_mode="symmetric",
                    spatial_mode="uniform",
                    capacity_mode=config.default_capacity_mode,
                    workspace_width=config.workspace_width,
                    workspace_height=config.workspace_height,
                    seed=seed,
                )
                records.append(
                    solve_paired_case(
                        study="scaling",
                        seed=seed,
                        robots=robots,
                        loads=loads,
                        quotas=quotas,
                        config=config,
                        quota_mode="symmetric",
                        spatial_mode="uniform",
                        capacity_mode=config.default_capacity_mode,
                        requested_delta=requested_delta,
                    )
                )
    return records


def run_balance_study(config: MonteCarloConfig) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    total_cells = len(config.balance_m_values) * len(config.balance_deltas)
    cell = 0
    for total_slots in config.balance_m_values:
        for requested_delta in config.balance_deltas:
            cell += 1
            robot_count = robot_count_from_delta(total_slots, requested_delta)
            print(
                f"[MILP balance {cell}/{total_cells}] "
                f"M={total_slots}, N={robot_count}, delta={requested_delta:+.2f}"
            )
            for replicate in range(config.seeds_per_cell):
                seed = stable_seed(
                    config.base_seed,
                    "balance",
                    total_slots,
                    requested_delta,
                    replicate,
                )
                robots, loads, quotas = generate_paired_world(
                    robot_count=robot_count,
                    total_slots=total_slots,
                    q_bar=config.q_bar,
                    mean_quota=config.mean_quota,
                    quota_mode="symmetric",
                    spatial_mode="uniform",
                    capacity_mode=config.default_capacity_mode,
                    workspace_width=config.workspace_width,
                    workspace_height=config.workspace_height,
                    seed=seed,
                )
                records.append(
                    solve_paired_case(
                        study="balance",
                        seed=seed,
                        robots=robots,
                        loads=loads,
                        quotas=quotas,
                        config=config,
                        quota_mode="symmetric",
                        spatial_mode="uniform",
                        capacity_mode=config.default_capacity_mode,
                        requested_delta=requested_delta,
                    )
                )
    return records


def run_asymmetry_study(config: MonteCarloConfig) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    total_cells = (
        len(config.asymmetry_m_values)
        * len(config.quota_modes)
        * len(config.spatial_modes)
    )
    cell = 0
    for total_slots in config.asymmetry_m_values:
        robot_count = robot_count_from_delta(
            total_slots,
            config.asymmetry_delta,
        )
        for quota_mode in config.quota_modes:
            for spatial_mode in config.spatial_modes:
                cell += 1
                print(
                    f"[MILP asymmetry {cell}/{total_cells}] M={total_slots}, "
                    f"N={robot_count}, quota={quota_mode}, spatial={spatial_mode}"
                )
                for replicate in range(config.seeds_per_cell):
                    seed = stable_seed(
                        config.base_seed,
                        "asymmetry",
                        total_slots,
                        quota_mode,
                        spatial_mode,
                        replicate,
                    )
                    robots, loads, quotas = generate_paired_world(
                        robot_count=robot_count,
                        total_slots=total_slots,
                        q_bar=config.q_bar,
                        mean_quota=config.mean_quota,
                        quota_mode=quota_mode,
                        spatial_mode=spatial_mode,
                        capacity_mode=config.default_capacity_mode,
                        workspace_width=config.workspace_width,
                        workspace_height=config.workspace_height,
                        seed=seed,
                    )
                    records.append(
                        solve_paired_case(
                            study="asymmetry",
                            seed=seed,
                            robots=robots,
                            loads=loads,
                            quotas=quotas,
                            config=config,
                            quota_mode=quota_mode,
                            spatial_mode=spatial_mode,
                            capacity_mode=config.default_capacity_mode,
                            requested_delta=config.asymmetry_delta,
                        )
                    )
    return records


def run_capacity_study(config: MonteCarloConfig) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    total_cells = len(config.asymmetry_m_values) * len(config.capacity_modes)
    cell = 0
    for total_slots in config.asymmetry_m_values:
        robot_count = robot_count_from_delta(
            total_slots,
            config.asymmetry_delta,
        )
        for capacity_mode in config.capacity_modes:
            cell += 1
            print(
                f"[MILP capacity {cell}/{total_cells}] M={total_slots}, "
                f"N={robot_count}, capacity={capacity_mode}"
            )
            for replicate in range(config.seeds_per_cell):
                seed = stable_seed(
                    config.base_seed,
                    "capacity",
                    total_slots,
                    capacity_mode,
                    replicate,
                )
                robots, loads, quotas = generate_paired_world(
                    robot_count=robot_count,
                    total_slots=total_slots,
                    q_bar=config.q_bar,
                    mean_quota=config.mean_quota,
                    quota_mode="moderate",
                    spatial_mode="uniform",
                    capacity_mode=capacity_mode,
                    workspace_width=config.workspace_width,
                    workspace_height=config.workspace_height,
                    seed=seed,
                )
                records.append(
                    solve_paired_case(
                        study="capacity",
                        seed=seed,
                        robots=robots,
                        loads=loads,
                        quotas=quotas,
                        config=config,
                        quota_mode="moderate",
                        spatial_mode="uniform",
                        capacity_mode=capacity_mode,
                        requested_delta=config.asymmetry_delta,
                    )
                )
    return records


def run_failure_study(config: MonteCarloConfig) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    total_cells = len(config.failure_m_values) * len(config.failure_deltas)
    cell = 0
    for total_slots in config.failure_m_values:
        for requested_delta in config.failure_deltas:
            cell += 1
            robot_count = robot_count_from_delta(total_slots, requested_delta)
            print(
                f"[MILP failures {cell}/{total_cells}] "
                f"M={total_slots}, N={robot_count}, delta={requested_delta:+.2f}"
            )
            for replicate in range(config.seeds_per_cell):
                world_seed = stable_seed(
                    config.base_seed,
                    "failures_world",
                    total_slots,
                    requested_delta,
                    replicate,
                )
                robots, loads, quotas = generate_paired_world(
                    robot_count=robot_count,
                    total_slots=total_slots,
                    q_bar=config.q_bar,
                    mean_quota=config.mean_quota,
                    quota_mode="moderate",
                    spatial_mode="uniform",
                    capacity_mode=config.default_capacity_mode,
                    workspace_width=config.workspace_width,
                    workspace_height=config.workspace_height,
                    seed=world_seed,
                )
                base_result: MILPResult | None = None
                try:
                    base_result = solve_heterogeneous_milp(
                        robots,
                        loads,
                        distance_weight=config.distance_weight,
                        excess_weight=config.excess_weight,
                        robot_use_weight=config.robot_use_weight,
                        time_limit_seconds=config.time_limit_seconds,
                        mip_rel_gap=config.mip_rel_gap,
                    )
                    validate_result(base_result, robots, loads)
                except InfeasibleCoalitionError:
                    base_result = None
                base_assignment = (
                    _assignment_map(base_result)
                    if base_result is not None
                    else None
                )
                base_assigned = (
                    {assignment.robot_id for assignment in base_result.assignments}
                    if base_result is not None
                    else set()
                )

                for treatment in config.failure_treatments:
                    treatment_seed = stable_seed(
                        config.base_seed,
                        "failure_treatment",
                        world_seed,
                        treatment,
                    )
                    failed_ids = select_failed_robot_ids(
                        treatment=treatment,
                        robots=robots,
                        base_result=base_result,
                        rng=np.random.default_rng(treatment_seed),
                    )
                    if failed_ids is None:
                        continue
                    active = [
                        robot for robot in robots if robot.id not in failed_ids
                    ]
                    records.append(
                        solve_paired_case(
                            study="failures",
                            seed=treatment_seed,
                            robots=active,
                            loads=loads,
                            quotas=quotas,
                            config=config,
                            quota_mode="moderate",
                            spatial_mode="uniform",
                            capacity_mode=config.default_capacity_mode,
                            requested_delta=requested_delta,
                            treatment=treatment,
                            original_robots=robots,
                            failure_count=len(failed_ids),
                            failed_robot_was_assigned=any(
                                robot_id in base_assigned
                                for robot_id in failed_ids
                            ),
                            base_milp_result=base_result,
                            base_assignment=base_assignment,
                        )
                    )
    return records


# ===============================================================
# == CSV, summaries, plots and report ============================
# ===============================================================


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        raise ValueError(f"No hay registros para escribir en {path}.")
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def parse_csv_value(value: str) -> Any:
    stripped = value.strip()
    if stripped == "True":
        return True
    if stripped == "False":
        return False
    if stripped.lower() in {"nan", "inf", "-inf"}:
        return float(stripped)
    try:
        integer = int(stripped)
        if str(integer) == stripped:
            return integer
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        return value


def read_csv_records(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as file:
        return [
            {key: parse_csv_value(value) for key, value in row.items()}
            for row in csv.DictReader(file)
        ]


def _finite(records: Iterable[dict[str, Any]], field: str) -> FloatArray:
    values: list[float] = []
    for record in records:
        try:
            value = float(record[field])
        except (KeyError, TypeError, ValueError):
            continue
        if np.isfinite(value):
            values.append(value)
    return np.asarray(values, dtype=np.float64)


def _save_figure(figure: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def _series_plot(
    *,
    records: list[dict[str, Any]],
    x_field: str,
    y_fields: tuple[tuple[str, str], ...],
    output_path: Path,
    title: str,
    xlabel: str,
    ylabel: str,
    log_x: bool = False,
    log_y: bool = False,
) -> None:
    figure, axis = plt.subplots(figsize=(10, 6))
    x_values = sorted({float(record[x_field]) for record in records})
    for field, label in y_fields:
        medians: list[float] = []
        lower: list[float] = []
        upper: list[float] = []
        retained_x: list[float] = []
        for x_value in x_values:
            selected = [
                record
                for record in records
                if float(record[x_field]) == x_value
            ]
            values = _finite(selected, field)
            if values.size == 0:
                continue
            retained_x.append(x_value)
            medians.append(float(np.median(values)))
            lower.append(float(np.quantile(values, 0.05)))
            upper.append(float(np.quantile(values, 0.95)))
        axis.plot(retained_x, medians, marker="o", label=label)
        axis.fill_between(retained_x, lower, upper, alpha=0.12)
    if log_x:
        axis.set_xscale("log")
    if log_y:
        axis.set_yscale("log")
    axis.set_title(title)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.grid(True, alpha=0.28)
    axis.legend()
    _save_figure(figure, output_path)


def _category_boxplot(
    *,
    records: list[dict[str, Any]],
    category_field: str,
    metric_field: str,
    categories: Sequence[str],
    output_path: Path,
    title: str,
    ylabel: str,
) -> None:
    data = [
        _finite(
            [
                record
                for record in records
                if str(record[category_field]) == category
            ],
            metric_field,
        )
        for category in categories
    ]
    figure, axis = plt.subplots(figsize=(10, 6))
    axis.boxplot(data, tick_labels=categories, showfliers=False)
    axis.set_title(title)
    axis.set_ylabel(ylabel)
    axis.grid(axis="y", alpha=0.28)
    axis.tick_params(axis="x", rotation=20)
    _save_figure(figure, output_path)


def _feasibility_by_category(
    *,
    records: list[dict[str, Any]],
    category_field: str,
    categories: Sequence[str],
    output_path: Path,
    title: str,
) -> None:
    milp_rates: list[float] = []
    hungarian_rates: list[float] = []
    for category in categories:
        selected = [
            record
            for record in records
            if str(record[category_field]) == category
        ]
        milp_rates.append(
            float(np.mean([bool(record["milp_feasible"]) for record in selected]))
            if selected
            else math.nan
        )
        hungarian_rates.append(
            float(np.mean([bool(record["hungarian_feasible"]) for record in selected]))
            if selected
            else math.nan
        )
    x = np.arange(len(categories))
    figure, axis = plt.subplots(figsize=(11, 6))
    axis.bar(x - 0.2, milp_rates, width=0.4, label="MILP heterogéneo")
    axis.bar(x + 0.2, hungarian_rates, width=0.4, label="Hungarian homogéneo")
    axis.set_xticks(x, categories, rotation=25, ha="right")
    axis.set_ylim(0.0, 1.05)
    axis.set_ylabel("Fracción de ejecuciones factibles")
    axis.set_title(title)
    axis.grid(axis="y", alpha=0.28)
    axis.legend()
    _save_figure(figure, output_path)


def _comparison_scatter(
    *,
    records: list[dict[str, Any]],
    x_field: str,
    y_field: str,
    output_path: Path,
    title: str,
    xlabel: str,
    ylabel: str,
    log_scale: bool = False,
) -> None:
    pairs = [
        (float(record[x_field]), float(record[y_field]))
        for record in records
        if np.isfinite(float(record[x_field]))
        and np.isfinite(float(record[y_field]))
    ]
    figure, axis = plt.subplots(figsize=(7, 7))
    if pairs:
        x, y = np.asarray(pairs, dtype=np.float64).T
        axis.scatter(x, y, s=18, alpha=0.45)
        lower = max(np.min([x.min(), y.min()]), 1e-12 if log_scale else 0.0)
        upper = float(np.max([x.max(), y.max()]))
        axis.plot([lower, upper], [lower, upper], linestyle="--", color="black")
    if log_scale:
        axis.set_xscale("log")
        axis.set_yscale("log")
    axis.set_title(title)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.grid(True, alpha=0.28)
    _save_figure(figure, output_path)


def generate_all_plots(
    *,
    scaling_records: list[dict[str, Any]],
    balance_records: list[dict[str, Any]],
    asymmetry_records: list[dict[str, Any]],
    failure_records: list[dict[str, Any]],
    capacity_records: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _series_plot(
        records=scaling_records,
        x_field="N",
        y_fields=(
            ("milp_solver_wall_ns", "MILP"),
            ("hungarian_solver_wall_ns", "Hungarian"),
        ),
        output_path=output_dir / "scaling_solver_time.png",
        title="Tiempo del solver: MILP heterogéneo vs Hungarian",
        xlabel="N",
        ylabel="Tiempo [ns]",
        log_x=True,
        log_y=True,
    )
    _series_plot(
        records=scaling_records,
        x_field="N",
        y_fields=(
            ("milp_total_wall_ns", "MILP"),
            ("hungarian_total_wall_ns", "Hungarian"),
        ),
        output_path=output_dir / "scaling_total_time.png",
        title="Tiempo total por tamaño",
        xlabel="N",
        ylabel="Tiempo [ns]",
        log_x=True,
        log_y=True,
    )
    _series_plot(
        records=scaling_records,
        x_field="N",
        y_fields=(("milp_matrix_bytes", "MILP disperso"),),
        output_path=output_dir / "model_memory.png",
        title="Memoria explícita del modelo MILP",
        xlabel="N",
        ylabel="Bytes",
        log_x=True,
        log_y=True,
    )
    _series_plot(
        records=scaling_records,
        x_field="milp_binary_variable_count",
        y_fields=(("milp_node_count", "Nodos B&B"),),
        output_path=output_dir / "branch_and_bound_nodes.png",
        title="Nodos branch-and-bound",
        xlabel="Variables binarias N×K",
        ylabel="Nodos",
        log_x=True,
        log_y=False,
    )
    _series_plot(
        records=balance_records,
        x_field="requested_delta",
        y_fields=(
            ("milp_feasible", "MILP"),
            ("hungarian_feasible", "Hungarian"),
        ),
        output_path=output_dir / "balance_feasibility.png",
        title="Factibilidad frente al balance nominal δ",
        xlabel="δ solicitado",
        ylabel="Indicador de factibilidad (mediana)",
    )
    _series_plot(
        records=balance_records,
        x_field="requested_delta",
        y_fields=(("milp_to_hungarian_distance_ratio", "Ratio de distancia"),),
        output_path=output_dir / "balance_distance_ratio.png",
        title="Distancia MILP/Hungarian en casos factibles",
        xlabel="δ solicitado",
        ylabel="Ratio de distancia total",
    )
    _category_boxplot(
        records=asymmetry_records,
        category_field="spatial_mode",
        metric_field="milp_normalized_distance_p95",
        categories=tuple(HUNGARIAN.GEOMETRY_NAMES),
        output_path=output_dir / "asymmetry_spatial_p95.png",
        title="Cola de distancia MILP por geometría",
        ylabel="P95 normalizado",
    )
    _category_boxplot(
        records=asymmetry_records,
        category_field="quota_mode",
        metric_field="milp_total_excess_kg",
        categories=("symmetric", "low", "moderate", "high", "extreme"),
        output_path=output_dir / "asymmetry_quota_excess.png",
        title="Exceso de capacidad por asimetría de cuotas",
        ylabel="Exceso total [kg]",
    )
    _category_boxplot(
        records=capacity_records,
        category_field="capacity_mode",
        metric_field="capacity_cv",
        categories=tuple(CAPACITY_MODE_SIGMA),
        output_path=output_dir / "capacity_cv.png",
        title="Heterogeneidad realizada de capacidades",
        ylabel="CV de capacidades",
    )
    _feasibility_by_category(
        records=capacity_records,
        category_field="capacity_mode",
        categories=tuple(CAPACITY_MODE_SIGMA),
        output_path=output_dir / "capacity_feasibility.png",
        title="Factibilidad por nivel de heterogeneidad",
    )
    _category_boxplot(
        records=capacity_records,
        category_field="capacity_mode",
        metric_field="milp_minus_hungarian_assigned_robots",
        categories=tuple(CAPACITY_MODE_SIGMA),
        output_path=output_dir / "capacity_assigned_robot_difference.png",
        title="Cambio del número de robots reclutados",
        ylabel="MILP − Hungarian [robots]",
    )
    treatments = (
        "no_failure",
        "idle_robot_failure",
        "random_assigned_failure",
        "critical_assigned_failure",
        "random_5_percent",
        "random_10_percent",
        "random_20_percent",
        "random_30_percent",
    )
    _feasibility_by_category(
        records=failure_records,
        category_field="treatment",
        categories=treatments,
        output_path=output_dir / "failure_feasibility.png",
        title="Factibilidad después de fallos",
    )
    _category_boxplot(
        records=failure_records,
        category_field="treatment",
        metric_field="assignment_churn",
        categories=treatments,
        output_path=output_dir / "failure_assignment_churn.png",
        title="Reasignación MILP tras fallos",
        ylabel="Fracción de robots supervivientes que cambian",
    )
    _category_boxplot(
        records=failure_records,
        category_field="treatment",
        metric_field="relative_distance_increase",
        categories=treatments,
        output_path=output_dir / "failure_relative_distance.png",
        title="Incremento relativo de distancia tras fallos",
        ylabel="Incremento relativo",
    )
    all_records = (
        scaling_records
        + balance_records
        + asymmetry_records
        + failure_records
        + capacity_records
    )
    _comparison_scatter(
        records=all_records,
        x_field="hungarian_total_distance",
        y_field="milp_total_distance",
        output_path=output_dir / "paired_total_distance.png",
        title="Distancia pareada: modelos homogéneo y heterogéneo",
        xlabel="Hungarian homogéneo [m]",
        ylabel="MILP heterogéneo [m]",
    )
    _comparison_scatter(
        records=all_records,
        x_field="hungarian_solver_wall_ns",
        y_field="milp_solver_wall_ns",
        output_path=output_dir / "paired_solver_time.png",
        title="Tiempo pareado de solver",
        xlabel="Hungarian [ns]",
        ylabel="MILP [ns]",
        log_scale=True,
    )
    _series_plot(
        records=scaling_records,
        x_field="N",
        y_fields=(("milp_optimal", "Óptimo certificado"),),
        output_path=output_dir / "optimality_by_size.png",
        title="Certificación de optimalidad por tamaño",
        xlabel="N",
        ylabel="Indicador (mediana)",
        log_x=True,
    )
    _series_plot(
        records=capacity_records,
        x_field="capacity_cv",
        y_fields=(("milp_total_excess_kg", "Exceso"),),
        output_path=output_dir / "capacity_cv_vs_excess.png",
        title="Heterogeneidad y exceso de capacidad",
        xlabel="CV de capacidades",
        ylabel="Exceso total [kg]",
    )


def regenerate_plots_from_csv(output_dir: Path) -> None:
    generate_all_plots(
        scaling_records=read_csv_records(output_dir / "mc_scaling.csv"),
        balance_records=read_csv_records(output_dir / "mc_balance.csv"),
        asymmetry_records=read_csv_records(output_dir / "mc_asymmetry.csv"),
        failure_records=read_csv_records(output_dir / "mc_failures.csv"),
        capacity_records=read_csv_records(output_dir / "mc_capacity.csv"),
        output_dir=output_dir / "plots",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def config_for_profile(profile: str) -> MonteCarloConfig:
    hungarian_config = HUNGARIAN.config_for_profile(profile)
    time_limit = {"smoke": 10.0, "quick": 5.0, "full": 10.0}[profile]
    return MonteCarloConfig(
        q_bar=hungarian_config.q_bar,
        workspace_width=hungarian_config.workspace_width,
        workspace_height=hungarian_config.workspace_height,
        mean_quota=hungarian_config.mean_quota,
        base_seed=hungarian_config.base_seed,
        seeds_per_cell=hungarian_config.seeds_per_cell,
        scaling_m_values=hungarian_config.scaling_m_values,
        scaling_deltas=hungarian_config.scaling_deltas,
        balance_m_values=hungarian_config.balance_m_values,
        balance_deltas=hungarian_config.balance_deltas,
        asymmetry_m_values=hungarian_config.asymmetry_m_values,
        asymmetry_delta=hungarian_config.asymmetry_delta,
        quota_modes=hungarian_config.quota_modes,
        spatial_modes=hungarian_config.spatial_modes,
        failure_m_values=hungarian_config.failure_m_values,
        failure_deltas=hungarian_config.failure_deltas,
        failure_treatments=hungarian_config.failure_treatments,
        capacity_modes=tuple(CAPACITY_MODE_SIGMA),
        default_capacity_mode="moderate",
        max_retries=hungarian_config.max_retries,
        time_limit_seconds=time_limit,
        mip_rel_gap=0.0,
        distance_weight=1.0,
        excess_weight=0.25,
        robot_use_weight=1e-3,
    )


def _summary(
    records: list[dict[str, Any]],
    group_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    metric_fields = (
        "milp_feasible",
        "milp_optimal",
        "milp_total_distance",
        "milp_normalized_distance_p95",
        "milp_total_excess_kg",
        "milp_assigned_robot_count",
        "milp_solver_wall_ns",
        "milp_total_wall_ns",
        "milp_matrix_bytes",
        "hungarian_feasible",
        "hungarian_coverage",
        "hungarian_total_distance",
        "hungarian_solver_wall_ns",
        "milp_to_hungarian_distance_ratio",
        "milp_to_hungarian_solver_ratio",
        "assignment_churn",
        "relative_distance_increase",
        "capacity_cv",
    )
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[tuple(record[field] for field in group_fields)].append(record)

    summaries: list[dict[str, Any]] = []
    for key, group in sorted(
        grouped.items(),
        key=lambda item: tuple(str(value) for value in item[0]),
    ):
        summary = {
            field: value
            for field, value in zip(group_fields, key, strict=True)
        }
        summary["replicates"] = len(group)
        summary["milp_feasibility_rate"] = float(
            np.mean([bool(record["milp_feasible"]) for record in group])
        )
        summary["hungarian_feasibility_rate"] = float(
            np.mean([bool(record["hungarian_feasible"]) for record in group])
        )
        for metric in metric_fields:
            values = _finite(group, metric)
            summary[f"{metric}_mean"] = (
                float(np.mean(values)) if values.size else math.nan
            )
            summary[f"{metric}_std"] = (
                float(np.std(values, ddof=0)) if values.size else math.nan
            )
            summary[f"{metric}_median"] = (
                float(np.median(values)) if values.size else math.nan
            )
            summary[f"{metric}_p05"] = (
                float(np.quantile(values, 0.05)) if values.size else math.nan
            )
            summary[f"{metric}_p95"] = (
                float(np.quantile(values, 0.95)) if values.size else math.nan
            )
        summaries.append(summary)
    return summaries


def write_comparison_report(
    *,
    path: Path,
    records: list[dict[str, Any]],
    profile: str,
) -> None:
    milp_feasible = float(
        np.mean([bool(record["milp_feasible"]) for record in records])
    )
    hungarian_feasible = float(
        np.mean([bool(record["hungarian_feasible"]) for record in records])
    )
    optimal_rate = float(
        np.mean([bool(record["milp_optimal"]) for record in records])
    )
    both = [record for record in records if bool(record["both_feasible"])]
    ratios = _finite(both, "milp_to_hungarian_distance_ratio")
    homogeneous = [
        record
        for record in records
        if record["capacity_mode"] == "homogeneous"
        and bool(record["both_feasible"])
    ]
    homogeneous_differences = np.asarray(
        [
            abs(
                float(record["milp_total_distance"])
                - float(record["hungarian_total_distance"])
            )
            for record in homogeneous
        ],
        dtype=np.float64,
    )
    lines = [
        "# SP1.A2 — MILP heterogéneo frente a Hungarian homogéneo",
        "",
        f"- Perfil: `{profile}`.",
        f"- Filas método--mundo/tratamiento: {len(records)}.",
        f"- Factibilidad MILP heterogéneo: {milp_feasible:.3f}.",
        f"- Factibilidad Hungarian homogéneo: {hungarian_feasible:.3f}.",
        f"- Optimalidad MILP certificada: {optimal_rate:.3f}.",
        (
            f"- Mediana de distancia MILP/Hungarian entre casos factibles: "
            f"{float(np.median(ratios)):.4f}."
            if ratios.size
            else "- No hubo pares conjuntamente factibles para el ratio."
        ),
        (
            "- Error máximo de la reducción homogénea MILP--Hungarian: "
            f"{float(np.max(homogeneous_differences)):.3e} m."
            if homogeneous_differences.size
            else "- La reducción homogénea no tuvo pares factibles."
        ),
        "",
        "## Interpretación",
        "",
        "Hungarian resuelve el caso homogéneo expandido en slots. El MILP "
        "resuelve cargas obligatorias con capacidades individuales escalares. "
        "Cuando las capacidades son distintas, el ratio de distancia no mide "
        "por sí solo superioridad del algoritmo: también cambia el conjunto "
        "factible y el número de robots reclutados.",
        "",
        "La capacidad escalar representa carga útil nominal en kg. No certifica "
        "soporte, fuerza, wrench, contacto, navegación ni transporte físico.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_metric_crosswalk(path: Path) -> None:
    lines = [
        "# Correspondencia de métricas Hungarian–MILP",
        "",
        "| Eje Hungarian | Métrica MILP | Correspondencia | Razón |",
        "|---|---|---|---|",
        "| `N`, `K`, `M`, semilla, geometría, cuota | mismos campos | exacta | El mundo base es idéntico. |",
        "| `mission_feasible` | `milp_feasible` | exacta en significado de misión completa | Todas las cargas son obligatorias. |",
        "| `coverage` parcial de slots | `milp_complete_load_fraction` | no equivalente | El MILP no devuelve coaliciones parciales como solución. |",
        "| `total_cost` de distancia | `milp_total_distance` | comparable con cautela | Cambia el conjunto factible cuando las capacidades son heterogéneas. |",
        "| media por slot asignado | media por robot asignado y distancia por slot nominal | renombrada | Un robot heterogéneo no representa un slot. |",
        "| P50/P95/máximo/CV/Gini/Jain | `milp_assignment_distance_*` | exacta sobre distancias seleccionadas | Misma unidad: metros. |",
        "| utilización/robots libres | `milp_robot_utilization`, `milp_idle_fraction` | exacta | Cuenta robots, no capacidad. |",
        "| cuota asimétrica | `quota_asymmetry_cv` | exacta | Las cuotas nominales son pareadas. |",
        "| matriz de costes | matriz robot–carga | dimensionalmente distinta | Hungarian expande `M` slots; MILP conserva `K` cargas. |",
        "| memoria | `milp_matrix_bytes` | específica | Incluye distancias y matriz dispersa de restricciones. |",
        "| tiempos de solver/total | `milp_*_wall_ns` | exacta en reloj, no en complejidad | Se separan matriz, modelo, solver y postproceso. |",
        "| ratio greedy/oráculo | no se replica | no aplicable | El propio MILP es el oráculo central. |",
        "| mensajes/reintentos | `central_*` | modelo central explícito | No representa comunicación distribuida. |",
        "| churn/coste tras fallo | `assignment_churn`, `relative_distance_increase` | exacta sobre robots supervivientes | Los IDs fallados son pareados entre modelos. |",
        "| gap de optimalidad | `milp_mip_gap`, `milp_optimal` | adicional | Nunca se llama óptima a una incumbente sin certificado. |",
        "| heterogeneidad | `capacity_*`, `capacity_cv` | adicional | Caracteriza las capacidades individuales en kg. |",
        "",
        "La convención local solicitada por el autor denomina `q_i` a la "
        "capacidad. En la notación canónica de la memoria, `q_i` ya designa el "
        "estado del robot; por ello, esta campaña debe redactarse con "
        "`c_i^{pay}` para capacidad útil nominal.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_monte_carlo(
    *,
    config: MonteCarloConfig,
    output_dir: Path,
    profile: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    print(json.dumps(asdict(config), indent=2, ensure_ascii=False))
    scaling = run_scaling_study(config)
    balance = run_balance_study(config)
    asymmetry = run_asymmetry_study(config)
    failures = run_failure_study(config)
    capacity = run_capacity_study(config)
    all_records = scaling + balance + asymmetry + failures + capacity

    csv_records = {
        "mc_scaling.csv": scaling,
        "mc_balance.csv": balance,
        "mc_asymmetry.csv": asymmetry,
        "mc_failures.csv": failures,
        "mc_capacity.csv": capacity,
        "mc_all_runs.csv": all_records,
        "summary_scaling.csv": _summary(
            scaling,
            ("M", "requested_delta"),
        ),
        "summary_balance.csv": _summary(
            balance,
            ("M", "requested_delta"),
        ),
        "summary_asymmetry.csv": _summary(
            asymmetry,
            ("M", "quota_mode", "spatial_mode"),
        ),
        "summary_failures.csv": _summary(
            failures,
            ("M", "requested_delta", "treatment"),
        ),
        "summary_capacity.csv": _summary(
            capacity,
            ("M", "capacity_mode"),
        ),
    }
    for name, rows in csv_records.items():
        write_csv(output_dir / name, rows)

    config_path = output_dir / "config.json"
    config_path.write_text(
        json.dumps(asdict(config), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    plots_dir = output_dir / "plots"
    generate_all_plots(
        scaling_records=scaling,
        balance_records=balance,
        asymmetry_records=asymmetry,
        failure_records=failures,
        capacity_records=capacity,
        output_dir=plots_dir,
    )
    report_path = output_dir / "MILP_HUNGARIAN_COMPARISON_REPORT.md"
    write_comparison_report(
        path=report_path,
        records=all_records,
        profile=profile,
    )
    crosswalk_path = output_dir / "MILP_HUNGARIAN_METRIC_CROSSWALK.md"
    write_metric_crosswalk(crosswalk_path)

    artifacts = [
        *(output_dir / name for name in csv_records),
        config_path,
        report_path,
        crosswalk_path,
        *sorted(plots_dir.glob("*.png")),
    ]
    manifest = {
        "schema_version": 1,
        "profile": profile,
        "scientific_scope": (
            "Static centralized assignment; scalar payload capacity only."
        ),
        "comparison_note": (
            "MILP heterogeneous versus Hungarian homogeneous changes both "
            "model and method; homogeneous MILP rows audit algorithmic equivalence."
        ),
        "config": asdict(config),
        "row_counts": {
            "scaling": len(scaling),
            "balance": len(balance),
            "asymmetry": len(asymmetry),
            "failures": len(failures),
            "capacity": len(capacity),
            "all": len(all_records),
        },
        "audit": {
            "all_unique_study_seed_treatment": (
                len(
                    {
                        (
                            record["study"],
                            record["seed"],
                            record["treatment"],
                            record["capacity_mode"],
                        )
                        for record in all_records
                    }
                )
                == len(all_records)
            ),
            "capacity_modes": sorted(
                {str(record["capacity_mode"]) for record in capacity}
            ),
            "spatial_modes": sorted(
                {str(record["spatial_mode"]) for record in asymmetry}
            ),
            "quota_modes": sorted(
                {str(record["quota_mode"]) for record in asymmetry}
            ),
        },
        "artifacts": {
            path.relative_to(output_dir).as_posix(): {
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in artifacts
        },
    }
    manifest_path = output_dir / "milp_hungarian_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        f"Campaña MILP completada: {len(all_records)} filas en "
        f"{output_dir.resolve()}"
    )
    return manifest


# ===============================================================
# == Separated scientific publication ==========================
# ===============================================================


EDITORIAL_COLORS = {
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "green": "#009E73",
    "orange": "#E69F00",
    "purple": "#CC79A7",
    "sky": "#56B4E9",
    "yellow": "#F0E442",
    "ink": "#20242A",
    "muted": "#66707A",
    "grid": "#D9DEE3",
    "paper": "#FFFFFF",
}

EDITORIAL_RC = {
    "font.family": "DejaVu Sans",
    "font.size": 8.5,
    "axes.titlesize": 12,
    "axes.titleweight": "semibold",
    "axes.labelsize": 9,
    "axes.labelcolor": EDITORIAL_COLORS["ink"],
    "axes.edgecolor": EDITORIAL_COLORS["ink"],
    "axes.linewidth": 0.8,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "xtick.color": EDITORIAL_COLORS["ink"],
    "ytick.color": EDITORIAL_COLORS["ink"],
    "legend.fontsize": 7.5,
    "legend.frameon": False,
    "lines.linewidth": 1.8,
    "lines.markersize": 5.2,
    "mathtext.fontset": "stixsans",
    "figure.facecolor": EDITORIAL_COLORS["paper"],
    "axes.facecolor": EDITORIAL_COLORS["paper"],
    "savefig.facecolor": EDITORIAL_COLORS["paper"],
}

GEOMETRY_LABELS = {
    "uniform": "Uniforme",
    "clustered": "Agrupada",
    "separated": "Separada",
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

TREATMENT_LABELS = {
    "no_failure": "Sin fallo",
    "idle_robot_failure": "Robot libre",
    "random_assigned_failure": "Asignado aleatorio",
    "critical_assigned_failure": "Asignado crítico",
    "random_5_percent": "Aleatorio 5 %",
    "random_10_percent": "Aleatorio 10 %",
    "random_20_percent": "Aleatorio 20 %",
    "random_30_percent": "Aleatorio 30 %",
}


def _editorial_axis(axis: Any, *, grid_axis: str = "y") -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color(EDITORIAL_COLORS["ink"])
    axis.spines["bottom"].set_color(EDITORIAL_COLORS["ink"])
    axis.grid(
        True,
        axis=grid_axis,
        color=EDITORIAL_COLORS["grid"],
        linewidth=0.65,
        alpha=0.75,
    )
    axis.set_axisbelow(True)
    axis.tick_params(direction="out", length=3.0, width=0.7)


def _figure_heading(
    figure: Any,
    axis: Any,
    *,
    title: str,
    subtitle: str,
) -> None:
    del figure
    axis.set_title(
        title,
        loc="left",
        pad=27,
        color=EDITORIAL_COLORS["ink"],
        fontsize=12,
        fontweight="semibold",
    )
    axis.text(
        0.0,
        1.015,
        subtitle,
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        color=EDITORIAL_COLORS["muted"],
        fontsize=7.5,
    )


def _indicator_box(axis: Any, text: str, *, location: str = "upper left") -> None:
    coordinates = {
        "upper left": (0.02, 0.98, "left", "top"),
        "upper right": (0.98, 0.98, "right", "top"),
        "lower left": (0.02, 0.03, "left", "bottom"),
        "lower right": (0.98, 0.03, "right", "bottom"),
    }
    x, y, horizontal, vertical = coordinates[location]
    axis.text(
        x,
        y,
        text,
        transform=axis.transAxes,
        ha=horizontal,
        va=vertical,
        fontsize=7.2,
        color=EDITORIAL_COLORS["ink"],
        linespacing=1.35,
        bbox={
            "boxstyle": "round,pad=0.38",
            "facecolor": "#FFFFFF",
            "edgecolor": EDITORIAL_COLORS["grid"],
            "linewidth": 0.7,
            "alpha": 0.94,
        },
        zorder=20,
    )


def _save_editorial_figure(figure: Any, png_path: Path) -> tuple[Path, Path]:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path = png_path.with_suffix(".pdf")
    figure.savefig(
        png_path,
        dpi=450,
        bbox_inches="tight",
        facecolor="white",
        metadata={"Software": "sp1_a2_milp.py"},
    )
    figure.savefig(
        pdf_path,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)
    return png_path, pdf_path


def _numeric_pairs(
    records: Iterable[dict[str, Any]],
    x_field: str,
    y_field: str,
) -> tuple[FloatArray, FloatArray]:
    pairs: list[tuple[float, float]] = []
    for record in records:
        try:
            x_value = float(record[x_field])
            y_value = float(record[y_field])
        except (KeyError, TypeError, ValueError):
            continue
        if np.isfinite(x_value) and np.isfinite(y_value):
            pairs.append((x_value, y_value))
    if not pairs:
        return (
            np.asarray([], dtype=np.float64),
            np.asarray([], dtype=np.float64),
        )
    x_values, y_values = np.asarray(pairs, dtype=np.float64).T
    return x_values, y_values


def _group_quantiles(
    records: Iterable[dict[str, Any]],
    *,
    x_field: str,
    y_field: str,
    scale: float = 1.0,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray, IntArray]:
    groups: dict[float, list[float]] = defaultdict(list)
    x_values, y_values = _numeric_pairs(records, x_field, y_field)
    for x_value, y_value in zip(x_values, y_values, strict=True):
        groups[float(x_value)].append(float(y_value) * scale)
    ordered_x = np.asarray(sorted(groups), dtype=np.float64)
    medians = np.asarray(
        [np.median(groups[value]) for value in ordered_x],
        dtype=np.float64,
    )
    lower = np.asarray(
        [np.quantile(groups[value], 0.05) for value in ordered_x],
        dtype=np.float64,
    )
    upper = np.asarray(
        [np.quantile(groups[value], 0.95) for value in ordered_x],
        dtype=np.float64,
    )
    counts = np.asarray(
        [len(groups[value]) for value in ordered_x],
        dtype=np.int64,
    )
    return ordered_x, medians, lower, upper, counts


def _power_law_fit(
    x_values: Sequence[float],
    y_values: Sequence[float],
) -> tuple[float, float, float] | None:
    x = np.asarray(x_values, dtype=np.float64)
    y = np.asarray(y_values, dtype=np.float64)
    mask = np.isfinite(x) & np.isfinite(y) & (x > 0.0) & (y > 0.0)
    if np.count_nonzero(mask) < 3 or np.unique(x[mask]).size < 3:
        return None
    log_x = np.log10(x[mask])
    log_y = np.log10(y[mask])
    slope, intercept = np.polyfit(log_x, log_y, 1)
    predicted = slope * log_x + intercept
    residual = float(np.sum((log_y - predicted) ** 2))
    total = float(np.sum((log_y - np.mean(log_y)) ** 2))
    r_squared = 1.0 - residual / total if total > 0.0 else 1.0
    return float(slope), float(intercept), float(r_squared)


def _linear_fit(
    x_values: Sequence[float],
    y_values: Sequence[float],
) -> tuple[float, float, float] | None:
    x = np.asarray(x_values, dtype=np.float64)
    y = np.asarray(y_values, dtype=np.float64)
    mask = np.isfinite(x) & np.isfinite(y)
    if np.count_nonzero(mask) < 3 or np.unique(x[mask]).size < 2:
        return None
    slope, intercept = np.polyfit(x[mask], y[mask], 1)
    predicted = slope * x[mask] + intercept
    residual = float(np.sum((y[mask] - predicted) ** 2))
    total = float(np.sum((y[mask] - np.mean(y[mask])) ** 2))
    r_squared = 1.0 - residual / total if total > 0.0 else 1.0
    return float(slope), float(intercept), float(r_squared)


def _wilson_interval(successes: int, total: int) -> tuple[float, float, float]:
    if total <= 0:
        return math.nan, math.nan, math.nan
    z = 1.959963984540054
    rate = successes / total
    denominator = 1.0 + z**2 / total
    center = (rate + z**2 / (2.0 * total)) / denominator
    half_width = (
        z
        * math.sqrt(
            rate * (1.0 - rate) / total
            + z**2 / (4.0 * total**2)
        )
        / denominator
    )
    return rate, max(0.0, center - half_width), min(1.0, center + half_width)


def _binary_rate_by_category(
    records: Iterable[dict[str, Any]],
    *,
    category_field: str,
    value_field: str,
    categories: Sequence[Any],
) -> tuple[FloatArray, FloatArray, FloatArray, IntArray]:
    rates: list[float] = []
    lower: list[float] = []
    upper: list[float] = []
    counts: list[int] = []
    for category in categories:
        selected = [
            record
            for record in records
            if record.get(category_field) == category
        ]
        successes = sum(bool(record.get(value_field)) for record in selected)
        rate, low, high = _wilson_interval(successes, len(selected))
        rates.append(rate)
        lower.append(low)
        upper.append(high)
        counts.append(len(selected))
    rates_array = np.asarray(rates, dtype=np.float64)
    return (
        rates_array,
        np.maximum(
            0.0,
            rates_array - np.asarray(lower, dtype=np.float64),
        ),
        np.maximum(
            0.0,
            np.asarray(upper, dtype=np.float64) - rates_array,
        ),
        np.asarray(counts, dtype=np.int64),
    )


def _append_indicator(
    indicators: list[dict[str, Any]],
    *,
    figure: str,
    indicator: str,
    value: float | int | str,
    unit: str,
    interpretation: str,
) -> None:
    indicators.append(
        {
            "figure": figure,
            "indicator": indicator,
            "value": value,
            "unit": unit,
            "interpretation": interpretation,
        }
    )


def _styled_boxplot(
    axis: Any,
    data: Sequence[FloatArray],
    labels: Sequence[str],
    *,
    color: str = EDITORIAL_COLORS["blue"],
    median_format: str = ".3g",
) -> None:
    boxplot = axis.boxplot(
        data,
        tick_labels=labels,
        widths=0.58,
        showfliers=False,
        patch_artist=True,
        medianprops={
            "color": EDITORIAL_COLORS["vermillion"],
            "linewidth": 1.6,
        },
        boxprops={
            "facecolor": color,
            "edgecolor": color,
            "alpha": 0.18,
            "linewidth": 1.0,
        },
        whiskerprops={"color": EDITORIAL_COLORS["muted"], "linewidth": 0.9},
        capprops={"color": EDITORIAL_COLORS["muted"], "linewidth": 0.9},
    )
    for patch in boxplot["boxes"]:
        patch.set_facecolor(mpl.colors.to_rgba(color, 0.18))
    random_generator = np.random.default_rng(20260729)
    for index, values in enumerate(data, start=1):
        finite = np.asarray(values, dtype=np.float64)
        finite = finite[np.isfinite(finite)]
        if finite.size == 0:
            continue
        sample = finite
        if finite.size > 120:
            sample = random_generator.choice(finite, size=120, replace=False)
        jitter = random_generator.normal(0.0, 0.045, size=sample.size)
        axis.scatter(
            np.full(sample.size, index) + jitter,
            sample,
            s=9,
            marker="o",
            facecolor=mpl.colors.to_rgba(color, 0.22),
            edgecolor="none",
            zorder=2,
        )
        median = float(np.median(finite))
        axis.text(
            index,
            median,
            f" {format(median, median_format)}",
            va="center",
            ha="left",
            fontsize=6.6,
            color=EDITORIAL_COLORS["vermillion"],
            fontweight="semibold",
        )


def generate_milp_editorial_plots(
    *,
    datasets: dict[str, list[dict[str, Any]]],
    output_dir: Path,
    profile: str,
) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    scaling = datasets["scaling"]
    balance = datasets["balance"]
    asymmetry = datasets["asymmetry"]
    failures = datasets["failures"]
    capacity = datasets["capacity"]
    indicators: list[dict[str, Any]] = []

    with mpl.rc_context(EDITORIAL_RC):
        # 1. Solver scaling.
        x, median, lower, upper, counts = _group_quantiles(
            scaling,
            x_field="N",
            y_field="milp_solver_wall_ns",
            scale=1e-6,
        )
        fit = _power_law_fit(x, median)
        figure, axis = plt.subplots(
            figsize=(7.2, 4.8),
            constrained_layout=True,
        )
        axis.fill_between(
            x,
            lower,
            upper,
            color=EDITORIAL_COLORS["blue"],
            alpha=0.14,
            linewidth=0.0,
            label="P05–P95",
        )
        axis.plot(
            x,
            median,
            color=EDITORIAL_COLORS["blue"],
            marker="o",
            markerfacecolor="white",
            markeredgewidth=1.2,
            label="Mediana",
        )
        if fit is not None:
            slope, intercept, r_squared = fit
            fitted_x = np.geomspace(float(np.min(x)), float(np.max(x)), 160)
            fitted_y = 10.0 ** intercept * fitted_x**slope
            axis.plot(
                fitted_x,
                fitted_y,
                color=EDITORIAL_COLORS["vermillion"],
                linestyle="--",
                label="Ajuste log–log",
            )
            fit_text = (
                f"Tendencia descriptiva\n"
                f"$t \\propto N^{{{slope:.2f}}}$ · $R^2={r_squared:.2f}$\n"
                f"$n={sum(counts)}$ ejecuciones"
            )
            _append_indicator(
                indicators,
                figure="milp_scaling_solver_time",
                indicator="log_log_exponent",
                value=slope,
                unit="adimensional",
                interpretation=(
                    "Pendiente OLS descriptiva sobre medianas; no es una "
                    "cota de complejidad."
                ),
            )
            _append_indicator(
                indicators,
                figure="milp_scaling_solver_time",
                indicator="r_squared",
                value=r_squared,
                unit="adimensional",
                interpretation="Ajuste de la tendencia log–log observada.",
            )
        else:
            fit_text = f"Sin ajuste identificable\n$n={sum(counts)}$ ejecuciones"
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlabel("Robots disponibles, $N$")
        axis.set_ylabel("Tiempo del solver [ms]")
        _editorial_axis(axis, grid_axis="both")
        _figure_heading(
            figure,
            axis,
            title="Escalabilidad temporal del MILP heterogéneo",
            subtitle=(
                f"Perfil {profile} · mediana y banda empírica P05–P95 "
                "por tamaño"
            ),
        )
        _indicator_box(axis, fit_text, location="upper left")
        axis.legend(loc="lower right", ncols=3)
        _save_editorial_figure(
            figure,
            output_dir / "milp_scaling_solver_time.png",
        )

        # 2. Explicit model memory.
        x, median, lower, upper, counts = _group_quantiles(
            scaling,
            x_field="N",
            y_field="milp_matrix_bytes",
            scale=1.0 / (1024.0**2),
        )
        fit = _power_law_fit(x, median)
        figure, axis = plt.subplots(
            figsize=(7.2, 4.8),
            constrained_layout=True,
        )
        axis.fill_between(
            x,
            lower,
            upper,
            color=EDITORIAL_COLORS["green"],
            alpha=0.14,
            linewidth=0.0,
            label="P05–P95",
        )
        axis.plot(
            x,
            median,
            color=EDITORIAL_COLORS["green"],
            marker="s",
            markerfacecolor="white",
            markeredgewidth=1.2,
            label="Mediana",
        )
        if fit is not None:
            slope, intercept, r_squared = fit
            fitted_x = np.geomspace(float(np.min(x)), float(np.max(x)), 160)
            axis.plot(
                fitted_x,
                10.0 ** intercept * fitted_x**slope,
                color=EDITORIAL_COLORS["vermillion"],
                linestyle="--",
                label="Ajuste log–log",
            )
            box_text = (
                f"Pendiente observada: {slope:.2f}\n"
                f"$R^2={r_squared:.2f}$ · $n={sum(counts)}$"
            )
            _append_indicator(
                indicators,
                figure="milp_scaling_memory",
                indicator="log_log_exponent",
                value=slope,
                unit="adimensional",
                interpretation=(
                    "Crecimiento empírico de la memoria explícita del modelo "
                    "disperso."
                ),
            )
        else:
            box_text = f"$n={sum(counts)}$ ejecuciones"
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlabel("Robots disponibles, $N$")
        axis.set_ylabel("Memoria explícita [MiB]")
        _editorial_axis(axis, grid_axis="both")
        _figure_heading(
            figure,
            axis,
            title="Huella de memoria del modelo disperso",
            subtitle="Matriz robot–carga más restricciones CSR; no incluye el solver",
        )
        _indicator_box(axis, box_text, location="upper left")
        axis.legend(loc="lower right", ncols=3)
        _save_editorial_figure(
            figure,
            output_dir / "milp_scaling_memory.png",
        )

        # 3. Balance and feasibility.
        deltas = sorted({float(record["requested_delta"]) for record in balance})
        rates, error_low, error_high, counts = _binary_rate_by_category(
            balance,
            category_field="requested_delta",
            value_field="milp_feasible",
            categories=deltas,
        )
        figure, axis = plt.subplots(
            figsize=(7.2, 4.8),
            constrained_layout=True,
        )
        axis.axvspan(
            min(deltas),
            0.0,
            color=EDITORIAL_COLORS["vermillion"],
            alpha=0.055,
            linewidth=0.0,
        )
        axis.axvline(
            0.0,
            color=EDITORIAL_COLORS["muted"],
            linestyle=":",
            linewidth=1.0,
        )
        axis.errorbar(
            deltas,
            rates,
            yerr=np.vstack((error_low, error_high)),
            color=EDITORIAL_COLORS["blue"],
            marker="o",
            markerfacecolor="white",
            markeredgewidth=1.2,
            capsize=2.5,
            label="Factibilidad e IC Wilson 95 %",
        )
        for delta, rate, count in zip(deltas, rates, counts, strict=True):
            axis.annotate(
                f"{rate:.0%}\n$n={count}$",
                (delta, rate),
                xytext=(0, 7),
                textcoords="offset points",
                ha="center",
                fontsize=6.2,
                color=EDITORIAL_COLORS["muted"],
            )
        overall_rate = float(
            np.mean([bool(record["milp_feasible"]) for record in balance])
        )
        axis.set_ylim(-0.02, 1.08)
        axis.yaxis.set_major_formatter(PercentFormatter(1.0))
        axis.set_xlabel("Balance nominal, $\\delta=(N-M)/(N+M)$")
        axis.set_ylabel("Mundos factibles")
        _editorial_axis(axis)
        _figure_heading(
            figure,
            axis,
            title="Factibilidad frente al balance de recursos",
            subtitle=(
                "La zona sombreada indica déficit nominal de robots "
                "respecto a slots"
            ),
        )
        _indicator_box(
            axis,
            f"Factibilidad global\n{overall_rate:.1%} · $n={len(balance)}$",
            location="lower right",
        )
        _append_indicator(
            indicators,
            figure="milp_balance_feasibility",
            indicator="overall_feasibility_rate",
            value=overall_rate,
            unit="proporción",
            interpretation="Factibilidad de misión completa en el estudio balance.",
        )
        _save_editorial_figure(
            figure,
            output_dir / "milp_balance_feasibility.png",
        )

        # 4. Optimality certification by size.
        sizes = sorted({int(record["N"]) for record in scaling})
        rates, error_low, error_high, counts = _binary_rate_by_category(
            scaling,
            category_field="N",
            value_field="milp_optimal",
            categories=sizes,
        )
        figure, axis = plt.subplots(
            figsize=(7.2, 4.8),
            constrained_layout=True,
        )
        axis.errorbar(
            sizes,
            rates,
            yerr=np.vstack((error_low, error_high)),
            color=EDITORIAL_COLORS["purple"],
            marker="D",
            markerfacecolor="white",
            markeredgewidth=1.1,
            capsize=2.2,
            linewidth=1.5,
        )
        axis.set_xscale("log")
        axis.set_ylim(-0.02, 1.08)
        axis.yaxis.set_major_formatter(PercentFormatter(1.0))
        axis.set_xlabel("Robots disponibles, $N$")
        axis.set_ylabel("Optimalidad certificada")
        _editorial_axis(axis, grid_axis="both")
        overall_optimal = float(
            np.mean([bool(record["milp_optimal"]) for record in scaling])
        )
        _figure_heading(
            figure,
            axis,
            title="Certificación de optimalidad bajo límite de tiempo",
            subtitle=(
                "Una solución factible sin certificado no se contabiliza "
                "como óptima"
            ),
        )
        _indicator_box(
            axis,
            f"Certificación global\n{overall_optimal:.1%} · "
            f"$n={sum(counts)}$",
            location="lower left",
        )
        _append_indicator(
            indicators,
            figure="milp_optimality_by_size",
            indicator="optimality_certificate_rate",
            value=overall_optimal,
            unit="proporción",
            interpretation=(
                "Fracción de instancias de escala con certificado del solver."
            ),
        )
        _save_editorial_figure(
            figure,
            output_dir / "milp_optimality_by_size.png",
        )

        # 5. Spatial asymmetry and distance tail.
        geometry_order = tuple(HUNGARIAN.GEOMETRY_NAMES)
        data = [
            _finite(
                [
                    record
                    for record in asymmetry
                    if record["spatial_mode"] == mode
                ],
                "milp_normalized_distance_p95",
            )
            for mode in geometry_order
        ]
        figure, axis = plt.subplots(
            figsize=(7.2, 4.8),
            constrained_layout=True,
        )
        _styled_boxplot(
            axis,
            data,
            [GEOMETRY_LABELS[mode] for mode in geometry_order],
        )
        axis.set_ylabel("P95 de distancia / diagonal del workspace")
        axis.tick_params(axis="x", rotation=12)
        _editorial_axis(axis)
        medians = [float(np.median(values)) for values in data if values.size]
        worst_index = int(np.argmax(medians))
        _figure_heading(
            figure,
            axis,
            title="Cola de distancia por geometría espacial",
            subtitle=(
                "Caja: IQR; línea naranja: mediana; puntos: muestra de ejecuciones"
            ),
        )
        _indicator_box(
            axis,
            f"Mayor mediana\n{GEOMETRY_LABELS[geometry_order[worst_index]]}: "
            f"{medians[worst_index]:.3f}",
            location="upper right",
        )
        _append_indicator(
            indicators,
            figure="milp_geometry_distance_tail",
            indicator="largest_median_geometry",
            value=geometry_order[worst_index],
            unit="categoría",
            interpretation=(
                "Geometría con mayor mediana del P95 normalizado."
            ),
        )
        _save_editorial_figure(
            figure,
            output_dir / "milp_geometry_distance_tail.png",
        )

        # 6. Capacity heterogeneity: feasibility and excess.
        modes = tuple(CAPACITY_MODE_SIGMA)
        rates, error_low, error_high, counts = _binary_rate_by_category(
            capacity,
            category_field="capacity_mode",
            value_field="milp_feasible",
            categories=modes,
        )
        figure, axes = plt.subplots(
            1,
            2,
            figsize=(9.6, 4.8),
            constrained_layout=True,
        )
        left, right = axes
        positions = np.arange(len(modes))
        bars = left.bar(
            positions,
            rates,
            color=EDITORIAL_COLORS["blue"],
            alpha=0.82,
            width=0.64,
            yerr=np.vstack((error_low, error_high)),
            capsize=2.5,
        )
        left.set_xticks(
            positions,
            [CAPACITY_LABELS[mode] for mode in modes],
            rotation=18,
            ha="right",
        )
        left.set_ylim(0.0, 1.08)
        left.yaxis.set_major_formatter(PercentFormatter(1.0))
        left.set_ylabel("Mundos factibles")
        left.set_title("A  ·  Factibilidad", loc="left", fontsize=9)
        left.bar_label(bars, labels=[f"{value:.0%}" for value in rates], padding=2)
        _editorial_axis(left)

        mode_colors = {
            "homogeneous": EDITORIAL_COLORS["muted"],
            "low": EDITORIAL_COLORS["sky"],
            "moderate": EDITORIAL_COLORS["blue"],
            "high": EDITORIAL_COLORS["orange"],
            "extreme": EDITORIAL_COLORS["vermillion"],
        }
        for mode in modes:
            selected = [
                record
                for record in capacity
                if record["capacity_mode"] == mode
            ]
            x_values, y_values = _numeric_pairs(
                selected,
                "capacity_cv",
                "milp_total_excess_kg",
            )
            right.scatter(
                x_values,
                y_values,
                s=22,
                marker={"homogeneous": "s"}.get(mode, "o"),
                facecolor=mode_colors[mode],
                edgecolor="white",
                linewidth=0.45,
                alpha=0.78,
                label=CAPACITY_LABELS[mode],
            )
        all_x, all_y = _numeric_pairs(
            capacity,
            "capacity_cv",
            "milp_total_excess_kg",
        )
        fit = _linear_fit(all_x, all_y)
        if fit is not None:
            slope, intercept, r_squared = fit
            if r_squared >= 0.30:
                fit_x = np.linspace(
                    float(np.min(all_x)),
                    float(np.max(all_x)),
                    120,
                )
                right.plot(
                    fit_x,
                    slope * fit_x + intercept,
                    color=EDITORIAL_COLORS["ink"],
                    linestyle="--",
                    linewidth=1.1,
                    label="OLS descriptiva",
                )
                fit_message = (
                    f"Pendiente: {slope:.2f} kg/CV\n"
                    f"$R^2={r_squared:.2f}$ · $n={len(all_x)}$"
                )
            else:
                fit_message = (
                    "Sin tendencia lineal clara\n"
                    f"$R^2={r_squared:.2f}$ · $n={len(all_x)}$"
                )
            _indicator_box(right, fit_message, location="upper left")
            _append_indicator(
                indicators,
                figure="milp_capacity_effects",
                indicator="excess_vs_capacity_cv_slope",
                value=slope,
                unit="kg por CV",
                interpretation=(
                    "Tendencia OLS descriptiva entre heterogeneidad realizada "
                    "y exceso de capacidad."
                ),
            )
            _append_indicator(
                indicators,
                figure="milp_capacity_effects",
                indicator="excess_vs_capacity_cv_r_squared",
                value=r_squared,
                unit="adimensional",
                interpretation=(
                    "Bondad de ajuste de la tendencia lineal descriptiva."
                ),
            )
        right.set_xlabel("CV de capacidad individual")
        right.set_ylabel("Exceso total reclutado [kg]")
        right.set_title("B  ·  Exceso de capacidad", loc="left", fontsize=9)
        _editorial_axis(right)
        right.legend(loc="best", ncols=2)
        figure.suptitle(
            "Efecto de la heterogeneidad de capacidades",
            x=0.055,
            y=1.02,
            ha="left",
            fontsize=12,
            fontweight="semibold",
            color=EDITORIAL_COLORS["ink"],
        )
        _append_indicator(
            indicators,
            figure="milp_capacity_effects",
            indicator="minimum_feasibility_rate",
            value=float(np.min(rates)),
            unit="proporción",
            interpretation=(
                "Menor factibilidad entre los cinco niveles de heterogeneidad."
            ),
        )
        _save_editorial_figure(
            figure,
            output_dir / "milp_capacity_effects.png",
        )

        # 7. Recruitment relative to homogeneous nominal slots.
        recruitment_records = []
        for record in capacity:
            enriched = dict(record)
            enriched["assigned_over_nominal_slots"] = (
                float(record["milp_assigned_robot_count"]) / float(record["M"])
                if float(record["M"]) > 0.0
                else math.nan
            )
            recruitment_records.append(enriched)
        data = [
            _finite(
                [
                    record
                    for record in recruitment_records
                    if record["capacity_mode"] == mode
                ],
                "assigned_over_nominal_slots",
            )
            for mode in modes
        ]
        figure, axis = plt.subplots(
            figsize=(7.2, 4.8),
            constrained_layout=True,
        )
        axis.axhline(
            1.0,
            color=EDITORIAL_COLORS["muted"],
            linestyle="--",
            linewidth=1.0,
            label="Referencia homogénea $N_{asig}=M$",
        )
        _styled_boxplot(
            axis,
            data,
            [CAPACITY_LABELS[mode] for mode in modes],
            color=EDITORIAL_COLORS["green"],
        )
        axis.set_ylabel("Robots asignados / slots nominales")
        axis.tick_params(axis="x", rotation=12)
        _editorial_axis(axis)
        _figure_heading(
            figure,
            axis,
            title="Reclutamiento bajo capacidad heterogénea",
            subtitle=(
                "Valores <1 indican que robots de mayor capacidad sustituyen "
                "varios slots nominales"
            ),
        )
        extreme_median = float(np.median(data[-1]))
        _indicator_box(
            axis,
            f"Heterogeneidad extrema\nMediana: {extreme_median:.3f}",
            location="upper right",
        )
        _append_indicator(
            indicators,
            figure="milp_capacity_recruitment",
            indicator="extreme_capacity_recruitment_ratio_median",
            value=extreme_median,
            unit="robots por slot nominal",
            interpretation=(
                "Mediana del reclutamiento relativo con heterogeneidad extrema."
            ),
        )
        axis.legend(loc="lower left")
        _save_editorial_figure(
            figure,
            output_dir / "milp_capacity_recruitment.png",
        )

        # 8. Failure resilience: feasibility and churn.
        treatments = tuple(TREATMENT_LABELS)
        rates, error_low, error_high, counts = _binary_rate_by_category(
            failures,
            category_field="treatment",
            value_field="milp_feasible",
            categories=treatments,
        )
        figure, axes = plt.subplots(
            1,
            2,
            figsize=(10.8, 4.8),
            constrained_layout=True,
        )
        left, right = axes
        positions = np.arange(len(treatments))
        bars = left.barh(
            positions,
            rates,
            color=EDITORIAL_COLORS["blue"],
            alpha=0.82,
            xerr=np.vstack((error_low, error_high)),
            capsize=2.3,
        )
        left.set_yticks(
            positions,
            [TREATMENT_LABELS[item] for item in treatments],
        )
        left.invert_yaxis()
        left.set_xlim(0.0, 1.08)
        left.xaxis.set_major_formatter(PercentFormatter(1.0))
        left.set_xlabel("Mundos recuperados")
        left.set_title("A  ·  Factibilidad posterior", loc="left", fontsize=9)
        left.bar_label(
            bars,
            labels=[f"{value:.0%}" for value in rates],
            padding=3,
            fontsize=6.5,
        )
        _editorial_axis(left, grid_axis="x")

        churn_data = [
            _finite(
                [
                    record
                    for record in failures
                    if record["treatment"] == treatment
                ],
                "assignment_churn",
            )
            for treatment in treatments
        ]
        _styled_boxplot(
            right,
            churn_data,
            [TREATMENT_LABELS[item] for item in treatments],
            color=EDITORIAL_COLORS["purple"],
            median_format=".1%",
        )
        right.set_ylabel("Robots supervivientes que cambian de carga")
        right.yaxis.set_major_formatter(PercentFormatter(1.0))
        right.tick_params(axis="x", rotation=35)
        right.set_title("B  ·  Churn de reasignación", loc="left", fontsize=9)
        _editorial_axis(right)
        figure.suptitle(
            "Resiliencia del MILP ante fallos de robots",
            x=0.05,
            y=1.02,
            ha="left",
            fontsize=12,
            fontweight="semibold",
            color=EDITORIAL_COLORS["ink"],
        )
        worst_index = int(np.argmin(rates))
        _append_indicator(
            indicators,
            figure="milp_failure_resilience",
            indicator="worst_treatment_feasibility",
            value=float(rates[worst_index]),
            unit="proporción",
            interpretation=(
                f"Factibilidad mínima observada en "
                f"{TREATMENT_LABELS[treatments[worst_index]]}."
            ),
        )
        _save_editorial_figure(
            figure,
            output_dir / "milp_failure_resilience.png",
        )

        # 9. Fleet utilization by geometry.
        utilization_data = [
            _finite(
                [
                    record
                    for record in asymmetry
                    if record["spatial_mode"] == mode
                ],
                "milp_robot_utilization",
            )
            for mode in geometry_order
        ]
        figure, axis = plt.subplots(
            figsize=(7.2, 4.8),
            constrained_layout=True,
        )
        _styled_boxplot(
            axis,
            utilization_data,
            [GEOMETRY_LABELS[mode] for mode in geometry_order],
            color=EDITORIAL_COLORS["orange"],
            median_format=".1%",
        )
        axis.set_ylabel("Robots asignados / robots disponibles")
        axis.set_ylim(0.0, 1.04)
        axis.yaxis.set_major_formatter(PercentFormatter(1.0))
        axis.tick_params(axis="x", rotation=12)
        _editorial_axis(axis)
        _figure_heading(
            figure,
            axis,
            title="Utilización de flota por geometría",
            subtitle=(
                "Fracción de robots reclutados por el MILP en cada mundo "
                "factible"
            ),
        )
        median_utilization = float(
            np.median(
                np.concatenate(
                    [values for values in utilization_data if values.size]
                )
            )
        )
        _indicator_box(
            axis,
            f"Mediana global\n{median_utilization:.1%} de la flota",
            location="upper right",
        )
        _append_indicator(
            indicators,
            figure="milp_fleet_utilization",
            indicator="global_median_robot_utilization",
            value=median_utilization,
            unit="proporción",
            interpretation="Fracción mediana de robots reclutados.",
        )
        _save_editorial_figure(
            figure,
            output_dir / "milp_fleet_utilization.png",
        )

    return indicators


def generate_controlled_comparison_plots(
    *,
    datasets: dict[str, list[dict[str, Any]]],
    output_dir: Path,
    profile: str,
) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_records = [
        record
        for name in ("scaling", "balance", "asymmetry", "failures")
        for record in datasets[name]
    ]
    indicators: list[dict[str, Any]] = []
    study_order = ("scaling", "balance", "asymmetry", "failures")
    study_labels = {
        "scaling": "Escala",
        "balance": "Balance",
        "asymmetry": "Asimetría",
        "failures": "Fallos",
    }
    study_colors = {
        "scaling": EDITORIAL_COLORS["blue"],
        "balance": EDITORIAL_COLORS["green"],
        "asymmetry": EDITORIAL_COLORS["orange"],
        "failures": EDITORIAL_COLORS["purple"],
    }
    study_markers = {
        "scaling": "o",
        "balance": "s",
        "asymmetry": "^",
        "failures": "D",
    }

    with mpl.rc_context(EDITORIAL_RC):
        # 1. Exact objective-quality parity.
        jointly_feasible = [
            record
            for record in all_records
            if bool(record["both_feasible"])
        ]
        x_values, y_values = _numeric_pairs(
            jointly_feasible,
            "hungarian_total_distance",
            "milp_total_distance",
        )
        absolute_errors = np.abs(y_values - x_values)
        max_error = (
            float(np.max(absolute_errors)) if absolute_errors.size else math.nan
        )
        figure, axis = plt.subplots(
            figsize=(6.4, 6.4),
            constrained_layout=True,
        )
        for study in study_order:
            selected = [
                record
                for record in jointly_feasible
                if record["study"] == study
            ]
            x_study, y_study = _numeric_pairs(
                selected,
                "hungarian_total_distance",
                "milp_total_distance",
            )
            axis.scatter(
                x_study,
                y_study,
                s=24,
                marker=study_markers[study],
                facecolor=mpl.colors.to_rgba(study_colors[study], 0.58),
                edgecolor="white",
                linewidth=0.45,
                label=f"{study_labels[study]} · $n={len(x_study)}$",
            )
        if x_values.size:
            lower = float(min(np.min(x_values), np.min(y_values)))
            upper = float(max(np.max(x_values), np.max(y_values)))
            padding = max(1e-9, 0.035 * (upper - lower))
            axis.plot(
                [lower - padding, upper + padding],
                [lower - padding, upper + padding],
                color=EDITORIAL_COLORS["ink"],
                linestyle="--",
                linewidth=1.1,
                label="Paridad $y=x$",
            )
            axis.set_xlim(lower - padding, upper + padding)
            axis.set_ylim(lower - padding, upper + padding)
        axis.set_aspect("equal", adjustable="box")
        axis.set_xlabel("Distancia Hungarian homogéneo [m]")
        axis.set_ylabel("Distancia MILP homogéneo [m]")
        _editorial_axis(axis, grid_axis="both")
        _figure_heading(
            figure,
            axis,
            title="Paridad de distancia en el problema homogéneo",
            subtitle=(
                "Mismos mundos, capacidades, cargas y semillas; cada punto "
                "es una instancia conjuntamente factible"
            ),
        )
        _indicator_box(
            axis,
            f"Error absoluto máximo\n{max_error:.3e} m\n"
            f"$n={len(x_values)}$ pares",
            location="upper left",
        )
        axis.legend(loc="lower right")
        _append_indicator(
            indicators,
            figure="comparison_distance_parity",
            indicator="maximum_absolute_distance_error",
            value=max_error,
            unit="m",
            interpretation=(
                "Diferencia máxima entre costes de distancia en la reducción "
                "homogénea."
            ),
        )
        _save_editorial_figure(
            figure,
            output_dir / "comparison_distance_parity.png",
        )

        # 2. Paired solver time.
        runtime_records = [
            record
            for record in all_records
            if float(record["milp_solver_wall_ns"]) > 0.0
            and float(record["hungarian_solver_wall_ns"]) > 0.0
        ]
        x_values, y_values = _numeric_pairs(
            runtime_records,
            "hungarian_solver_wall_ns",
            "milp_solver_wall_ns",
        )
        x_ms = x_values * 1e-6
        y_ms = y_values * 1e-6
        runtime_ratios = y_values / x_values
        median_ratio = (
            float(np.median(runtime_ratios))
            if runtime_ratios.size
            else math.nan
        )
        p05_ratio = (
            float(np.quantile(runtime_ratios, 0.05))
            if runtime_ratios.size
            else math.nan
        )
        p95_ratio = (
            float(np.quantile(runtime_ratios, 0.95))
            if runtime_ratios.size
            else math.nan
        )
        figure, axis = plt.subplots(
            figsize=(6.4, 6.4),
            constrained_layout=True,
        )
        for study in study_order:
            selected = [
                record
                for record in runtime_records
                if record["study"] == study
            ]
            x_study, y_study = _numeric_pairs(
                selected,
                "hungarian_solver_wall_ns",
                "milp_solver_wall_ns",
            )
            axis.scatter(
                x_study * 1e-6,
                y_study * 1e-6,
                s=24,
                marker=study_markers[study],
                facecolor=mpl.colors.to_rgba(study_colors[study], 0.58),
                edgecolor="white",
                linewidth=0.45,
                label=study_labels[study],
            )
        if x_ms.size:
            lower = float(max(min(np.min(x_ms), np.min(y_ms)), 1e-6))
            upper = float(max(np.max(x_ms), np.max(y_ms)))
            axis.plot(
                [lower, upper],
                [lower, upper],
                color=EDITORIAL_COLORS["ink"],
                linestyle="--",
                linewidth=1.1,
                label="Igual tiempo",
            )
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlabel("Tiempo Hungarian [ms]")
        axis.set_ylabel("Tiempo MILP [ms]")
        _editorial_axis(axis, grid_axis="both")
        _figure_heading(
            figure,
            axis,
            title="Coste computacional pareado",
            subtitle=(
                "La calidad coincide, pero los solvers tienen estructuras "
                "computacionales distintas"
            ),
        )
        _indicator_box(
            axis,
            f"Ratio MILP/Hungarian\nP50: {median_ratio:.1f}×\n"
            f"P05–P95: {p05_ratio:.1f}–{p95_ratio:.1f}×",
            location="upper left",
        )
        axis.legend(loc="lower right", ncols=2)
        _append_indicator(
            indicators,
            figure="comparison_paired_solver_time",
            indicator="median_milp_to_hungarian_solver_ratio",
            value=median_ratio,
            unit="razón",
            interpretation=(
                "Ratio pareado de tiempo; valores mayores que uno indican "
                "mayor tiempo del MILP."
            ),
        )
        _save_editorial_figure(
            figure,
            output_dir / "comparison_paired_solver_time.png",
        )

        # 3. Runtime scaling with separate descriptive fits.
        scaling = datasets["scaling"]
        series = (
            (
                "milp_solver_wall_ns",
                "MILP homogéneo",
                EDITORIAL_COLORS["vermillion"],
                "o",
            ),
            (
                "hungarian_solver_wall_ns",
                "Hungarian",
                EDITORIAL_COLORS["blue"],
                "s",
            ),
        )
        figure, axis = plt.subplots(
            figsize=(7.2, 4.8),
            constrained_layout=True,
        )
        fit_lines: list[str] = []
        for field, label, color, marker in series:
            x, median, lower, upper, counts = _group_quantiles(
                scaling,
                x_field="N",
                y_field=field,
                scale=1e-6,
            )
            axis.fill_between(
                x,
                lower,
                upper,
                color=color,
                alpha=0.10,
                linewidth=0.0,
            )
            axis.plot(
                x,
                median,
                color=color,
                marker=marker,
                markerfacecolor="white",
                markeredgewidth=1.1,
                label=label,
            )
            fit = _power_law_fit(x, median)
            if fit is not None:
                slope, intercept, r_squared = fit
                identifiable = slope > 0.0 and r_squared >= 0.50
                if identifiable:
                    fitted_x = np.geomspace(
                        float(np.min(x)),
                        float(np.max(x)),
                        120,
                    )
                    axis.plot(
                        fitted_x,
                        10.0 ** intercept * fitted_x**slope,
                        color=color,
                        linestyle=":",
                        linewidth=1.0,
                    )
                    fit_lines.append(
                        f"{label}: $\\beta={slope:.2f}$, "
                        f"$R^2={r_squared:.2f}$"
                    )
                else:
                    fit_lines.append(
                        f"{label}: tendencia no identificable "
                        f"($R^2={r_squared:.2f}$)"
                    )
                _append_indicator(
                    indicators,
                    figure="comparison_runtime_scaling",
                    indicator=f"{field}_trend_identifiable",
                    value=identifiable,
                    unit="booleano",
                    interpretation=(
                        f"Exige pendiente positiva y R²≥0.50 para {label}."
                    ),
                )
                _append_indicator(
                    indicators,
                    figure="comparison_runtime_scaling",
                    indicator=f"{field}_r_squared",
                    value=r_squared,
                    unit="adimensional",
                    interpretation=(
                        f"Bondad del ajuste log–log descriptivo de {label}."
                    ),
                )
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlabel("Robots disponibles, $N$")
        axis.set_ylabel("Tiempo del solver [ms]")
        _editorial_axis(axis, grid_axis="both")
        _figure_heading(
            figure,
            axis,
            title="Escalabilidad temporal sobre el mismo problema",
            subtitle=(
                f"Perfil {profile} · P50 y P05–P95; un ajuste solo se dibuja "
                "si tiene pendiente positiva y R²≥0.50"
            ),
        )
        _indicator_box(
            axis,
            "\n".join(fit_lines) if fit_lines else "Ajuste no identificable",
            location="upper left",
        )
        axis.legend(loc="lower right")
        _save_editorial_figure(
            figure,
            output_dir / "comparison_runtime_scaling.png",
        )

        # 4. Feasibility agreement by study.
        milp_rates: list[float] = []
        hungarian_rates: list[float] = []
        disagreements: list[int] = []
        counts: list[int] = []
        for study in study_order:
            selected = [
                record for record in all_records if record["study"] == study
            ]
            counts.append(len(selected))
            milp_rates.append(
                float(np.mean([bool(record["milp_feasible"]) for record in selected]))
            )
            hungarian_rates.append(
                float(
                    np.mean(
                        [bool(record["hungarian_feasible"]) for record in selected]
                    )
                )
            )
            disagreements.append(
                sum(
                    bool(record["milp_feasible"])
                    != bool(record["hungarian_feasible"])
                    for record in selected
                )
            )
        positions = np.arange(len(study_order))
        figure, axis = plt.subplots(
            figsize=(7.2, 4.8),
            constrained_layout=True,
        )
        axis.plot(
            positions,
            milp_rates,
            color=EDITORIAL_COLORS["vermillion"],
            marker="o",
            markerfacecolor="white",
            markeredgewidth=1.2,
            label="MILP homogéneo",
        )
        axis.plot(
            positions,
            hungarian_rates,
            color=EDITORIAL_COLORS["blue"],
            marker="s",
            markerfacecolor="white",
            markeredgewidth=1.2,
            linestyle="--",
            label="Hungarian",
        )
        for index, (rate, disagreement, count) in enumerate(
            zip(milp_rates, disagreements, counts, strict=True)
        ):
            axis.annotate(
                f"{rate:.0%}\nΔ={disagreement}, $n={count}$",
                (index, rate),
                xytext=(0, 8),
                textcoords="offset points",
                ha="center",
                fontsize=6.5,
                color=EDITORIAL_COLORS["muted"],
            )
        axis.set_xticks(
            positions,
            [study_labels[study] for study in study_order],
        )
        axis.set_ylim(-0.02, 1.08)
        axis.yaxis.set_major_formatter(PercentFormatter(1.0))
        axis.set_ylabel("Mundos factibles")
        _editorial_axis(axis)
        total_disagreements = int(sum(disagreements))
        _figure_heading(
            figure,
            axis,
            title="Acuerdo de factibilidad por estudio",
            subtitle=(
                "Δ es el número de mundos donde los métodos discrepan "
                "sobre misión completa"
            ),
        )
        _indicator_box(
            axis,
            f"Desacuerdos totales\n{total_disagreements} de "
            f"{len(all_records)} mundos",
            location="lower right",
        )
        axis.legend(loc="lower left")
        _append_indicator(
            indicators,
            figure="comparison_feasibility_agreement",
            indicator="feasibility_disagreement_count",
            value=total_disagreements,
            unit="mundos",
            interpretation=(
                "Número de mundos con clasificación de factibilidad distinta."
            ),
        )
        _save_editorial_figure(
            figure,
            output_dir / "comparison_feasibility_agreement.png",
        )

    return indicators


MILP_EXCLUDED_FIELDS = {
    "both_feasible",
    "same_capacity_model",
    "milp_to_hungarian_distance_ratio",
    "milp_minus_hungarian_assigned_robots",
    "milp_to_hungarian_solver_ratio",
}


def milp_only_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.items()
        if not key.startswith("hungarian_")
        and key not in MILP_EXCLUDED_FIELDS
    }


def _milp_summary(
    records: list[dict[str, Any]],
    group_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    metric_fields = (
        "milp_feasible",
        "milp_optimal",
        "milp_total_distance",
        "milp_normalized_distance_p95",
        "milp_total_excess_kg",
        "milp_assigned_robot_count",
        "milp_robot_utilization",
        "milp_assignment_distance_gini",
        "milp_solver_wall_ns",
        "milp_total_wall_ns",
        "milp_matrix_bytes",
        "assignment_churn",
        "relative_distance_increase",
        "capacity_cv",
    )
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[tuple(record[field] for field in group_fields)].append(record)
    summaries: list[dict[str, Any]] = []
    for key, group in sorted(
        grouped.items(),
        key=lambda item: tuple(str(value) for value in item[0]),
    ):
        summary = {
            field: value
            for field, value in zip(group_fields, key, strict=True)
        }
        summary["replicates"] = len(group)
        for metric in metric_fields:
            values = _finite(group, metric)
            summary[f"{metric}_mean"] = (
                float(np.mean(values)) if values.size else math.nan
            )
            summary[f"{metric}_std"] = (
                float(np.std(values, ddof=0)) if values.size else math.nan
            )
            summary[f"{metric}_median"] = (
                float(np.median(values)) if values.size else math.nan
            )
            summary[f"{metric}_p05"] = (
                float(np.quantile(values, 0.05)) if values.size else math.nan
            )
            summary[f"{metric}_p95"] = (
                float(np.quantile(values, 0.95)) if values.size else math.nan
            )
        summaries.append(summary)
    return summaries


def _comparison_summary(
    records: list[dict[str, Any]],
    group_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[tuple(record[field] for field in group_fields)].append(record)
    summaries: list[dict[str, Any]] = []
    metrics = (
        "milp_total_distance",
        "hungarian_total_distance",
        "milp_solver_wall_ns",
        "hungarian_solver_wall_ns",
        "milp_to_hungarian_distance_ratio",
        "milp_to_hungarian_solver_ratio",
        "milp_minus_hungarian_assigned_robots",
    )
    for key, group in sorted(
        grouped.items(),
        key=lambda item: tuple(str(value) for value in item[0]),
    ):
        summary = {
            field: value
            for field, value in zip(group_fields, key, strict=True)
        }
        summary["replicates"] = len(group)
        summary["milp_feasibility_rate"] = float(
            np.mean([bool(record["milp_feasible"]) for record in group])
        )
        summary["hungarian_feasibility_rate"] = float(
            np.mean([bool(record["hungarian_feasible"]) for record in group])
        )
        summary["feasibility_disagreements"] = sum(
            bool(record["milp_feasible"])
            != bool(record["hungarian_feasible"])
            for record in group
        )
        for metric in metrics:
            values = _finite(group, metric)
            summary[f"{metric}_median"] = (
                float(np.median(values)) if values.size else math.nan
            )
            summary[f"{metric}_p05"] = (
                float(np.quantile(values, 0.05)) if values.size else math.nan
            )
            summary[f"{metric}_p95"] = (
                float(np.quantile(values, 0.95)) if values.size else math.nan
            )
        summaries.append(summary)
    return summaries


def _write_figure_guide(
    *,
    path: Path,
    title: str,
    introduction: str,
    entries: Sequence[tuple[str, str, str, str]],
) -> None:
    lines = [f"# {title}", "", introduction, ""]
    for file_stem, question, reading, limitation in entries:
        lines.extend(
            [
                f"## `{file_stem}.png` / `{file_stem}.pdf`",
                "",
                f"**Pregunta.** {question}",
                "",
                f"**Cómo leerla.** {reading}",
                "",
                f"**Límite.** {limitation}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_milp_results_report(
    *,
    path: Path,
    records: list[dict[str, Any]],
    profile: str,
) -> None:
    feasible = sum(bool(record["milp_feasible"]) for record in records)
    optimal = sum(bool(record["milp_optimal"]) for record in records)
    solver_ms = _finite(records, "milp_solver_wall_ns") * 1e-6
    by_study: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_study[str(record["study"])].append(record)
    lines = [
        "# SP1.A2 — resultados autónomos del MILP heterogéneo",
        "",
        "Este directorio analiza únicamente el oráculo MILP con capacidades "
        "individuales escalares. No contiene métricas ni curvas Hungarian.",
        "",
        "## Indicadores globales",
        "",
        f"- Perfil de la fuente: `{profile}`.",
        f"- Ejecuciones: {len(records):,}.",
        f"- Misiones factibles: {feasible:,} ({feasible / len(records):.1%}).",
        (
            f"- Optimalidad certificada: {optimal:,} "
            f"({optimal / len(records):.1%})."
        ),
        (
            f"- Tiempo de solver mediano: {float(np.median(solver_ms)):.3f} ms; "
            f"P95: {float(np.quantile(solver_ms, 0.95)):.3f} ms."
            if solver_ms.size
            else "- No hay tiempos finitos."
        ),
        "",
        "## Cobertura por estudio",
        "",
        "| Estudio | Filas | Factibles | Óptimos certificados |",
        "|---|---:|---:|---:|",
    ]
    for study in ("scaling", "balance", "asymmetry", "failures", "capacity"):
        group = by_study[study]
        study_feasible = sum(bool(record["milp_feasible"]) for record in group)
        study_optimal = sum(bool(record["milp_optimal"]) for record in group)
        lines.append(
            f"| {study} | {len(group):,} | "
            f"{study_feasible / len(group):.1%} | "
            f"{study_optimal / len(group):.1%} |"
        )
    lines.extend(
        [
            "",
            "## Interpretación correcta",
            "",
            "La factibilidad indica que todas las cargas reciben capacidad "
            "escalar suficiente con exclusividad robot--carga. No demuestra "
            "soporte mecánico, reparto de wrench, navegación, estabilidad ni "
            "transporte físico.",
            "",
            "Las pendientes y regresiones mostradas en las figuras son "
            "descriptivas del dominio muestreado. No son pruebas de complejidad "
            "asintótica ni resultados confirmatorios.",
            "",
            "La capacidad solicitada informalmente como `q_i` se reporta en la "
            "memoria como `c_i^{pay}`, porque `q_i` ya está reservado para el "
            "estado del robot en la notación canónica.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_controlled_comparison_report(
    *,
    path: Path,
    records: list[dict[str, Any]],
    profile: str,
) -> None:
    same_model = all(
        bool(record["same_capacity_model"])
        and record["capacity_mode"] == "homogeneous"
        for record in records
    )
    both = [record for record in records if bool(record["both_feasible"])]
    differences = np.asarray(
        [
            abs(
                float(record["milp_total_distance"])
                - float(record["hungarian_total_distance"])
            )
            for record in both
        ],
        dtype=np.float64,
    )
    ratios = _finite(records, "milp_to_hungarian_solver_ratio")
    disagreements = sum(
        bool(record["milp_feasible"]) != bool(record["hungarian_feasible"])
        for record in records
    )
    lines = [
        "# SP1.A2 — comparación controlada MILP–Hungarian",
        "",
        "Esta comparación reduce el MILP al mismo problema homogéneo que puede "
        "resolver Hungarian: `c_i^{pay}=q_bar` y cada carga se expande en su "
        "cuota entera de slots. Los mundos, masas, posiciones, semillas y "
        "robots fallados son pareados.",
        "",
        "## Auditoría del diseño",
        "",
        f"- Perfil: `{profile}`.",
        f"- Filas: {len(records):,}.",
        f"- Modelo homogéneo en todas las filas: `{same_model}`.",
        f"- Pares conjuntamente factibles: {len(both):,}.",
        f"- Desacuerdos de factibilidad: {disagreements:,}.",
        (
            "- Error absoluto máximo de distancia: "
            f"{float(np.max(differences)):.3e} m."
            if differences.size
            else "- No hubo pares factibles para auditar la distancia."
        ),
        (
            "- Ratio mediano de tiempo MILP/Hungarian: "
            f"{float(np.median(ratios)):.2f}×."
            if ratios.size
            else "- No hubo ratios de tiempo finitos."
        ),
        "",
        "## Conclusión",
        "",
        "En esta reducción, ambos métodos deben recuperar el mismo coste de "
        "distancia, salvo tolerancia numérica. La comparación relevante es "
        "computacional: el MILP resuelve una formulación binaria general, "
        "mientras Hungarian explota la estructura especializada de asignación. "
        "Por ello, igualdad de calidad no implica igualdad de tiempo.",
        "",
        "Este resultado no autoriza extrapolar Hungarian al problema "
        "heterogéneo: fuera de la reducción homogénea ya no representa las "
        "restricciones de capacidad del MILP.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_directory_manifest(
    *,
    output_dir: Path,
    profile: str,
    scope: str,
    row_counts: dict[str, int],
    audit: dict[str, Any],
    manifest_name: str,
) -> dict[str, Any]:
    manifest_path = output_dir / manifest_name
    artifacts = sorted(
        path
        for path in output_dir.rglob("*")
        if path.is_file() and path != manifest_path
    )
    manifest = {
        "schema_version": 2,
        "profile": profile,
        "scope": scope,
        "row_counts": row_counts,
        "audit": audit,
        "artifacts": {
            path.relative_to(output_dir).as_posix(): {
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in artifacts
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest


def publish_milp_only_results(
    *,
    datasets: dict[str, list[dict[str, Any]]],
    config: MonteCarloConfig,
    output_dir: Path,
    profile: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    filtered = {
        name: [milp_only_record(record) for record in records]
        for name, records in datasets.items()
    }
    group_fields = {
        "scaling": ("M", "requested_delta"),
        "balance": ("M", "requested_delta"),
        "asymmetry": ("M", "quota_mode", "spatial_mode"),
        "failures": ("M", "requested_delta", "treatment"),
        "capacity": ("M", "capacity_mode"),
    }
    all_records = [
        record
        for name in ("scaling", "balance", "asymmetry", "failures", "capacity")
        for record in filtered[name]
    ]
    for name, records in filtered.items():
        write_csv(output_dir / f"mc_{name}.csv", records)
        write_csv(
            output_dir / f"summary_{name}.csv",
            _milp_summary(records, group_fields[name]),
        )
    write_csv(output_dir / "mc_all_runs.csv", all_records)
    (output_dir / "config.json").write_text(
        json.dumps(asdict(config), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    figure_dir = output_dir / "figures"
    indicators = generate_milp_editorial_plots(
        datasets=filtered,
        output_dir=figure_dir,
        profile=profile,
    )
    write_csv(output_dir / "figure_indicators.csv", indicators)
    write_milp_results_report(
        path=output_dir / "MILP_RESULTS_REPORT.md",
        records=all_records,
        profile=profile,
    )
    _write_figure_guide(
        path=output_dir / "FIGURE_GUIDE.md",
        title="Guía de lectura — figuras MILP heterogéneo",
        introduction=(
            "Cada figura responde una pregunta concreta. Las bandas P05–P95 "
            "describen dispersión empírica; los intervalos de Wilson describen "
            "incertidumbre de una proporción binaria."
        ),
        entries=(
            (
                "milp_scaling_solver_time",
                "¿Cómo crece el tiempo observado con el número de robots?",
                "La línea azul es la mediana; la banda es P05–P95. La línea "
                "naranja resume una regresión log–log sobre medianas.",
                "La pendiente no es una cota asintótica y depende del dominio, "
                "hardware, solver y timeout.",
            ),
            (
                "milp_scaling_memory",
                "¿Cuánta memoria explícita requiere el modelo disperso?",
                "Se muestra la matriz de distancia y la matriz CSR de "
                "restricciones, en MiB.",
                "No incluye memoria interna del solver ni del proceso Python.",
            ),
            (
                "milp_balance_feasibility",
                "¿Cómo cambia la factibilidad con déficit o exceso nominal?",
                "Cada punto es una tasa con IC Wilson 95 %. La zona roja "
                "corresponde a `N<M`.",
                "La capacidad heterogénea puede hacer que `N/M` no determine "
                "por sí solo la factibilidad.",
            ),
            (
                "milp_optimality_by_size",
                "¿Con qué frecuencia el solver certifica optimalidad?",
                "Una solución factible sin certificado se representa como no "
                "óptima.",
                "La curva está condicionada por el límite de tiempo del perfil.",
            ),
            (
                "milp_geometry_distance_tail",
                "¿Qué geometrías producen colas de distancia más largas?",
                "Se compara el P95 normalizado mediante cajas, medianas y "
                "puntos de ejecuciones.",
                "Mide asignación estática, no navegación ni colisiones.",
            ),
            (
                "milp_capacity_effects",
                "¿Cómo afecta la heterogeneidad a factibilidad y exceso?",
                "El panel A muestra tasas; el B relaciona CV de capacidad con "
                "capacidad excedente reclutada.",
                "La regresión es descriptiva y la capacidad es escalar.",
            ),
            (
                "milp_capacity_recruitment",
                "¿Cuántos robots recluta el MILP respecto a slots homogéneos?",
                "La línea 1 representa un robot por slot nominal; valores "
                "menores indican sustitución por robots de mayor capacidad.",
                "Menos robots no implica menor energía ni mejor control.",
            ),
            (
                "milp_failure_resilience",
                "¿Qué fallos preservan la misión y cuánto churn producen?",
                "El panel A muestra recuperación completa; el B, cambios de "
                "carga entre robots supervivientes.",
                "Es una reasignación estática posterior al fallo.",
            ),
            (
                "milp_fleet_utilization",
                "¿Qué fracción de la flota recluta cada geometría?",
                "Las cajas muestran la distribución de robots asignados sobre "
                "robots disponibles.",
                "Utilización alta no implica mejor energía, control o reparto "
                "de fuerza.",
            ),
        ),
    )
    return _write_directory_manifest(
        output_dir=output_dir,
        profile=profile,
        scope="MILP heterogeneous only; no Hungarian fields or plots.",
        row_counts={
            **{name: len(records) for name, records in filtered.items()},
            "all": len(all_records),
        },
        audit={
            "contains_hungarian_columns": any(
                key.startswith("hungarian_")
                for record in all_records
                for key in record
            ),
            "png_dpi": 450,
            "vector_pdf_for_each_png": all(
                png.with_suffix(".pdf").is_file()
                for png in figure_dir.glob("*.png")
            ),
        },
        manifest_name="milp_results_manifest.json",
    )


def run_controlled_comparison_studies(
    config: MonteCarloConfig,
) -> dict[str, list[dict[str, Any]]]:
    homogeneous_config = replace(
        config,
        default_capacity_mode="homogeneous",
        capacity_modes=("homogeneous",),
    )
    datasets = {
        "scaling": run_scaling_study(homogeneous_config),
        "balance": run_balance_study(homogeneous_config),
        "asymmetry": run_asymmetry_study(homogeneous_config),
        "failures": run_failure_study(homogeneous_config),
    }
    all_records = [
        record
        for records in datasets.values()
        for record in records
    ]
    if not all(
        record["capacity_mode"] == "homogeneous"
        and bool(record["same_capacity_model"])
        for record in all_records
    ):
        raise RuntimeError(
            "La comparación controlada contiene un modelo no homogéneo."
        )
    return datasets


def publish_controlled_comparison(
    *,
    datasets: dict[str, list[dict[str, Any]]],
    config: MonteCarloConfig,
    output_dir: Path,
    profile: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    group_fields = {
        "scaling": ("M", "requested_delta"),
        "balance": ("M", "requested_delta"),
        "asymmetry": ("M", "quota_mode", "spatial_mode"),
        "failures": ("M", "requested_delta", "treatment"),
    }
    all_records = [
        record
        for name in ("scaling", "balance", "asymmetry", "failures")
        for record in datasets[name]
    ]
    for name, records in datasets.items():
        write_csv(output_dir / f"mc_{name}.csv", records)
        write_csv(
            output_dir / f"summary_{name}.csv",
            _comparison_summary(records, group_fields[name]),
        )
    write_csv(output_dir / "mc_all_runs.csv", all_records)
    homogeneous_config = replace(
        config,
        default_capacity_mode="homogeneous",
        capacity_modes=("homogeneous",),
    )
    (output_dir / "config.json").write_text(
        json.dumps(asdict(homogeneous_config), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    figure_dir = output_dir / "figures"
    indicators = generate_controlled_comparison_plots(
        datasets=datasets,
        output_dir=figure_dir,
        profile=profile,
    )
    write_csv(output_dir / "figure_indicators.csv", indicators)
    write_controlled_comparison_report(
        path=output_dir / "CONTROLLED_COMPARISON_REPORT.md",
        records=all_records,
        profile=profile,
    )
    write_metric_crosswalk(output_dir / "METRIC_CROSSWALK.md")
    _write_figure_guide(
        path=output_dir / "FIGURE_GUIDE.md",
        title="Guía de lectura — comparación homogénea controlada",
        introduction=(
            "Aquí MILP y Hungarian reciben exactamente el mismo problema. "
            "Las figuras de calidad y factibilidad sí permiten una comparación "
            "algorítmica dentro de esta reducción."
        ),
        entries=(
            (
                "comparison_distance_parity",
                "¿Recuperan ambos métodos el mismo coste de distancia?",
                "La diagonal representa igualdad exacta. La caja indica el "
                "error absoluto máximo.",
                "La equivalencia solo vale para capacidad homogénea y cuotas "
                "enteras reducibles a slots.",
            ),
            (
                "comparison_paired_solver_time",
                "¿Qué método consume más tiempo de solver en el mismo mundo?",
                "Puntos sobre la diagonal indican mayor tiempo MILP; el ratio "
                "P50 resume la diferencia pareada.",
                "Los tiempos dependen de hardware, carga del sistema y versiones.",
            ),
            (
                "comparison_runtime_scaling",
                "¿Cómo evolucionan los tiempos con el tamaño?",
                "Líneas sólidas: medianas; bandas: P05–P95. Una tendencia "
                "log–log solo se dibuja con pendiente positiva y R²≥0.50.",
                "Las pendientes no son complejidad asintótica demostrada.",
            ),
            (
                "comparison_feasibility_agreement",
                "¿Clasifican igual la factibilidad de misión completa?",
                "Las dos series usan las mismas instancias; Δ cuenta desacuerdos.",
                "No evalúa factibilidad mecánica ni transporte.",
            ),
        ),
    )
    jointly_feasible = [
        record for record in all_records if bool(record["both_feasible"])
    ]
    max_distance_error = (
        max(
            abs(
                float(record["milp_total_distance"])
                - float(record["hungarian_total_distance"])
            )
            for record in jointly_feasible
        )
        if jointly_feasible
        else math.nan
    )
    return _write_directory_manifest(
        output_dir=output_dir,
        profile=profile,
        scope=(
            "Controlled homogeneous MILP versus Hungarian on identical worlds."
        ),
        row_counts={
            **{name: len(records) for name, records in datasets.items()},
            "all": len(all_records),
        },
        audit={
            "all_rows_homogeneous": all(
                record["capacity_mode"] == "homogeneous"
                and bool(record["same_capacity_model"])
                for record in all_records
            ),
            "feasibility_disagreements": sum(
                bool(record["milp_feasible"])
                != bool(record["hungarian_feasible"])
                for record in all_records
            ),
            "maximum_absolute_distance_error_m": max_distance_error,
            "png_dpi": 450,
            "vector_pdf_for_each_png": all(
                png.with_suffix(".pdf").is_file()
                for png in figure_dir.glob("*.png")
            ),
        },
        manifest_name="comparison_manifest.json",
    )


def read_existing_milp_datasets(
    source_dir: Path,
) -> dict[str, list[dict[str, Any]]]:
    required = ("scaling", "balance", "asymmetry", "failures", "capacity")
    datasets = {
        name: read_csv_records(source_dir / f"mc_{name}.csv")
        for name in required
    }
    if not all(datasets.values()):
        raise ValueError(f"Fuente incompleta en {source_dir}.")
    return datasets


def publish_existing_separated_results(
    *,
    source_dir: Path,
    output_dir: Path,
    milp_profile: str,
    comparison_profile: str,
) -> dict[str, Any]:
    source_datasets = read_existing_milp_datasets(source_dir)
    milp_config = config_for_profile(milp_profile)
    comparison_config = config_for_profile(comparison_profile)
    milp_manifest = publish_milp_only_results(
        datasets=source_datasets,
        config=milp_config,
        output_dir=output_dir / "milp_results",
        profile=milp_profile,
    )
    comparison_datasets = run_controlled_comparison_studies(
        comparison_config
    )
    comparison_manifest = publish_controlled_comparison(
        datasets=comparison_datasets,
        config=comparison_config,
        output_dir=output_dir / "comparison",
        profile=comparison_profile,
    )
    directories = sorted(
        path.name for path in output_dir.iterdir() if path.is_dir()
    )
    if directories != ["comparison", "milp_results"]:
        raise RuntimeError(
            "La publicación debe contener exactamente las carpetas "
            "'milp_results' y 'comparison'."
        )
    return {
        "milp_results": milp_manifest,
        "comparison": comparison_manifest,
    }


def run_separated_monte_carlo(
    *,
    config: MonteCarloConfig,
    output_dir: Path,
    profile: str,
    comparison_profile: str,
) -> dict[str, Any]:
    heterogeneous = {
        "scaling": run_scaling_study(config),
        "balance": run_balance_study(config),
        "asymmetry": run_asymmetry_study(config),
        "failures": run_failure_study(config),
        "capacity": run_capacity_study(config),
    }
    milp_manifest = publish_milp_only_results(
        datasets=heterogeneous,
        config=config,
        output_dir=output_dir / "milp_results",
        profile=profile,
    )
    comparison_config = config_for_profile(comparison_profile)
    comparison = run_controlled_comparison_studies(comparison_config)
    comparison_manifest = publish_controlled_comparison(
        datasets=comparison,
        config=comparison_config,
        output_dir=output_dir / "comparison",
        profile=comparison_profile,
    )
    return {
        "milp_results": milp_manifest,
        "comparison": comparison_manifest,
    }


def regenerate_separated_publication(
    *,
    output_dir: Path,
    milp_profile: str,
    comparison_profile: str,
) -> dict[str, Any]:
    milp_dir = output_dir / "milp_results"
    comparison_dir = output_dir / "comparison"
    milp_datasets = read_existing_milp_datasets(milp_dir)
    comparison_datasets = {
        name: read_csv_records(comparison_dir / f"mc_{name}.csv")
        for name in ("scaling", "balance", "asymmetry", "failures")
    }
    return {
        "milp_results": publish_milp_only_results(
            datasets=milp_datasets,
            config=config_for_profile(milp_profile),
            output_dir=milp_dir,
            profile=milp_profile,
        ),
        "comparison": publish_controlled_comparison(
            datasets=comparison_datasets,
            config=config_for_profile(comparison_profile),
            output_dir=comparison_dir,
            profile=comparison_profile,
        ),
    }


# ===============================================================
# == Saturation / timeout-censoring audit =======================
# ===============================================================


def saturation_audit_cases(
    config: SaturationAuditConfig,
) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    case_index = 0
    for robot_count in config.fixed_demand_n_values:
        for replicate in range(config.replicates):
            cases.append(
                {
                    "case_index": case_index,
                    "arm": "fixed_demand",
                    "N": robot_count,
                    "M": config.fixed_demand_m,
                    "time_limit_seconds": config.main_timeout_seconds,
                    "replicate": replicate,
                }
            )
            case_index += 1
    for total_slots in config.joint_m_values:
        robot_count = robot_count_from_delta(
            total_slots,
            config.joint_delta,
        )
        for replicate in range(config.replicates):
            cases.append(
                {
                    "case_index": case_index,
                    "arm": "joint_growth",
                    "N": robot_count,
                    "M": total_slots,
                    "time_limit_seconds": config.main_timeout_seconds,
                    "replicate": replicate,
                }
            )
            case_index += 1
    for robot_count in config.timeout_probe_n_values:
        for time_limit_seconds in config.timeout_probe_seconds:
            for replicate in range(config.replicates):
                cases.append(
                    {
                        "case_index": case_index,
                        "arm": "timeout_probe",
                        "N": robot_count,
                        "M": config.fixed_demand_m,
                        "time_limit_seconds": time_limit_seconds,
                        "replicate": replicate,
                    }
                )
                case_index += 1
    return cases


def saturation_case_key(record: dict[str, Any]) -> tuple[str, int, int, float, int]:
    return (
        str(record["arm"]),
        int(record["N"]),
        int(record["M"]),
        float(record["time_limit_seconds"]),
        int(record["replicate"]),
    )


def classify_saturation_outcome(
    *,
    result: MILPResult | None,
    error_message: str,
    call_wall_seconds: float,
    time_limit_seconds: float,
) -> tuple[str, bool]:
    message = error_message.lower()
    status_time_limit = (
        (result is not None and result.status == 1)
        or "status=1" in message
        or "time limit" in message
        or "límite de tiempo" in message
    )
    near_limit_without_certificate = (
        (result is None or not result.optimal)
        and call_wall_seconds >= 0.90 * time_limit_seconds
    )
    censored = bool(status_time_limit or near_limit_without_certificate)
    if result is not None and result.optimal:
        return "optimal_certified", False
    if result is not None and result.feasible and censored:
        return "timeout_with_incumbent", True
    if result is not None and result.feasible:
        return "feasible_uncertified", False
    if censored:
        return "timeout_without_incumbent", True
    if result is None:
        return "no_solution_returned", False
    return "solver_stopped", False


def estimated_sparse_model_bytes(robot_count: int, load_count: int) -> int:
    distance_bytes = robot_count * load_count * 8
    nonzero_count = 3 * robot_count * load_count + load_count
    row_count = robot_count + 2 * load_count
    csr_bytes = nonzero_count * (8 + 4) + (row_count + 1) * 4
    return int(distance_bytes + csr_bytes)


def run_saturation_case(
    *,
    case: dict[str, Any],
    config: SaturationAuditConfig,
) -> dict[str, Any]:
    robot_count = int(case["N"])
    total_slots = int(case["M"])
    replicate = int(case["replicate"])
    arm = str(case["arm"])
    time_limit_seconds = float(case["time_limit_seconds"])
    seed = stable_seed(
        config.base_seed,
        "saturation-audit",
        arm,
        robot_count,
        total_slots,
        time_limit_seconds,
        replicate,
    )
    robots, loads, quotas = generate_paired_world(
        robot_count=robot_count,
        total_slots=total_slots,
        q_bar=config.q_bar,
        mean_quota=config.mean_quota,
        quota_mode=config.quota_mode,
        spatial_mode=config.spatial_mode,
        capacity_mode=config.capacity_mode,
        workspace_width=config.workspace_width,
        workspace_height=config.workspace_height,
        seed=seed,
    )
    load_count = len(loads)
    capacities = np.asarray(
        [robot.capacity for robot in robots],
        dtype=np.float64,
    )
    call_start = time.perf_counter_ns()
    result: MILPResult | None = None
    error_message = ""
    try:
        result = solve_heterogeneous_milp(
            robots,
            loads,
            distance_weight=config.distance_weight,
            excess_weight=config.excess_weight,
            robot_use_weight=config.robot_use_weight,
            time_limit_seconds=time_limit_seconds,
            mip_rel_gap=config.mip_rel_gap,
        )
        validate_result(result, robots, loads)
    except InfeasibleCoalitionError as error:
        error_message = str(error)
    call_wall_seconds = (time.perf_counter_ns() - call_start) / 1e9
    outcome, censored = classify_saturation_outcome(
        result=result,
        error_message=error_message,
        call_wall_seconds=call_wall_seconds,
        time_limit_seconds=time_limit_seconds,
    )
    if result is not None:
        solver_wall_seconds = result.timings.solver_wall_ns / 1e9
        matrix_wall_seconds = result.timings.matrix_wall_ns / 1e9
        model_wall_seconds = result.timings.model_wall_ns / 1e9
        post_wall_seconds = result.timings.post_wall_ns / 1e9
        internal_total_wall_seconds = result.timings.total_wall_ns / 1e9
        observed_time_seconds = solver_wall_seconds
        status = result.status
        message = result.message
        mip_gap = result.mip_gap if result.mip_gap is not None else math.nan
        node_count = (
            result.mip_node_count
            if result.mip_node_count is not None
            else 0
        )
        matrix_bytes = (
            int(result.distance_matrix.nbytes)
            + int(result.diagnostics["constraint_matrix_bytes"])
        )
        assigned_robot_count = len(result.assignments)
        total_distance = result.total_distance
    else:
        solver_wall_seconds = math.nan
        matrix_wall_seconds = math.nan
        model_wall_seconds = math.nan
        post_wall_seconds = math.nan
        internal_total_wall_seconds = math.nan
        observed_time_seconds = call_wall_seconds
        status = 1 if "status=1" in error_message else -1
        message = error_message
        mip_gap = math.nan
        node_count = 0
        matrix_bytes = estimated_sparse_model_bytes(robot_count, load_count)
        assigned_robot_count = 0
        total_distance = math.nan
    total_capacity = float(np.sum(capacities))
    total_demand = float(sum(load.mass for load in loads))
    return {
        "case_index": int(case["case_index"]),
        "arm": arm,
        "replicate": replicate,
        "seed": seed,
        "N": robot_count,
        "K": load_count,
        "M": int(np.sum(quotas)),
        "binary_variable_count": robot_count * load_count,
        "constraint_count": robot_count + 2 * load_count,
        "time_limit_seconds": time_limit_seconds,
        "capacity_mode": config.capacity_mode,
        "capacity_cv": coefficient_of_variation(capacities),
        "total_capacity_kg": total_capacity,
        "total_demand_kg": total_demand,
        "structural_capacity_feasible": (
            total_capacity + 1e-12 >= total_demand
        ),
        "solver_returned_incumbent": result is not None,
        "mission_feasible_observed": (
            bool(result.feasible) if result is not None else False
        ),
        "optimal_certified": (
            bool(result.optimal) if result is not None else False
        ),
        "censored": censored,
        "outcome": outcome,
        "solver_status": status,
        "solver_message": message,
        "mip_gap": mip_gap,
        "mip_node_count": node_count,
        "solver_wall_seconds": solver_wall_seconds,
        "matrix_wall_seconds": matrix_wall_seconds,
        "model_wall_seconds": model_wall_seconds,
        "post_wall_seconds": post_wall_seconds,
        "internal_total_wall_seconds": internal_total_wall_seconds,
        "call_wall_seconds": call_wall_seconds,
        "observed_time_seconds": observed_time_seconds,
        "observed_over_timeout": observed_time_seconds / time_limit_seconds,
        "explicit_model_bytes": matrix_bytes,
        "estimated_explicit_model_bytes": estimated_sparse_model_bytes(
            robot_count,
            load_count,
        ),
        "assigned_robot_count": assigned_robot_count,
        "total_distance": total_distance,
    }


def _saturation_groups(
    records: Iterable[dict[str, Any]],
    *,
    arm: str,
    time_limit_seconds: float | None = None,
) -> list[dict[str, Any]]:
    selected = [
        record
        for record in records
        if record["arm"] == arm
        and (
            time_limit_seconds is None
            or math.isclose(
                float(record["time_limit_seconds"]),
                time_limit_seconds,
            )
        )
    ]
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in selected:
        groups[int(record["N"])].append(record)
    summaries: list[dict[str, Any]] = []
    for robot_count, group in sorted(groups.items()):
        times = _finite(group, "observed_time_seconds")
        summaries.append(
            {
                "N": robot_count,
                "M_median": float(
                    np.median([float(record["M"]) for record in group])
                ),
                "K_median": float(
                    np.median([float(record["K"]) for record in group])
                ),
                "runs": len(group),
                "time_median_seconds": (
                    float(np.median(times)) if times.size else math.nan
                ),
                "time_p05_seconds": (
                    float(np.quantile(times, 0.05))
                    if times.size
                    else math.nan
                ),
                "time_p95_seconds": (
                    float(np.quantile(times, 0.95))
                    if times.size
                    else math.nan
                ),
                "optimality_rate": float(
                    np.mean(
                        [bool(record["optimal_certified"]) for record in group]
                    )
                ),
                "censoring_rate": float(
                    np.mean([bool(record["censored"]) for record in group])
                ),
                "incumbent_rate": float(
                    np.mean(
                        [
                            bool(record["solver_returned_incumbent"])
                            for record in group
                        ]
                    )
                ),
                "binary_variables_median": float(
                    np.median(
                        [
                            float(record["binary_variable_count"])
                            for record in group
                        ]
                    )
                ),
                "explicit_memory_mib_median": float(
                    np.median(
                        [
                            float(record["explicit_model_bytes"])
                            / (1024.0**2)
                            for record in group
                        ]
                    )
                ),
            }
        )
    return summaries


def build_saturation_summary_records(
    *,
    records: list[dict[str, Any]],
    config: SaturationAuditConfig,
) -> list[dict[str, Any]]:
    summary_records: list[dict[str, Any]] = []
    for arm in ("fixed_demand", "joint_growth"):
        for group in _saturation_groups(records, arm=arm):
            summary_records.append(
                {
                    "arm": arm,
                    "time_limit_seconds": config.main_timeout_seconds,
                    **group,
                }
            )
    for time_limit in config.timeout_probe_seconds:
        for group in _saturation_groups(
            records,
            arm="timeout_probe",
            time_limit_seconds=time_limit,
        ):
            summary_records.append(
                {
                    "arm": "timeout_probe",
                    "time_limit_seconds": time_limit,
                    **group,
                }
            )
    return summary_records


def generate_saturation_audit_plots(
    *,
    records: list[dict[str, Any]],
    config: SaturationAuditConfig,
    output_dir: Path,
) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    indicators: list[dict[str, Any]] = []
    arm_specs = (
        (
            "fixed_demand",
            "Demanda fija ($M=120$)",
            EDITORIAL_COLORS["blue"],
        ),
        (
            "joint_growth",
            "Crecimiento conjunto ($\\delta=0.20$)",
            EDITORIAL_COLORS["vermillion"],
        ),
    )
    with mpl.rc_context(EDITORIAL_RC):
        # 1. Observed runtime plus certification/censoring.
        figure, axes = plt.subplots(
            2,
            2,
            figsize=(10.8, 7.2),
            constrained_layout=True,
            sharex="col",
        )
        figure.get_layout_engine().set(rect=(0.0, 0.0, 1.0, 0.88))
        for column, (arm, label, color) in enumerate(arm_specs):
            groups = _saturation_groups(records, arm=arm)
            x = np.asarray([group["N"] for group in groups], dtype=np.float64)
            median = np.asarray(
                [group["time_median_seconds"] for group in groups],
                dtype=np.float64,
            )
            lower = np.asarray(
                [group["time_p05_seconds"] for group in groups],
                dtype=np.float64,
            )
            upper = np.asarray(
                [group["time_p95_seconds"] for group in groups],
                dtype=np.float64,
            )
            top = axes[0, column]
            top.fill_between(
                x,
                lower,
                upper,
                color=color,
                alpha=0.13,
                linewidth=0.0,
                label="P05–P95",
            )
            top.plot(
                x,
                median,
                color=color,
                marker="o",
                markerfacecolor="white",
                markeredgewidth=1.1,
                label="P50 observado",
            )
            top.axhline(
                config.main_timeout_seconds,
                color=EDITORIAL_COLORS["ink"],
                linestyle="--",
                linewidth=1.0,
                label="Timeout principal",
            )
            top.set_xscale("log")
            top.set_yscale("log")
            top.set_ylabel("Tiempo observado [s]")
            top.set_title(f"{chr(65 + column)}  ·  {label}", loc="left")
            _editorial_axis(top, grid_axis="both")
            top.legend(loc="best")

            optimality = np.asarray(
                [group["optimality_rate"] for group in groups],
                dtype=np.float64,
            )
            censoring = np.asarray(
                [group["censoring_rate"] for group in groups],
                dtype=np.float64,
            )
            bottom = axes[1, column]
            bottom.plot(
                x,
                optimality,
                color=EDITORIAL_COLORS["green"],
                marker="o",
                markerfacecolor="white",
                markeredgewidth=1.1,
                label="Optimalidad certificada",
            )
            bottom.plot(
                x,
                censoring,
                color=EDITORIAL_COLORS["vermillion"],
                marker="^",
                markerfacecolor="white",
                markeredgewidth=1.1,
                linestyle="--",
                label="Censura por timeout",
            )
            bottom.set_xscale("log")
            bottom.set_ylim(-0.03, 1.05)
            bottom.yaxis.set_major_formatter(PercentFormatter(1.0))
            bottom.set_xlabel("Robots disponibles, $N$")
            bottom.set_ylabel("Fracción de ejecuciones")
            _editorial_axis(bottom, grid_axis="both")
            bottom.legend(loc="best")
            if groups:
                largest = groups[-1]
                _append_indicator(
                    indicators,
                    figure="saturation_runtime_and_certification",
                    indicator=f"{arm}_largest_n",
                    value=int(largest["N"]),
                    unit="robots",
                    interpretation=f"Mayor tamaño completado en {label}.",
                )
                _append_indicator(
                    indicators,
                    figure="saturation_runtime_and_certification",
                    indicator=f"{arm}_tail_optimality_rate",
                    value=float(largest["optimality_rate"]),
                    unit="proporción",
                    interpretation=(
                        f"Optimalidad en el mayor tamaño de {label}."
                    ),
                )
                _append_indicator(
                    indicators,
                    figure="saturation_runtime_and_certification",
                    indicator=f"{arm}_tail_censoring_rate",
                    value=float(largest["censoring_rate"]),
                    unit="proporción",
                    interpretation=(
                        f"Censura en el mayor tamaño de {label}."
                    ),
                )
        figure.suptitle(
            "¿Saturación real o tiempo censurado?",
            x=0.055,
            y=0.985,
            ha="left",
            fontsize=12,
            fontweight="semibold",
            color=EDITORIAL_COLORS["ink"],
        )
        figure.text(
            0.055,
            0.942,
            (
                "La meseta solo sería escalabilidad útil si la optimalidad "
                "permanece alta y la censura baja"
            ),
            ha="left",
            va="top",
            fontsize=7.5,
            color=EDITORIAL_COLORS["muted"],
        )
        _save_editorial_figure(
            figure,
            output_dir / "saturation_runtime_and_certification.png",
        )

        # 2. Timeout sensitivity probe.
        figure, axes = plt.subplots(
            1,
            2,
            figsize=(10.2, 4.8),
            constrained_layout=True,
        )
        figure.get_layout_engine().set(rect=(0.0, 0.0, 1.0, 0.88))
        timeout_colors = (
            EDITORIAL_COLORS["sky"],
            EDITORIAL_COLORS["blue"],
            EDITORIAL_COLORS["vermillion"],
        )
        timeout_markers = ("s", "o", "^")
        for time_limit, color, marker in zip(
            config.timeout_probe_seconds,
            timeout_colors,
            timeout_markers,
            strict=True,
        ):
            groups = _saturation_groups(
                records,
                arm="timeout_probe",
                time_limit_seconds=time_limit,
            )
            x = np.asarray([group["N"] for group in groups], dtype=np.float64)
            median = np.asarray(
                [group["time_median_seconds"] for group in groups],
                dtype=np.float64,
            )
            lower = np.asarray(
                [group["time_p05_seconds"] for group in groups],
                dtype=np.float64,
            )
            upper = np.asarray(
                [group["time_p95_seconds"] for group in groups],
                dtype=np.float64,
            )
            axes[0].fill_between(
                x,
                lower,
                upper,
                color=color,
                alpha=0.10,
                linewidth=0.0,
            )
            axes[0].plot(
                x,
                median,
                color=color,
                marker=marker,
                markerfacecolor="white",
                markeredgewidth=1.1,
                label=f"Timeout {time_limit:g} s",
            )
            axes[1].plot(
                x,
                [group["optimality_rate"] for group in groups],
                color=color,
                marker=marker,
                markerfacecolor="white",
                markeredgewidth=1.1,
                label=f"Timeout {time_limit:g} s",
            )
            if groups:
                _append_indicator(
                    indicators,
                    figure="saturation_timeout_probe",
                    indicator=f"timeout_{time_limit:g}s_tail_optimality",
                    value=float(groups[-1]["optimality_rate"]),
                    unit="proporción",
                    interpretation=(
                        f"Optimalidad a N={groups[-1]['N']} con límite "
                        f"{time_limit:g} s."
                    ),
                )
        axes[0].set_xscale("log")
        axes[0].set_yscale("log")
        axes[0].set_xlabel("Robots disponibles, $N$")
        axes[0].set_ylabel("Tiempo observado [s]")
        axes[0].set_title("A  ·  La meseta sigue al timeout", loc="left")
        _editorial_axis(axes[0], grid_axis="both")
        axes[0].legend(loc="best")
        axes[1].set_xscale("log")
        axes[1].set_ylim(-0.03, 1.05)
        axes[1].yaxis.set_major_formatter(PercentFormatter(1.0))
        axes[1].set_xlabel("Robots disponibles, $N$")
        axes[1].set_ylabel("Optimalidad certificada")
        axes[1].set_title("B  ·  Certificación al ampliar el presupuesto", loc="left")
        _editorial_axis(axes[1], grid_axis="both")
        axes[1].legend(loc="best")
        figure.suptitle(
            "Sonda de sensibilidad al límite de tiempo",
            x=0.055,
            y=0.985,
            ha="left",
            fontsize=12,
            fontweight="semibold",
            color=EDITORIAL_COLORS["ink"],
        )
        _save_editorial_figure(
            figure,
            output_dir / "saturation_timeout_probe.png",
        )

        # 3. Irreducible growth in variables and explicit memory.
        figure, axes = plt.subplots(
            1,
            2,
            figsize=(10.2, 4.8),
            constrained_layout=True,
        )
        figure.get_layout_engine().set(rect=(0.0, 0.0, 1.0, 0.88))
        for arm, label, color in arm_specs:
            groups = _saturation_groups(records, arm=arm)
            x = np.asarray([group["N"] for group in groups], dtype=np.float64)
            binaries = np.asarray(
                [group["binary_variables_median"] for group in groups],
                dtype=np.float64,
            )
            memory = np.asarray(
                [group["explicit_memory_mib_median"] for group in groups],
                dtype=np.float64,
            )
            marker = "o" if arm == "fixed_demand" else "^"
            axes[0].plot(
                x,
                binaries,
                color=color,
                marker=marker,
                markerfacecolor="white",
                markeredgewidth=1.1,
                label=label,
            )
            axes[1].plot(
                x,
                memory,
                color=color,
                marker=marker,
                markerfacecolor="white",
                markeredgewidth=1.1,
                label=label,
            )
            binary_fit = _power_law_fit(x, binaries)
            memory_fit = _power_law_fit(x, memory)
            if binary_fit is not None:
                _append_indicator(
                    indicators,
                    figure="saturation_model_growth",
                    indicator=f"{arm}_binary_growth_exponent",
                    value=float(binary_fit[0]),
                    unit="adimensional",
                    interpretation=(
                        f"Pendiente log–log de N×K para {label}."
                    ),
                )
            if memory_fit is not None:
                _append_indicator(
                    indicators,
                    figure="saturation_model_growth",
                    indicator=f"{arm}_memory_growth_exponent",
                    value=float(memory_fit[0]),
                    unit="adimensional",
                    interpretation=(
                        f"Pendiente log–log de memoria explícita para {label}."
                    ),
                )
        for axis in axes:
            axis.set_xscale("log")
            axis.set_yscale("log")
            axis.set_xlabel("Robots disponibles, $N$")
            _editorial_axis(axis, grid_axis="both")
            axis.legend(loc="best")
        axes[0].set_ylabel("Variables binarias, $N K$")
        axes[0].set_title("A  ·  Tamaño combinatorio explícito", loc="left")
        axes[1].set_ylabel("Memoria explícita estimada [MiB]")
        axes[1].set_title("B  ·  Datos y restricciones dispersas", loc="left")
        figure.suptitle(
            "El coste de representar el problema no se satura",
            x=0.055,
            y=0.985,
            ha="left",
            fontsize=12,
            fontweight="semibold",
            color=EDITORIAL_COLORS["ink"],
        )
        _save_editorial_figure(
            figure,
            output_dir / "saturation_model_growth.png",
        )

        # 4. Internal phases where an incumbent was returned.
        phase_fields = (
            (
                "matrix_wall_seconds",
                "Distancias",
                EDITORIAL_COLORS["sky"],
                "s",
            ),
            (
                "model_wall_seconds",
                "Ensamblaje",
                EDITORIAL_COLORS["orange"],
                "^",
            ),
            (
                "solver_wall_seconds",
                "Solver",
                EDITORIAL_COLORS["vermillion"],
                "o",
            ),
            (
                "internal_total_wall_seconds",
                "Total interno",
                EDITORIAL_COLORS["ink"],
                "D",
            ),
        )
        figure, axes = plt.subplots(
            1,
            2,
            figsize=(10.2, 4.8),
            constrained_layout=True,
        )
        figure.get_layout_engine().set(rect=(0.0, 0.0, 1.0, 0.88))
        for axis, (arm, label, _) in zip(axes, arm_specs, strict=True):
            arm_records = [
                record
                for record in records
                if record["arm"] == arm
                and bool(record["solver_returned_incumbent"])
            ]
            for field, phase_label, color, marker in phase_fields:
                x, median, lower, upper, _ = _group_quantiles(
                    arm_records,
                    x_field="N",
                    y_field=field,
                )
                if x.size == 0:
                    continue
                axis.plot(
                    x,
                    median,
                    color=color,
                    marker=marker,
                    markerfacecolor="white",
                    markeredgewidth=1.0,
                    label=phase_label,
                )
                if field in {"solver_wall_seconds", "internal_total_wall_seconds"}:
                    axis.fill_between(
                        x,
                        lower,
                        upper,
                        color=color,
                        alpha=0.07,
                        linewidth=0.0,
                    )
            axis.set_xscale("log")
            axis.set_yscale("log")
            axis.set_xlabel("Robots disponibles, $N$")
            axis.set_ylabel("Tiempo [s]")
            axis.set_title(label, loc="left")
            _editorial_axis(axis, grid_axis="both")
            axis.legend(loc="best", ncols=2)
        figure.suptitle(
            "Descomposición del tiempo cuando existe incumbente",
            x=0.055,
            y=0.985,
            ha="left",
            fontsize=12,
            fontweight="semibold",
            color=EDITORIAL_COLORS["ink"],
        )
        _save_editorial_figure(
            figure,
            output_dir / "saturation_phase_costs.png",
        )
    return indicators


def write_saturation_audit_report(
    *,
    path: Path,
    records: list[dict[str, Any]],
    config: SaturationAuditConfig,
) -> None:
    expected = len(saturation_audit_cases(config))
    censored = sum(bool(record["censored"]) for record in records)
    optimal = sum(bool(record["optimal_certified"]) for record in records)
    incumbents = sum(
        bool(record["solver_returned_incumbent"]) for record in records
    )
    maximum_timeout_ratio = max(
        float(record["observed_over_timeout"]) for record in records
    )
    lines = [
        "# SP1.A2 — auditoría de la aparente saturación temporal",
        "",
        "## Veredicto metodológico",
        "",
        "Una línea temporal plana al nivel del timeout no demuestra coste "
        "constante: es una observación censurada. La saturación solo sería "
        "compatible con los datos si el tiempo se estabilizara lejos del "
        "límite, manteniendo factibilidad y optimalidad certificada.",
        "",
        "Además, el modelo explícito contiene `N*K` costes y variables. Con "
        "`K` fijo, leer y construir la instancia cuesta al menos `Omega(N)`; "
        "cuando `K` crece proporcionalmente con `N`, cuesta al menos "
        "`Omega(N^2)`. Por tanto, esta formulación no puede resolver "
        "`N -> infinito` con coste total fijo.",
        "",
        "## Ejecución",
        "",
        f"- Casos completados: {len(records)} de {expected}.",
        f"- Réplicas por celda: {config.replicates}.",
        f"- Soluciones incumbent devueltas: {incumbents} "
        f"({incumbents / len(records):.1%}).",
        f"- Optimalidad certificada: {optimal} ({optimal / len(records):.1%}).",
        f"- Ejecuciones censuradas: {censored} ({censored / len(records):.1%}).",
        f"- Mayor razón tiempo observado/timeout nominal: "
        f"{maximum_timeout_ratio:.2f}.",
        "",
        "## Extremos de los dos brazos",
        "",
        "| Brazo | N máximo | M | K mediana | P50 tiempo [s] | Óptimos | Censura |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, label in (
        ("fixed_demand", "Demanda fija"),
        ("joint_growth", "Crecimiento conjunto"),
    ):
        groups = _saturation_groups(records, arm=arm)
        if not groups:
            continue
        tail = groups[-1]
        lines.append(
            f"| {label} | {tail['N']} | {tail['M_median']:.0f} | "
            f"{tail['K_median']:.0f} | {tail['time_median_seconds']:.3f} | "
            f"{tail['optimality_rate']:.1%} | "
            f"{tail['censoring_rate']:.1%} |"
        )
    lines.extend(
        [
            "",
            "## Crecimiento mínimo de la representación explícita",
            "",
            "| Brazo | Exponente de `N*K` | Exponente de memoria |",
            "|---|---:|---:|",
        ]
    )
    for arm, label in (
        ("fixed_demand", "Demanda fija"),
        ("joint_growth", "Crecimiento conjunto"),
    ):
        groups = _saturation_groups(records, arm=arm)
        x = np.asarray([group["N"] for group in groups], dtype=np.float64)
        binaries = np.asarray(
            [group["binary_variables_median"] for group in groups],
            dtype=np.float64,
        )
        memory = np.asarray(
            [group["explicit_memory_mib_median"] for group in groups],
            dtype=np.float64,
        )
        binary_fit = _power_law_fit(x, binaries)
        memory_fit = _power_law_fit(x, memory)
        if binary_fit is None or memory_fit is None:
            continue
        lines.append(
            f"| {label} | {binary_fit[0]:.3f} | {memory_fit[0]:.3f} |"
        )
    lines.extend(
        [
            "",
            "Estos exponentes describen el tamaño determinista de la "
            "representación, no una regresión de tiempo. No se ajusta una "
            "ley temporal sobre la cola porque está censurada.",
            "",
            "## Sonda completa de timeout",
            "",
            "| N | Timeout [s] | P50 observado [s] | Incumbent | Optimalidad | Censura |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )
    probe_groups = {
        (int(group["N"]), float(time_limit)): group
        for time_limit in config.timeout_probe_seconds
        for group in _saturation_groups(
            records,
            arm="timeout_probe",
            time_limit_seconds=time_limit,
        )
    }
    for robot_count in config.timeout_probe_n_values:
        for time_limit in config.timeout_probe_seconds:
            group = probe_groups.get((robot_count, float(time_limit)))
            if group is None:
                continue
            lines.append(
                f"| {robot_count} | {time_limit:g} | "
                f"{group['time_median_seconds']:.3f} | "
                f"{group['incumbent_rate']:.1%} | "
                f"{group['optimality_rate']:.1%} | "
                f"{group['censoring_rate']:.1%} |"
            )
    short_timeout = float(config.main_timeout_seconds)
    long_timeout = float(max(config.timeout_probe_seconds))
    changed_certification: list[str] = []
    for robot_count in config.timeout_probe_n_values:
        short_group = probe_groups.get((robot_count, short_timeout))
        long_group = probe_groups.get((robot_count, long_timeout))
        if short_group is None or long_group is None:
            continue
        if not math.isclose(
            float(short_group["optimality_rate"]),
            float(long_group["optimality_rate"]),
        ):
            changed_certification.append(
                f"`N={robot_count}` pasa de "
                f"{short_group['optimality_rate']:.1%} a "
                f"{long_group['optimality_rate']:.1%} de optimalidad "
                "certificada"
            )
    probe_conclusion = ""
    if changed_certification:
        probe_conclusion = (
            "Al aumentar el presupuesto de "
            f"{short_timeout:g} a {long_timeout:g} s, "
            + " y ".join(changed_certification)
            + ". El cambio de régimen con el timeout demuestra que la "
            f"meseta de {short_timeout:g} s no es coste fijo."
        )
    largest_probe_n = max(config.timeout_probe_n_values)
    largest_short = probe_groups.get((largest_probe_n, short_timeout))
    largest_long = probe_groups.get((largest_probe_n, long_timeout))
    if largest_short is not None and largest_long is not None:
        probe_conclusion += (
            f" En `N={largest_probe_n}`, el límite de {long_timeout:g} s "
            f"eleva la tasa de incumbent de "
            f"{largest_short['incumbent_rate']:.1%} a "
            f"{largest_long['incumbent_rate']:.1%}, aunque la optimalidad "
            f"permanece en {largest_long['optimality_rate']:.1%}."
        )
    lines.extend(
        [
            "",
            probe_conclusion,
            "",
            "## Cómo interpretar las figuras",
            "",
            "- `saturation_runtime_and_certification`: tiempo, optimalidad y "
            "censura deben leerse conjuntamente.",
            "- `saturation_timeout_probe`: si la meseta se desplaza al cambiar "
            "2/5/20 s, es una frontera impuesta por el presupuesto.",
            "- `saturation_model_growth`: muestra que variables y memoria siguen "
            "creciendo aunque el solver parezca plano.",
            "- `saturation_phase_costs`: separa distancias, ensamblaje, solver y "
            "tiempo total en casos con incumbente.",
            "",
            "## Limitaciones",
            "",
            "Esta es una auditoría piloto con tres semillas. Los tiempos "
            "dependen de hardware, carga del sistema, SciPy/HiGHS, presolve y "
            "timeout. No constituyen una prueba asintótica.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run_saturation_audit(
    *,
    output_dir: Path,
    config: SaturationAuditConfig | None = None,
) -> dict[str, Any]:
    actual_config = config or SaturationAuditConfig()
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "saturation_runs.csv"
    existing = (
        read_csv_records(csv_path)
        if csv_path.is_file()
        else []
    )
    completed_keys = {saturation_case_key(record) for record in existing}
    records = list(existing)
    cases = saturation_audit_cases(actual_config)
    for position, case in enumerate(cases, start=1):
        key = saturation_case_key(case)
        if key in completed_keys:
            continue
        print(
            f"[saturation {position}/{len(cases)}] "
            f"arm={case['arm']} N={case['N']} M={case['M']} "
            f"timeout={case['time_limit_seconds']:g}s "
            f"rep={case['replicate']}"
        )
        record = run_saturation_case(case=case, config=actual_config)
        records.append(record)
        completed_keys.add(key)
        records.sort(key=lambda item: int(item["case_index"]))
        write_csv(csv_path, records)
        print(
            f"  -> {record['outcome']}; "
            f"t={record['observed_time_seconds']:.3f}s; "
            f"optimal={record['optimal_certified']}; "
            f"censored={record['censored']}"
        )
    config_path = output_dir / "config.json"
    config_path.write_text(
        json.dumps(asdict(actual_config), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    summary_records = build_saturation_summary_records(
        records=records,
        config=actual_config,
    )
    write_csv(output_dir / "saturation_summary.csv", summary_records)
    figure_dir = output_dir / "figures"
    indicators = generate_saturation_audit_plots(
        records=records,
        config=actual_config,
        output_dir=figure_dir,
    )
    write_csv(output_dir / "figure_indicators.csv", indicators)
    write_saturation_audit_report(
        path=output_dir / "SATURATION_AUDIT_REPORT.md",
        records=records,
        config=actual_config,
    )
    unique_keys = {saturation_case_key(record) for record in records}
    return _write_directory_manifest(
        output_dir=output_dir,
        profile="saturation-audit",
        scope=(
            "Heterogeneous MILP scaling with explicit timeout-censoring audit."
        ),
        row_counts={
            "completed": len(records),
            "expected": len(cases),
            "fixed_demand": sum(
                record["arm"] == "fixed_demand" for record in records
            ),
            "joint_growth": sum(
                record["arm"] == "joint_growth" for record in records
            ),
            "timeout_probe": sum(
                record["arm"] == "timeout_probe" for record in records
            ),
        },
        audit={
            "unique_case_keys": len(unique_keys) == len(records),
            "complete": len(records) == len(cases),
            "maximum_n": max(int(record["N"]) for record in records),
            "censored_count": sum(
                bool(record["censored"]) for record in records
            ),
            "optimal_count": sum(
                bool(record["optimal_certified"]) for record in records
            ),
            "png_dpi": 450,
            "vector_pdf_for_each_png": all(
                png.with_suffix(".pdf").is_file()
                for png in figure_dir.glob("*.png")
            ),
        },
        manifest_name="saturation_audit_manifest.json",
    )


# ===============================================================
# == Demonstration ==============================================
# ===============================================================


def run_demo(output_dir: Path, show: bool) -> MILPResult:
    # Same geometry as SP1.A1, but heterogeneous capacities.
    robots = [
        Robot(id="R1", x=0.0, y=0.0, capacity=1.0),
        Robot(id="R2", x=1.0, y=1.0, capacity=2.0),
        Robot(id="R3", x=2.0, y=0.5, capacity=5.0),
        Robot(id="R4", x=8.0, y=1.0, capacity=5.0),
        Robot(id="R5", x=7.0, y=3.0, capacity=3.0),
        Robot(id="R6", x=5.5, y=5.0, capacity=5.0),
        Robot(id="R7", x=2.5, y=5.5, capacity=6.0),
        Robot(id="R8", x=9.0, y=6.0, capacity=10.0),
    ]

    loads = [
        Load(id="L1", x=0.5, y=0.2, mass=5.0),
        Load(id="L2", x=7.5, y=2.0, mass=8.0),
        Load(id="L3", x=4.0, y=5.0, mass=11.0),
    ]

    result = solve_heterogeneous_milp(
        robots=robots,
        loads=loads,
        distance_weight=1.0,
        excess_weight=0.25,
        robot_use_weight=1e-3,
        mip_rel_gap=0.0,
    )
    validate_result(result, robots, loads)
    print_result(result)
    print_distance_matrix(robots, loads, result)
    plot_milp_assignment(
        robots=robots,
        loads=loads,
        result=result,
        output_path=output_dir / "sp1_a2_milp.png",
        show=show,
    )
    return result


# ===============================================================
# == CLI ========================================================
# ===============================================================


def parse_legacy_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "SP1.A2: oráculo MILP centralizado para coaliciones heterogéneas "
            "con capacidades indivisibles y cargas obligatorias."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("sp1_a2_results"),
    )
    parser.add_argument("--show", action="store_true")
    return parser.parse_args()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "SP1.A2: MILP centralizado para coaliciones con capacidades "
            "heterogéneas y comparación homogénea controlada con Hungarian."
        )
    )
    parser.add_argument(
        "--mode",
        choices=(
            "demo",
            "montecarlo",
            "publish-existing",
            "saturation",
            "plots",
            "all",
        ),
        default="all",
    )
    parser.add_argument(
        "--profile",
        choices=("smoke", "quick", "full"),
        default="quick",
    )
    parser.add_argument(
        "--comparison-profile",
        choices=("smoke", "quick", "full"),
        default="smoke",
        help=(
            "Perfil independiente para la comparación homogénea. "
            "El valor por defecto limita el coste del oráculo MILP."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("scripts/results/sp1_a2_milp_revised"),
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("scripts/results/sp1_a2_milp"),
        help=(
            "Campaña combinada histórica usada por --mode publish-existing."
        ),
    )
    show_group = parser.add_mutually_exclusive_group()
    show_group.add_argument("--show", dest="show", action="store_true")
    show_group.add_argument("--no-show", dest="show", action="store_false")
    parser.set_defaults(show=False)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.mode == "saturation":
        manifest = run_saturation_audit(
            output_dir=(
                args.output_dir
                / "milp_results"
                / "saturation_audit"
            ),
        )
        print(
            "Auditoría de saturación completada: "
            f"{manifest['row_counts']['completed']}/"
            f"{manifest['row_counts']['expected']} casos en "
            f"{(args.output_dir / 'milp_results' / 'saturation_audit').resolve()}"
        )
        return
    if args.mode == "publish-existing":
        package = publish_existing_separated_results(
            source_dir=args.source_dir,
            output_dir=args.output_dir,
            milp_profile=args.profile,
            comparison_profile=args.comparison_profile,
        )
        print(
            "Publicación separada completada: "
            f"{package['milp_results']['row_counts']['all']} filas MILP y "
            f"{package['comparison']['row_counts']['all']} filas comparativas "
            f"en {args.output_dir.resolve()}"
        )
        return
    if args.mode in {"montecarlo", "all"}:
        run_separated_monte_carlo(
            config=config_for_profile(args.profile),
            output_dir=args.output_dir,
            profile=args.profile,
            comparison_profile=args.comparison_profile,
        )
    if args.mode == "plots":
        regenerate_separated_publication(
            output_dir=args.output_dir,
            milp_profile=args.profile,
            comparison_profile=args.comparison_profile,
        )
    if args.mode in {"demo", "all"}:
        run_demo(
            output_dir=args.output_dir / "milp_results" / "demo",
            show=args.show,
        )


if __name__ == "__main__":
    main()

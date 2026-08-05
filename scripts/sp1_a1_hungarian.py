from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from math import ceil
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Ellipse, Rectangle, Wedge
from numpy.typing import NDArray
from scipy.optimize import linear_sum_assignment


FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]

GEOMETRY_NAMES = (
    "uniform",
    "clustered",
    "separated",
    "ring",
    "corridor",
)
CLUSTER_CENTER_FRACTIONS = ((0.25, 0.30), (0.75, 0.70))
CLUSTER_STD_FRACTIONS = (0.07, 0.07)
SEPARATED_ROBOT_X_FRACTION = (0.00, 0.35)
SEPARATED_LOAD_X_FRACTION = (0.65, 1.00)
RING_ROBOT_RADIAL_FRACTION = (0.36, 0.48)
RING_LOAD_RADIAL_FRACTION = (0.04, 0.22)
CORRIDOR_CENTER_Y_FRACTION = 0.50
CORRIDOR_ROBOT_STD_FRACTION = 0.04
CORRIDOR_LOAD_STD_FRACTION = 0.08


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
        """Posición cartesiana de la entidad."""
        return np.array([self.x, self.y], dtype=np.float64)


@dataclass(frozen=True)
class Robot(PositionedEntity):
    capacity: float = 1.0
    battery: float = 100.0
    responding: bool = True


@dataclass(frozen=True)
class Load(PositionedEntity):
    mass: float = 1.0


@dataclass(frozen=True)
class Slot:
    """Plaza individual de una carga."""

    slot_id: str
    load_id: str
    position: FloatArray


@dataclass(frozen=True)
class Assignment:
    robot_id: str
    slot_id: str
    load_id: str
    cost: float


@dataclass(frozen=True)
class SolverTimings:
    slots_wall_ns: int
    matrix_wall_ns: int
    solver_wall_ns: int
    post_wall_ns: int
    total_wall_ns: int
    total_cpu_ns: int


@dataclass(frozen=True)
class HungarianResult:
    assignments: list[Assignment]
    coalitions: dict[str, list[str]]
    idle_robots: list[str]
    total_cost: float
    required_cardinality: dict[str, int]
    recruited_capacity: dict[str, float]
    excess_capacity: dict[str, float]
    cost_matrix: FloatArray
    slots: list[Slot]
    feasible: bool
    coverage: float
    missing_slots: int
    timings: SolverTimings


@dataclass(frozen=True)
class CommunicationStats:
    logical_messages: int
    communication_bytes: int
    communication_rounds: int
    retry_messages: int
    nonresponding_count: int


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
    max_retries: int


# ===============================================================
# == Model utilities ============================================
# ===============================================================

def required_robot_count(load: Load, q_bar: float) -> int:
    """Calcula n_k = ceil(mass_k / q_bar)."""
    if q_bar <= 0:
        raise ValueError("q_bar debe ser mayor que cero.")
    if load.mass <= 0:
        raise ValueError(
            f"La masa de la carga {load.id} debe ser mayor que cero."
        )
    return ceil(load.mass / q_bar)


def build_slots(loads: list[Load], q_bar: float) -> list[Slot]:
    """Convierte cada carga k en n_k slots intercambiables."""
    slots: list[Slot] = []
    for load in loads:
        k_required = required_robot_count(load, q_bar)
        for slot_number in range(1, k_required + 1):
            slots.append(
                Slot(
                    slot_id=f"{load.id}_slot_{slot_number}",
                    load_id=load.id,
                    position=load.position,
                )
            )
    return slots


def build_cost_matrix(
    robots: list[Robot],
    slots: list[Slot],
) -> FloatArray:
    """
    Construye C[i,s] = ||p_i - p_s||_2.

    La implementación vectorizada reduce el overhead de Python y deja que la
    campaña mida principalmente el coste real de NumPy/SciPy.
    """
    robot_positions = np.array(
        [[robot.x, robot.y] for robot in robots], dtype=np.float64
    )
    slot_positions = np.array(
        [slot.position for slot in slots], dtype=np.float64
    )

    differences = robot_positions[:, np.newaxis, :] - slot_positions[np.newaxis, :, :]
    return np.linalg.norm(differences, axis=2)


def validate_scenario(
    robots: list[Robot],
    loads: list[Load],
    q_bar: float,
) -> None:
    if not robots:
        raise ValueError("Debe existir al menos un robot.")
    if not loads:
        raise ValueError("Debe existir al menos una carga.")
    if q_bar <= 0:
        raise ValueError("q_bar debe ser mayor que cero.")

    robot_ids = [robot.id for robot in robots]
    load_ids = [load.id for load in loads]

    if len(set(robot_ids)) != len(robot_ids):
        raise ValueError("Los identificadores de los robots deben ser únicos.")
    if len(set(load_ids)) != len(load_ids):
        raise ValueError("Los identificadores de las cargas deben ser únicos.")

    for robot in robots:
        if robot.capacity <= 0:
            raise ValueError(
                f"La capacidad del robot {robot.id} debe ser positiva."
            )
        if not np.isclose(robot.capacity, q_bar):
            raise ValueError(
                "SP1.A1 supone robots homogéneos. "
                f"El robot {robot.id} tiene capacidad {robot.capacity}, "
                f"pero q_bar={q_bar}."
            )

    for load in loads:
        if load.mass <= 0:
            raise ValueError(
                f"La masa de la carga {load.id} debe ser positiva."
            )


# ===============================================================
# == Hungarian solver ===========================================
# ===============================================================

def solve_hungarian(
    robots: list[Robot],
    loads: list[Load],
    q_bar: float,
    *,
    allow_partial: bool = False,
) -> HungarianResult:
    """
    Resuelve SP1.A1 por expansión en slots y asignación lineal.

    Si N < M:
      - allow_partial=False: se rechaza la instancia.
      - allow_partial=True: se calcula la mejor asociación parcial únicamente
        para medir cobertura; feasible=False.
    """
    total_wall_start = time.perf_counter_ns()
    total_cpu_start = time.process_time_ns()

    validate_scenario(robots=robots, loads=loads, q_bar=q_bar)

    phase_start = time.perf_counter_ns()
    slots = build_slots(loads=loads, q_bar=q_bar)
    slots_wall_ns = time.perf_counter_ns() - phase_start

    robot_count = len(robots)
    slot_count = len(slots)

    if robot_count < slot_count and not allow_partial:
        raise ValueError(
            "La instancia es infactible: "
            f"hay {robot_count} robots, pero las cargas necesitan "
            f"{slot_count} robots."
        )

    phase_start = time.perf_counter_ns()
    cost_matrix = build_cost_matrix(robots=robots, slots=slots)
    matrix_wall_ns = time.perf_counter_ns() - phase_start

    phase_start = time.perf_counter_ns()
    robot_indices, slot_indices = linear_sum_assignment(cost_matrix)
    solver_wall_ns = time.perf_counter_ns() - phase_start

    phase_start = time.perf_counter_ns()

    assignments: list[Assignment] = []
    coalitions: dict[str, list[str]] = {load.id: [] for load in loads}
    assigned_robot_indices: set[int] = set()
    total_cost = 0.0

    for robot_index, slot_index in zip(
        robot_indices,
        slot_indices,
        strict=True,
    ):
        robot = robots[int(robot_index)]
        slot = slots[int(slot_index)]
        cost = float(cost_matrix[int(robot_index), int(slot_index)])

        assignments.append(
            Assignment(
                robot_id=robot.id,
                slot_id=slot.slot_id,
                load_id=slot.load_id,
                cost=cost,
            )
        )
        coalitions[slot.load_id].append(robot.id)
        assigned_robot_indices.add(int(robot_index))
        total_cost += cost

    idle_robots = [
        robot.id
        for robot_index, robot in enumerate(robots)
        if robot_index not in assigned_robot_indices
    ]

    required_cardinality = {
        load.id: required_robot_count(load, q_bar)
        for load in loads
    }
    recruited_capacity = {
        load_id: len(robot_ids) * q_bar
        for load_id, robot_ids in coalitions.items()
    }
    load_by_id = {load.id: load for load in loads}
    excess_capacity = {
        load_id: recruited_capacity[load_id] - load_by_id[load_id].mass
        for load_id in coalitions
    }

    assigned_slot_count = len(assignments)
    missing_slots = max(0, slot_count - assigned_slot_count)
    coverage = assigned_slot_count / slot_count
    feasible = missing_slots == 0

    post_wall_ns = time.perf_counter_ns() - phase_start
    total_wall_ns = time.perf_counter_ns() - total_wall_start
    total_cpu_ns = time.process_time_ns() - total_cpu_start

    return HungarianResult(
        assignments=assignments,
        coalitions=coalitions,
        idle_robots=idle_robots,
        total_cost=total_cost,
        required_cardinality=required_cardinality,
        recruited_capacity=recruited_capacity,
        excess_capacity=excess_capacity,
        cost_matrix=cost_matrix,
        slots=slots,
        feasible=feasible,
        coverage=coverage,
        missing_slots=missing_slots,
        timings=SolverTimings(
            slots_wall_ns=slots_wall_ns,
            matrix_wall_ns=matrix_wall_ns,
            solver_wall_ns=solver_wall_ns,
            post_wall_ns=post_wall_ns,
            total_wall_ns=total_wall_ns,
            total_cpu_ns=total_cpu_ns,
        ),
    )


def validate_result(
    result: HungarianResult,
    robots: list[Robot],
    loads: list[Load],
    q_bar: float,
) -> None:
    """Valida únicamente una solución completa y factible."""
    if not result.feasible:
        raise RuntimeError(
            "No puede validarse como solución completa una asignación parcial."
        )

    assigned_robot_ids = [assignment.robot_id for assignment in result.assignments]
    assigned_slot_ids = [assignment.slot_id for assignment in result.assignments]

    if len(assigned_robot_ids) != len(set(assigned_robot_ids)):
        raise RuntimeError("Un robot fue asignado más de una vez.")
    if len(assigned_slot_ids) != len(set(assigned_slot_ids)):
        raise RuntimeError("Un slot fue asignado más de una vez.")
    if len(assigned_slot_ids) != len(result.slots):
        raise RuntimeError("No todos los slots fueron ocupados.")

    load_by_id = {load.id: load for load in loads}
    for load_id, robot_ids in result.coalitions.items():
        required = result.required_cardinality[load_id]
        if len(robot_ids) != required:
            raise RuntimeError(
                f"La carga {load_id} recibió {len(robot_ids)} robots, "
                f"pero necesita {required}."
            )

        recruited = result.recruited_capacity[load_id]
        mass = load_by_id[load_id].mass
        excess = result.excess_capacity[load_id]

        if recruited < mass:
            raise RuntimeError(f"La coalición de {load_id} no cubre su masa.")
        if not (0 <= excess < q_bar):
            raise RuntimeError(
                f"El exceso de capacidad de {load_id} es inválido: {excess}."
            )

    all_robot_ids = {robot.id for robot in robots}
    classified_robot_ids = set(assigned_robot_ids) | set(result.idle_robots)
    if all_robot_ids != classified_robot_ids:
        raise RuntimeError(
            "Hay robots que no quedaron asignados ni libres."
        )


# ===============================================================
# == Demo printing and plotting =================================
# ===============================================================

def print_cost_matrix(robots: list[Robot], result: HungarianResult) -> None:
    print("\nMATRIZ DE COSTES")
    print("-" * 90)

    first_column_width = 8
    column_width = 14
    header = "Robot".ljust(first_column_width)
    for slot in result.slots:
        header += slot.slot_id.rjust(column_width)
    print(header)

    for robot_index, robot in enumerate(robots):
        row = robot.id.ljust(first_column_width)
        for cost in result.cost_matrix[robot_index]:
            row += f"{cost:.3f}".rjust(column_width)
        print(row)


def print_result(result: HungarianResult) -> None:
    print("\n" + "=" * 60)
    print("SP1.A1 — RESULTADO HUNGARIAN")
    print("=" * 60)

    print("\nAsignaciones robot-slot:")
    for assignment in result.assignments:
        print(
            f"  {assignment.robot_id:>2} -> "
            f"{assignment.slot_id:<12} | "
            f"carga={assignment.load_id} | "
            f"coste={assignment.cost:.3f} m"
        )

    print("\nCoaliciones:")
    for load_id, robot_ids in result.coalitions.items():
        required = result.required_cardinality[load_id]
        capacity = result.recruited_capacity[load_id]
        excess = result.excess_capacity[load_id]
        print(
            f"  {load_id}: {robot_ids} | "
            f"cardinalidad={len(robot_ids)}/{required} | "
            f"capacidad={capacity:.1f} kg | "
            f"exceso={excess:.1f} kg"
        )

    print(f"\nRobots libres: {result.idle_robots}")
    print(f"Factible: {result.feasible}")
    print(f"Cobertura: {result.coverage:.3f}")
    print(f"Coste total: {result.total_cost:.6f} m")


def plot_hungarian_assignment(
    robots: list[Robot],
    loads: list[Load],
    result: HungarianResult,
    output_path: str | Path | None = "sp1_a1_hungarian.png",
    show: bool = True,
) -> None:
    figure, axis = plt.subplots(figsize=(12, 9))

    robot_x = [robot.x for robot in robots]
    robot_y = [robot.y for robot in robots]
    load_x = [load.x for load in loads]
    load_y = [load.y for load in loads]

    axis.scatter(
        robot_x,
        robot_y,
        marker="o",
        s=70,
        color="tab:blue",
        label="Robots",
        zorder=3,
    )
    axis.scatter(
        load_x,
        load_y,
        marker="X",
        s=170,
        color="tab:orange",
        label="Loads",
        zorder=4,
    )

    robot_by_id = {robot.id: robot for robot in robots}
    load_by_id = {load.id: load for load in loads}
    color_map = plt.get_cmap("tab10")

    for assignment_index, assignment in enumerate(result.assignments):
        robot = robot_by_id[assignment.robot_id]
        load = load_by_id[assignment.load_id]
        axis.plot(
            [robot.x, load.x],
            [robot.y, load.y],
            linestyle="--",
            linewidth=1.6,
            color=color_map(assignment_index % 10),
            zorder=2,
        )

    for robot in robots:
        axis.annotate(
            robot.id,
            xy=(robot.x, robot.y),
            xytext=(0, 4),
            textcoords="offset points",
            fontsize=12,
            ha="left",
            va="center",
            zorder=5,
        )

    for load in loads:
        axis.annotate(
            f"{load.id}\n{load.mass:g} kg",
            xy=(load.x, load.y),
            xytext=(2, 12),
            textcoords="offset points",
            fontsize=12,
            ha="left",
            va="center",
            zorder=5,
        )

    axis.set_title(
        "SP1.A1 — Homogeneous coalition assignment by Hungarian",
        fontsize=16,
        pad=10,
    )
    axis.set_xlabel("x [m]", fontsize=13)
    axis.set_ylabel("y [m]", fontsize=13)
    axis.grid(visible=True, linestyle="-", linewidth=0.8, alpha=0.30)
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
# == Scenario generation for Monte Carlo ========================
# ===============================================================

def stable_seed(base_seed: int, *parts: object) -> int:
    payload = "|".join([str(base_seed), *(str(part) for part in parts)])
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little") % (2**32)


def robot_count_from_delta(total_slots: int, delta: float) -> int:
    """
    Inversa de delta = (N-M)/(N+M):

        N = M (1+delta)/(1-delta)
    """
    if not (-1.0 < delta < 1.0):
        raise ValueError("delta debe estar estrictamente entre -1 y 1.")
    return max(1, int(round(total_slots * (1.0 + delta) / (1.0 - delta))))


def balance_delta(robot_count: int, slot_count: int) -> float:
    return (robot_count - slot_count) / (robot_count + slot_count)


def coefficient_of_variation(values: Sequence[float] | FloatArray | IntArray) -> float:
    array = np.asarray(values, dtype=np.float64)
    mean = float(np.mean(array))
    if mean == 0.0:
        return 0.0
    return float(np.std(array, ddof=0) / mean)


def generate_quota_vector(
    total_slots: int,
    load_count: int,
    mode: str,
    rng: np.random.Generator,
) -> IntArray:
    """Genera cuotas positivas que suman exactamente M."""
    if total_slots <= 0:
        raise ValueError("total_slots debe ser positivo.")
    if not (1 <= load_count <= total_slots):
        raise ValueError("load_count debe satisfacer 1 <= K <= M.")

    quotas = np.ones(load_count, dtype=np.int64)
    remaining = total_slots - load_count

    if remaining == 0:
        return quotas

    if mode == "symmetric":
        quotient, remainder = divmod(remaining, load_count)
        quotas += quotient
        if remainder > 0:
            selected = rng.permutation(load_count)[:remainder]
            quotas[selected] += 1
        return quotas

    if mode == "low":
        alpha = 10.0
    elif mode == "moderate":
        alpha = 3.0
    elif mode == "high":
        alpha = 0.30
    elif mode == "extreme":
        alpha = 0.08
    else:
        raise ValueError(f"Modo de cuotas desconocido: {mode}")

    weights = rng.dirichlet(np.full(load_count, alpha, dtype=np.float64))
    quotas += rng.multinomial(remaining, weights).astype(np.int64)
    return quotas


def generate_positions(
    count: int,
    *,
    role: str,
    spatial_mode: str,
    workspace_width: float,
    workspace_height: float,
    rng: np.random.Generator,
) -> FloatArray:
    if count <= 0:
        return np.empty((0, 2), dtype=np.float64)

    if spatial_mode == "uniform":
        x = rng.uniform(0.0, workspace_width, size=count)
        y = rng.uniform(0.0, workspace_height, size=count)
        return np.column_stack((x, y)).astype(np.float64)

    if spatial_mode == "clustered":
        if role == "robot":
            x = rng.uniform(0.0, workspace_width, size=count)
            y = rng.uniform(0.0, workspace_height, size=count)
            return np.column_stack((x, y)).astype(np.float64)

        centers = np.array(
            [
                [
                    fraction_x * workspace_width,
                    fraction_y * workspace_height,
                ]
                for fraction_x, fraction_y in CLUSTER_CENTER_FRACTIONS
            ],
            dtype=np.float64,
        )
        center_indices = rng.integers(0, len(centers), size=count)
        noise = rng.normal(
            loc=0.0,
            scale=np.array(
                [
                    CLUSTER_STD_FRACTIONS[0] * workspace_width,
                    CLUSTER_STD_FRACTIONS[1] * workspace_height,
                ],
                dtype=np.float64,
            ),
            size=(count, 2),
        )
        points = centers[center_indices] + noise
        points[:, 0] = np.clip(points[:, 0], 0.0, workspace_width)
        points[:, 1] = np.clip(points[:, 1], 0.0, workspace_height)
        return points.astype(np.float64)

    if spatial_mode == "separated":
        if role == "robot":
            low, high = SEPARATED_ROBOT_X_FRACTION
        else:
            low, high = SEPARATED_LOAD_X_FRACTION
        x = rng.uniform(low * workspace_width, high * workspace_width, size=count)
        y = rng.uniform(0.0, workspace_height, size=count)
        return np.column_stack((x, y)).astype(np.float64)

    if spatial_mode == "ring":
        center = np.array(
            [0.5 * workspace_width, 0.5 * workspace_height],
            dtype=np.float64,
        )
        angles = rng.uniform(0.0, 2.0 * math.pi, size=count)
        if role == "robot":
            radial_range = RING_ROBOT_RADIAL_FRACTION
        else:
            radial_range = RING_LOAD_RADIAL_FRACTION
        radial_fraction = rng.uniform(*radial_range, size=count)
        radii = radial_fraction * min(workspace_width, workspace_height)
        points = np.column_stack(
            (
                center[0] + radii * np.cos(angles),
                center[1] + radii * np.sin(angles),
            )
        )
        points[:, 0] = np.clip(points[:, 0], 0.0, workspace_width)
        points[:, 1] = np.clip(points[:, 1], 0.0, workspace_height)
        return points.astype(np.float64)

    if spatial_mode == "corridor":
        x = rng.uniform(0.0, workspace_width, size=count)
        center_y = CORRIDOR_CENTER_Y_FRACTION * workspace_height
        spread = (
            CORRIDOR_ROBOT_STD_FRACTION
            if role == "robot"
            else CORRIDOR_LOAD_STD_FRACTION
        )
        y = rng.normal(center_y, spread * workspace_height, size=count)
        y = np.clip(y, 0.0, workspace_height)
        return np.column_stack((x, y)).astype(np.float64)

    raise ValueError(f"Modo espacial desconocido: {spatial_mode}")


def generate_world(
    *,
    robot_count: int,
    total_slots: int,
    q_bar: float,
    mean_quota: float,
    quota_mode: str,
    spatial_mode: str,
    workspace_width: float,
    workspace_height: float,
    seed: int,
) -> tuple[list[Robot], list[Load], IntArray]:
    rng = np.random.default_rng(seed)

    load_count = int(round(total_slots / mean_quota))
    load_count = max(1, min(total_slots, load_count))

    quotas = generate_quota_vector(
        total_slots=total_slots,
        load_count=load_count,
        mode=quota_mode,
        rng=rng,
    )

    robot_positions = generate_positions(
        robot_count,
        role="robot",
        spatial_mode=spatial_mode,
        workspace_width=workspace_width,
        workspace_height=workspace_height,
        rng=rng,
    )
    load_positions = generate_positions(
        load_count,
        role="load",
        spatial_mode=spatial_mode,
        workspace_width=workspace_width,
        workspace_height=workspace_height,
        rng=rng,
    )

    robots = [
        Robot(
            id=f"R{index + 1}",
            x=float(position[0]),
            y=float(position[1]),
            capacity=q_bar,
            battery=float(rng.uniform(80.0, 100.0)),
            responding=True,
        )
        for index, position in enumerate(robot_positions)
    ]

    loads: list[Load] = []
    for index, (position, quota) in enumerate(zip(load_positions, quotas, strict=True)):
        # mass/q_bar ∈ (quota-1, quota], de modo que ceil(mass/q_bar)=quota.
        fractional_offset = float(rng.uniform(0.05, 0.95))
        mass = q_bar * (float(quota) - fractional_offset)
        loads.append(
            Load(
                id=f"L{index + 1}",
                x=float(position[0]),
                y=float(position[1]),
                mass=mass,
            )
        )

    return robots, loads, quotas


# ===============================================================
# == Reproducible geometry visualization ========================
# ===============================================================

def _entity_sort_key(entity_id: str) -> tuple[str, int]:
    prefix = entity_id.rstrip("0123456789")
    suffix = entity_id[len(prefix):]
    return prefix, int(suffix) if suffix else 0


def build_geometry_visualization_cases(
    seed: int,
    m_slots: int,
    delta: float,
    q_bar: float,
    workspace_width: float,
    workspace_height: float,
) -> dict[str, tuple[list[Robot], list[Load]]]:
    """
    Construye cinco mundos pareados en los que solo cambian las posiciones.

    Cuotas, masas, baterías e identificadores se muestrean una vez. Los RNG
    espaciales se derivan de la semilla base para que añadir o reordenar una
    geometría no altere las demás.
    """
    if m_slots <= 0:
        raise ValueError("m_slots debe ser positivo.")
    if q_bar <= 0.0:
        raise ValueError("q_bar debe ser positivo.")
    if workspace_width <= 0.0 or workspace_height <= 0.0:
        raise ValueError("El workspace debe tener dimensiones positivas.")

    robot_count = robot_count_from_delta(m_slots, delta)
    load_count = max(1, min(m_slots, int(round(m_slots / 3.0))))
    logical_rng = np.random.default_rng(
        stable_seed(seed, "geometry-visualization", "logical")
    )
    quotas = generate_quota_vector(
        total_slots=m_slots,
        load_count=load_count,
        mode="symmetric",
        rng=logical_rng,
    )
    if int(np.sum(quotas)) != m_slots:
        raise RuntimeError("Las cuotas visuales no suman M.")

    masses = [
        q_bar * (float(quota) - float(logical_rng.uniform(0.05, 0.95)))
        for quota in quotas
    ]
    batteries = logical_rng.uniform(80.0, 100.0, size=robot_count)

    cases: dict[str, tuple[list[Robot], list[Load]]] = {}
    for geometry_name in GEOMETRY_NAMES:
        spatial_rng = np.random.default_rng(
            stable_seed(seed, "geometry-visualization", "spatial", geometry_name)
        )
        robot_positions = generate_positions(
            robot_count,
            role="robot",
            spatial_mode=geometry_name,
            workspace_width=workspace_width,
            workspace_height=workspace_height,
            rng=spatial_rng,
        )
        load_positions = generate_positions(
            load_count,
            role="load",
            spatial_mode=geometry_name,
            workspace_width=workspace_width,
            workspace_height=workspace_height,
            rng=spatial_rng,
        )
        robots = [
            Robot(
                id=f"R{index + 1}",
                x=float(position[0]),
                y=float(position[1]),
                capacity=q_bar,
                battery=float(batteries[index]),
                responding=True,
            )
            for index, position in enumerate(robot_positions)
        ]
        loads = [
            Load(
                id=f"L{index + 1}",
                x=float(position[0]),
                y=float(position[1]),
                mass=float(masses[index]),
            )
            for index, position in enumerate(load_positions)
        ]
        cases[geometry_name] = (robots, loads)

    validate_geometry_visualization_cases(
        cases=cases,
        m_slots=m_slots,
        q_bar=q_bar,
    )
    return cases


def validate_geometry_visualization_cases(
    *,
    cases: dict[str, tuple[list[Robot], list[Load]]],
    m_slots: int,
    q_bar: float,
) -> None:
    if tuple(cases) != GEOMETRY_NAMES:
        raise RuntimeError("El paquete visual debe contener las cinco geometrías.")

    reference_signature: tuple[Any, ...] | None = None
    for geometry_name, (robots, loads) in cases.items():
        quotas = tuple(required_robot_count(load, q_bar) for load in loads)
        signature = (
            tuple(robot.id for robot in robots),
            tuple(load.id for load in loads),
            tuple(float(load.mass) for load in loads),
            quotas,
        )
        if sum(quotas) != m_slots:
            raise RuntimeError(
                f"Las cuotas de {geometry_name} no suman M={m_slots}."
            )
        if reference_signature is None:
            reference_signature = signature
        elif signature != reference_signature:
            raise RuntimeError(
                f"{geometry_name} no conserva identidades, masas y cuotas."
            )


def solve_geometry_visualization_cases(
    *,
    cases: dict[str, tuple[list[Robot], list[Load]]],
    q_bar: float,
) -> dict[str, HungarianResult]:
    """Resuelve exactamente una vez cada geometría y valida el cierre."""
    results: dict[str, HungarianResult] = {}
    for geometry_name in GEOMETRY_NAMES:
        robots, loads = cases[geometry_name]
        result = solve_hungarian(
            robots=robots,
            loads=loads,
            q_bar=q_bar,
            allow_partial=False,
        )
        validate_result(result=result, robots=robots, loads=loads, q_bar=q_bar)
        results[geometry_name] = result
    return results


def geometry_result_metrics(
    result: HungarianResult,
    workspace_width: float,
    workspace_height: float,
) -> dict[str, float | int]:
    assigned_costs = np.asarray(
        [assignment.cost for assignment in result.assignments],
        dtype=np.float64,
    )
    workspace_diagonal = math.hypot(workspace_width, workspace_height)
    mean_cost = (
        float(result.total_cost / assigned_costs.size)
        if assigned_costs.size
        else math.nan
    )
    p95 = (
        float(np.quantile(assigned_costs, 0.95))
        if assigned_costs.size
        else math.nan
    )
    return {
        "total_cost": float(result.total_cost),
        "mean_cost_per_slot": mean_cost,
        "normalized_p95": (
            p95 / workspace_diagonal
            if workspace_diagonal > 0.0
            else math.nan
        ),
        "idle_robot_count": len(result.idle_robots),
        "assigned_count": len(result.assignments),
    }


def _load_colors(loads: list[Load]) -> dict[str, Any]:
    color_map = plt.get_cmap("tab10")
    ordered = sorted((load.id for load in loads), key=_entity_sort_key)
    return {
        load_id: color_map(index % color_map.N)
        for index, load_id in enumerate(ordered)
    }


def draw_geometry_guides(
    axis: Axes,
    geometry_name: str,
    workspace_width: float,
    workspace_height: float,
) -> None:
    """Dibuja parámetros del generador; nunca paredes ni obstáculos."""
    guide_color = "#64748b"
    if geometry_name == "clustered":
        for fraction_x, fraction_y in CLUSTER_CENTER_FRACTIONS:
            center_x = fraction_x * workspace_width
            center_y = fraction_y * workspace_height
            axis.add_patch(
                Ellipse(
                    (center_x, center_y),
                    width=4.0 * CLUSTER_STD_FRACTIONS[0] * workspace_width,
                    height=4.0 * CLUSTER_STD_FRACTIONS[1] * workspace_height,
                    facecolor=guide_color,
                    edgecolor=guide_color,
                    linestyle=":",
                    linewidth=1.0,
                    alpha=0.08,
                    zorder=0,
                )
            )
            axis.plot(
                center_x,
                center_y,
                marker="+",
                color=guide_color,
                alpha=0.55,
                zorder=1,
            )
    elif geometry_name == "separated":
        for low, high, color in (
            (*SEPARATED_ROBOT_X_FRACTION, "#3b82f6"),
            (*SEPARATED_LOAD_X_FRACTION, "#f97316"),
        ):
            axis.add_patch(
                Rectangle(
                    (low * workspace_width, 0.0),
                    (high - low) * workspace_width,
                    workspace_height,
                    facecolor=color,
                    edgecolor=color,
                    linestyle=":",
                    linewidth=1.0,
                    alpha=0.07,
                    zorder=0,
                )
            )
    elif geometry_name == "ring":
        scale = min(workspace_width, workspace_height)
        center = (0.5 * workspace_width, 0.5 * workspace_height)
        for radial_range, color in (
            (RING_ROBOT_RADIAL_FRACTION, "#3b82f6"),
            (RING_LOAD_RADIAL_FRACTION, "#f97316"),
        ):
            inner, outer = (value * scale for value in radial_range)
            axis.add_patch(
                Wedge(
                    center,
                    outer,
                    0.0,
                    360.0,
                    width=outer - inner,
                    facecolor=color,
                    edgecolor=color,
                    linestyle=":",
                    linewidth=1.0,
                    alpha=0.07,
                    zorder=0,
                )
            )
    elif geometry_name == "corridor":
        center_y = CORRIDOR_CENTER_Y_FRACTION * workspace_height
        for spread, color in (
            (CORRIDOR_LOAD_STD_FRACTION, "#f97316"),
            (CORRIDOR_ROBOT_STD_FRACTION, "#3b82f6"),
        ):
            half_width = 2.0 * spread * workspace_height
            axis.axhspan(
                center_y - half_width,
                center_y + half_width,
                color=color,
                alpha=0.05,
                zorder=0,
            )
        axis.axhline(
            center_y,
            color=guide_color,
            linestyle=":",
            linewidth=1.0,
            alpha=0.55,
            zorder=1,
        )


def _configure_geometry_axis(
    axis: Axes,
    *,
    geometry_name: str,
    workspace_width: float,
    workspace_height: float,
    show_generator_note: bool = True,
) -> None:
    draw_geometry_guides(
        axis,
        geometry_name,
        workspace_width,
        workspace_height,
    )
    axis.set_xlim(0.0, workspace_width)
    axis.set_ylim(0.0, workspace_height)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("x [m]")
    axis.set_ylabel("y [m]")
    axis.grid(visible=True, linewidth=0.7, alpha=0.22)
    if show_generator_note:
        axis.text(
            0.01,
            0.01,
            "Las regiones sombreadas describen el generador espacial;\n"
            "no representan obstáculos.",
            transform=axis.transAxes,
            fontsize=7.5,
            color="#475569",
            va="bottom",
            bbox={
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.72,
                "pad": 2.0,
            },
            zorder=8,
        )


def draw_geometry_panel(
    axis: Axes,
    *,
    robots: list[Robot],
    loads: list[Load],
    result: HungarianResult | None,
    geometry_name: str,
    workspace_width: float,
    workspace_height: float,
    show_labels: bool = True,
    title: str | None = None,
) -> list[Line2D]:
    """Dibuja un panel y devuelve los enlaces de asignación creados."""
    _configure_geometry_axis(
        axis,
        geometry_name=geometry_name,
        workspace_width=workspace_width,
        workspace_height=workspace_height,
    )
    load_colors = _load_colors(loads)
    robot_by_id = {robot.id: robot for robot in robots}
    load_by_id = {load.id: load for load in loads}
    assigned_by_robot = (
        {
            assignment.robot_id: assignment.load_id
            for assignment in result.assignments
        }
        if result is not None
        else {}
    )

    lines: list[Line2D] = []
    if result is not None:
        for assignment in sorted(
            result.assignments,
            key=lambda item: (
                _entity_sort_key(item.load_id),
                _entity_sort_key(item.robot_id),
            ),
        ):
            robot = robot_by_id[assignment.robot_id]
            load = load_by_id[assignment.load_id]
            line = axis.plot(
                [robot.x, load.x],
                [robot.y, load.y],
                linestyle="--",
                linewidth=1.15,
                color=load_colors[assignment.load_id],
                alpha=0.72,
                zorder=2,
            )[0]
            lines.append(line)

    for robot in robots:
        load_id = assigned_by_robot.get(robot.id)
        if result is None:
            face_color = "#2563eb"
            edge_color = "white"
            line_width = 0.8
        elif load_id is None:
            face_color = "none"
            edge_color = "#94a3b8"
            line_width = 1.4
        else:
            face_color = load_colors[load_id]
            edge_color = "white"
            line_width = 0.8
        axis.scatter(
            [robot.x],
            [robot.y],
            marker="o",
            s=48,
            facecolors=face_color,
            edgecolors=edge_color,
            linewidths=line_width,
            zorder=4,
        )
        if show_labels:
            numeric_id = _entity_sort_key(robot.id)[1]
            offset = (4, 5) if numeric_id % 2 else (4, -8)
            axis.annotate(
                robot.id,
                xy=(robot.x, robot.y),
                xytext=offset,
                textcoords="offset points",
                fontsize=6.8,
                color="#1e293b",
                zorder=6,
            )

    for load in loads:
        axis.scatter(
            [load.x],
            [load.y],
            marker="X",
            s=120,
            color=load_colors[load.id],
            edgecolors="white",
            linewidths=0.7,
            zorder=5,
        )
        if show_labels:
            quota = (
                result.required_cardinality[load.id]
                if result is not None
                else required_robot_count(load, next(iter(robots)).capacity)
            )
            axis.annotate(
                f"{load.id}\nn={quota}, m={load.mass:.1f} kg",
                xy=(load.x, load.y),
                xytext=(6, 7),
                textcoords="offset points",
                fontsize=7.2,
                color="#0f172a",
                bbox={
                    "boxstyle": "round,pad=0.15",
                    "facecolor": "white",
                    "edgecolor": "none",
                    "alpha": 0.68,
                },
                zorder=7,
            )
    if title:
        axis.set_title(title, fontsize=10.5)
    return lines


def plot_geometry_case(
    robots: list[Robot],
    loads: list[Load],
    result: HungarianResult,
    geometry_name: str,
    workspace_width: float,
    workspace_height: float,
    output_path: str | Path,
    show: bool = False,
) -> int:
    """Guarda los paneles inicial/final y devuelve el número de enlaces."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    metrics = geometry_result_metrics(result, workspace_width, workspace_height)
    delta_realized = balance_delta(len(robots), len(result.slots))
    figure, axes = plt.subplots(1, 2, figsize=(16, 9), constrained_layout=True)
    draw_geometry_panel(
        axes[0],
        robots=robots,
        loads=loads,
        result=None,
        geometry_name=geometry_name,
        workspace_width=workspace_width,
        workspace_height=workspace_height,
        title="(a) Distribución inicial",
    )
    lines = draw_geometry_panel(
        axes[1],
        robots=robots,
        loads=loads,
        result=result,
        geometry_name=geometry_name,
        workspace_width=workspace_width,
        workspace_height=workspace_height,
        title="(b) Asignación Hungarian",
    )
    figure.suptitle(
        f"Geometría: {geometry_name} | N={len(robots)} | K={len(loads)} | "
        f"M={len(result.slots)} | δ={delta_realized:+.3f}\n"
        f"coste total={metrics['total_cost']:.2f} m | "
        f"coste medio/slot={metrics['mean_cost_per_slot']:.2f} m | "
        f"P95 normalizado={metrics['normalized_p95']:.4f} | "
        f"robots libres={metrics['idle_robot_count']}",
        fontsize=13,
    )
    figure.savefig(output, dpi=180, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(figure)
    return len(lines)


def plot_geometry_overviews(
    *,
    cases: dict[str, tuple[list[Robot], list[Load]]],
    results: dict[str, HungarianResult],
    workspace_width: float,
    workspace_height: float,
    output_dir: Path,
    show: bool = False,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = (
        output_dir / "geometry_initial_overview.png",
        output_dir / "geometry_assignment_overview.png",
    )
    for assigned, output_path in zip((False, True), paths, strict=True):
        figure, axes = plt.subplots(
            2,
            3,
            figsize=(18, 11),
            constrained_layout=True,
        )
        for axis, geometry_name in zip(axes.flat[:5], GEOMETRY_NAMES, strict=True):
            robots, loads = cases[geometry_name]
            result = results[geometry_name]
            metrics = geometry_result_metrics(
                result,
                workspace_width,
                workspace_height,
            )
            panel_title = geometry_name
            if assigned:
                panel_title += (
                    f"\nC={metrics['total_cost']:.1f} m | "
                    f"media={metrics['mean_cost_per_slot']:.1f} m | "
                    f"P95n={metrics['normalized_p95']:.3f} | "
                    f"libres={metrics['idle_robot_count']}"
                )
            draw_geometry_panel(
                axis,
                robots=robots,
                loads=loads,
                result=result if assigned else None,
                geometry_name=geometry_name,
                workspace_width=workspace_width,
                workspace_height=workspace_height,
                show_labels=False,
                title=panel_title,
            )

        legend_axis = axes.flat[5]
        legend_axis.axis("off")
        representative_loads = cases[GEOMETRY_NAMES[0]][1]
        colors = _load_colors(representative_loads)
        handles = [
            Line2D(
                [0],
                [0],
                marker="X",
                color="none",
                markerfacecolor=colors[load.id],
                markeredgecolor="white",
                markersize=10,
                label=load.id,
            )
            for load in representative_loads
        ]
        handles.extend(
            [
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    color="none",
                    markerfacecolor="#2563eb",
                    markersize=7,
                    label=(
                        "Robot asignado (color=carga)"
                        if assigned
                        else "Robot inicial"
                    ),
                ),
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    color="#94a3b8",
                    markerfacecolor="none",
                    markersize=7,
                    label="Robot libre",
                ),
            ]
        )
        legend_axis.legend(handles=handles, loc="upper left", ncol=2, frameon=False)
        legend_axis.text(
            0.0,
            0.48,
            "Nota metodológica\n"
            "Hungarian produce una asignación lógica estática.\n"
            "Las guías tenues describen el muestreo espacial;\n"
            "no son paredes ni obstáculos.",
            fontsize=11,
            va="top",
        )
        figure.suptitle(
            "Asignaciones Hungarian pareadas por geometría"
            if assigned
            else "Distribuciones iniciales pareadas por geometría",
            fontsize=16,
        )
        figure.savefig(output_path, dpi=180, bbox_inches="tight")
        if show:
            plt.show()
        plt.close(figure)
    return paths


def build_motion_preview_positions(
    robots: list[Robot],
    loads: list[Load],
    result: HungarianResult,
    workspace_width: float,
    workspace_height: float,
) -> dict[str, FloatArray]:
    """
    Devuelve copias de poses visuales; no modifica Robot ni representa control.
    """
    robot_by_id = {robot.id: robot for robot in robots}
    load_by_id = {load.id: load for load in loads}
    target_positions = {
        robot.id: robot.position.copy()
        for robot in robots
    }
    radius = float(
        np.clip(
            0.03 * min(workspace_width, workspace_height),
            2.0,
            4.0,
        )
    )
    for load_id in sorted(result.coalitions, key=_entity_sort_key):
        member_ids = sorted(
            result.coalitions[load_id],
            key=_entity_sort_key,
        )
        load = load_by_id[load_id]
        for member_index, robot_id in enumerate(member_ids):
            angle = 2.0 * math.pi * member_index / max(1, len(member_ids))
            candidate = np.array(
                [
                    load.x + radius * math.cos(angle),
                    load.y + radius * math.sin(angle),
                ],
                dtype=np.float64,
            )
            candidate[0] = np.clip(candidate[0], 0.0, workspace_width)
            candidate[1] = np.clip(candidate[1], 0.0, workspace_height)
            target_positions[robot_id] = candidate

    for robot_id in result.idle_robots:
        if not np.array_equal(
            target_positions[robot_id],
            robot_by_id[robot_id].position,
        ):
            raise RuntimeError("Un robot libre se desplazó en la vista ilustrativa.")
    return target_positions


def check_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _animation_output_and_writer(
    output_path: Path,
    fps: int,
) -> tuple[Path, FFMpegWriter | PillowWriter, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if check_ffmpeg_available():
        actual_path = output_path.with_suffix(".mp4")
        writer: FFMpegWriter | PillowWriter = FFMpegWriter(
            fps=fps,
            codec="libx264",
            bitrate=4000,
            extra_args=["-pix_fmt", "yuv420p"],
        )
        return actual_path, writer, "mp4"

    print(
        "FFmpeg no está disponible. Se generará GIF.\n"
        "Para MP4 instale FFmpeg y asegúrese de que esté en PATH."
    )
    actual_path = output_path.with_suffix(".gif")
    return actual_path, PillowWriter(fps=fps), "gif"


def _smoothstep(value: float) -> float:
    clipped = min(1.0, max(0.0, value))
    return clipped * clipped * (3.0 - 2.0 * clipped)


def animate_geometry_recruitment(
    robots: list[Robot],
    loads: list[Load],
    result: HungarianResult,
    geometry_name: str,
    output_path: str | Path,
    workspace_width: float,
    workspace_height: float,
    fps: int = 30,
    duration_seconds: float = 12.0,
    include_motion_preview: bool = True,
) -> dict[str, Any]:
    """Anima el resultado ya resuelto; Hungarian no se ejecuta aquí."""
    if fps <= 0 or duration_seconds <= 0.0:
        raise ValueError("fps y duration_seconds deben ser positivos.")
    if geometry_name not in GEOMETRY_NAMES:
        raise ValueError(f"Geometría desconocida: {geometry_name}")

    requested_output = Path(output_path)
    actual_output, writer, video_format = _animation_output_and_writer(
        requested_output,
        fps,
    )
    total_frames = max(2, int(round(fps * duration_seconds)))
    ordered_assignments = sorted(
        result.assignments,
        key=lambda item: (
            _entity_sort_key(item.load_id),
            _entity_sort_key(item.robot_id),
        ),
    )
    robot_by_id = {robot.id: robot for robot in robots}
    load_by_id = {load.id: load for load in loads}
    load_colors = _load_colors(loads)
    target_positions = build_motion_preview_positions(
        robots,
        loads,
        result,
        workspace_width,
        workspace_height,
    )
    assigned_load_by_robot = {
        assignment.robot_id: assignment.load_id
        for assignment in ordered_assignments
    }
    original_positions = {
        robot.id: robot.position.copy()
        for robot in robots
    }

    figure, axis = plt.subplots(figsize=(12.8, 7.2), dpi=150)
    figure.subplots_adjust(left=0.08, right=0.78, top=0.90, bottom=0.10)
    _configure_geometry_axis(
        axis,
        geometry_name=geometry_name,
        workspace_width=workspace_width,
        workspace_height=workspace_height,
    )
    axis.set_title(f"SP1.A1 — Reclutamiento lógico | {geometry_name}", fontsize=14)

    line_artists: list[Line2D] = []
    for assignment in ordered_assignments:
        robot = robot_by_id[assignment.robot_id]
        load = load_by_id[assignment.load_id]
        line = axis.plot(
            [robot.x, load.x],
            [robot.y, load.y],
            linestyle="--",
            linewidth=1.5,
            color=load_colors[assignment.load_id],
            alpha=0.76,
            visible=False,
            zorder=2,
        )[0]
        line_artists.append(line)

    robot_artists: dict[str, Any] = {}
    robot_labels: dict[str, Any] = {}
    for robot in robots:
        robot_artists[robot.id] = axis.scatter(
            [robot.x],
            [robot.y],
            s=64,
            marker="o",
            facecolors="#2563eb",
            edgecolors="white",
            linewidths=0.9,
            zorder=4,
        )
        robot_labels[robot.id] = axis.annotate(
            robot.id,
            xy=(robot.x, robot.y),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7,
            zorder=6,
        )

    load_artists: dict[str, Any] = {}
    for load in loads:
        load_artists[load.id] = axis.scatter(
            [load.x],
            [load.y],
            marker="X",
            s=150,
            color=load_colors[load.id],
            edgecolors="white",
            linewidths=0.8,
            zorder=5,
        )
        axis.annotate(
            f"{load.id}\nn={result.required_cardinality[load.id]}, "
            f"m={load.mass:.1f} kg",
            xy=(load.x, load.y),
            xytext=(7, 8),
            textcoords="offset points",
            fontsize=8,
            bbox={
                "boxstyle": "round,pad=0.18",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.72,
            },
            zorder=7,
        )

    phase_text = figure.text(
        0.80,
        0.86,
        "",
        fontsize=12,
        weight="bold",
        va="top",
    )
    status_text = figure.text(
        0.80,
        0.70,
        "",
        fontsize=10,
        va="top",
        linespacing=1.35,
    )
    warning_text = figure.text(
        0.80,
        0.30,
        "",
        fontsize=9,
        va="top",
        color="#9a3412",
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "#fff7ed",
            "edgecolor": "#fdba74",
        },
    )
    metrics = geometry_result_metrics(result, workspace_width, workspace_height)
    phase_edges = (0.0, 2.0 / 12.0, 3.0 / 12.0, 7.0 / 12.0, 11.0 / 12.0, 1.0)

    def update(frame_index: int) -> list[Any]:
        fraction = frame_index / max(1, total_frames - 1)
        for artist in load_artists.values():
            artist.set_sizes([150])
        warning_text.set_text("")

        if fraction < phase_edges[1]:
            phase_text.set_text(f"Fase A\nEscenario inicial — geometría: {geometry_name}")
            status_text.set_text(
                f"N×M = {len(robots)}×{len(result.slots)}\n"
                f"K = {len(loads)} cargas\n"
                f"M = {len(result.slots)} slots\n"
                "Sin enlaces de asignación"
            )
            revealed_count = 0
            motion_fraction = 0.0
        elif fraction < phase_edges[2]:
            phase_text.set_text("Fase B\nSolución lógica")
            status_text.set_text(
                "Hungarian resuelve una asignación global\n"
                "de coste mínimo en una sola ejecución.\n\n"
                f"Matriz: {len(robots)}×{len(result.slots)}\n"
                f"Slots: {len(result.slots)}\n"
                f"Coste: {result.total_cost:.3f} m\n"
                f"Solver: {result.timings.solver_wall_ns / 1e6:.3f} ms"
            )
            revealed_count = 0
            motion_fraction = 0.0
        elif fraction < phase_edges[3]:
            phase_text.set_text("Fase C\nRevelado del reclutamiento")
            phase_progress = (
                (fraction - phase_edges[2])
                / (phase_edges[3] - phase_edges[2])
            )
            revealed_count = min(
                len(ordered_assignments),
                int(math.floor(phase_progress * (len(ordered_assignments) + 1))),
            )
            motion_fraction = 0.0
            if revealed_count:
                latest = ordered_assignments[revealed_count - 1]
                load_revealed = sum(
                    1
                    for item in ordered_assignments[:revealed_count]
                    if item.load_id == latest.load_id
                )
                required = result.required_cardinality[latest.load_id]
                complete = load_revealed == required
                status_text.set_text(
                    f"{latest.load_id}: {load_revealed}/{required} robots reclutados"
                    + (
                        f"\nCoalición {latest.load_id} completa"
                        if complete
                        else ""
                    )
                    + (
                        "\n\nTodas las coaliciones cubiertas"
                        if revealed_count == len(ordered_assignments)
                        else ""
                    )
                )
                if complete:
                    load_artists[latest.load_id].set_sizes([260])
            else:
                status_text.set_text("Orden: load_id, después robot_id")
        elif fraction < phase_edges[4]:
            phase_text.set_text("Fase D\nAproximación cinemática ilustrativa")
            revealed_count = len(ordered_assignments)
            motion_fraction = (
                (fraction - phase_edges[3])
                / (phase_edges[4] - phase_edges[3])
                if include_motion_preview
                else 0.0
            )
            warning_text.set_text(
                "Aproximación cinemática ilustrativa:\n"
                "no representa planificación, evitación de\n"
                "obstáculos ni control físico."
            )
            status_text.set_text(
                "Interpolación visual smoothstep hacia\n"
                "poses distribuidas alrededor de cada carga."
                if include_motion_preview
                else "Vista cinemática desactivada; se conserva\n"
                "la asignación lógica estática."
            )
        else:
            phase_text.set_text("Fase E\nResumen")
            revealed_count = len(ordered_assignments)
            motion_fraction = 1.0 if include_motion_preview else 0.0
            status_text.set_text(
                "\n".join(
                    f"{load_id}: {', '.join(sorted(members, key=_entity_sort_key))}"
                    for load_id, members in sorted(
                        result.coalitions.items(),
                        key=lambda item: _entity_sort_key(item[0]),
                    )
                )
                + f"\n\nLibres: {len(result.idle_robots)}"
                f"\nCoste total: {metrics['total_cost']:.3f} m"
                f"\nMedia/slot: {metrics['mean_cost_per_slot']:.3f} m"
                f"\nP95 normalizado: {metrics['normalized_p95']:.4f}"
                f"\nSolver: {result.timings.solver_wall_ns / 1e6:.3f} ms"
            )
            warning_text.set_text(
                "Asignación lógica estática.\n"
                "La pose final es solo ilustrativa."
            )

        interpolation = _smoothstep(motion_fraction)
        revealed_robot_ids = {
            assignment.robot_id
            for assignment in ordered_assignments[:revealed_count]
        }
        for robot in robots:
            position = original_positions[robot.id]
            if robot.id in assigned_load_by_robot:
                target = target_positions[robot.id]
                position = position + interpolation * (target - position)
            robot_artists[robot.id].set_offsets(position.reshape(1, 2))
            robot_labels[robot.id].xy = (float(position[0]), float(position[1]))
            if robot.id in revealed_robot_ids:
                color = load_colors[assigned_load_by_robot[robot.id]]
                robot_artists[robot.id].set_facecolors([color])
                robot_artists[robot.id].set_edgecolors(["white"])
            elif robot.id in result.idle_robots and fraction >= phase_edges[3]:
                robot_artists[robot.id].set_facecolors(["none"])
                robot_artists[robot.id].set_edgecolors(["#94a3b8"])
            else:
                robot_artists[robot.id].set_facecolors(["#2563eb"])
                robot_artists[robot.id].set_edgecolors(["white"])

        for index, (line, assignment) in enumerate(
            zip(line_artists, ordered_assignments, strict=True)
        ):
            visible = index < revealed_count
            line.set_visible(visible)
            if visible:
                position = robot_artists[assignment.robot_id].get_offsets()[0]
                load = load_by_id[assignment.load_id]
                line.set_data(
                    [float(position[0]), load.x],
                    [float(position[1]), load.y],
                )
        return [
            *line_artists,
            *robot_artists.values(),
            *load_artists.values(),
            phase_text,
            status_text,
            warning_text,
        ]

    animation = FuncAnimation(
        figure,
        update,
        frames=total_frames,
        interval=1000.0 / fps,
        blit=False,
        repeat=False,
    )
    animation.save(actual_output, writer=writer, dpi=150)
    plt.close(figure)
    if not actual_output.is_file() or actual_output.stat().st_size == 0:
        raise RuntimeError(f"No se generó el vídeo esperado: {actual_output}")
    return {
        "path": actual_output,
        "format": video_format,
        "frames": total_frames,
        "fps": fps,
        "duration_seconds": duration_seconds,
    }


def _figure_rgb(figure: Figure) -> NDArray[np.uint8]:
    figure.canvas.draw()
    rgba = np.asarray(figure.canvas.buffer_rgba(), dtype=np.uint8)
    return rgba[:, :, :3].copy()


def _render_geometry_combined_frame(
    *,
    robots: list[Robot],
    loads: list[Load],
    result: HungarianResult | None,
    geometry_name: str,
    workspace_width: float,
    workspace_height: float,
    title: str,
) -> NDArray[np.uint8]:
    figure, axis = plt.subplots(figsize=(12.8, 7.2), dpi=150)
    figure.subplots_adjust(left=0.15, right=0.85, top=0.88, bottom=0.10)
    draw_geometry_panel(
        axis,
        robots=robots,
        loads=loads,
        result=result,
        geometry_name=geometry_name,
        workspace_width=workspace_width,
        workspace_height=workspace_height,
        show_labels=True,
        title=title,
    )
    frame = _figure_rgb(figure)
    plt.close(figure)
    return frame


def _render_transition_frame(
    *,
    geometry_name: str,
    description: str,
    metrics: dict[str, float | int],
) -> NDArray[np.uint8]:
    figure = plt.figure(figsize=(12.8, 7.2), dpi=150, facecolor="#0f172a")
    figure.text(
        0.5,
        0.64,
        geometry_name.upper(),
        ha="center",
        va="center",
        color="white",
        fontsize=36,
        weight="bold",
    )
    figure.text(
        0.5,
        0.49,
        description,
        ha="center",
        va="center",
        color="#cbd5e1",
        fontsize=17,
    )
    figure.text(
        0.5,
        0.34,
        f"Coste total: {metrics['total_cost']:.2f} m   |   "
        f"P95 normalizado: {metrics['normalized_p95']:.4f}",
        ha="center",
        va="center",
        color="#fb923c",
        fontsize=18,
    )
    frame = _figure_rgb(figure)
    plt.close(figure)
    return frame


def _render_comparison_frame(
    *,
    results: dict[str, HungarianResult],
    workspace_width: float,
    workspace_height: float,
) -> NDArray[np.uint8]:
    order = ("corridor", "uniform", "clustered", "ring", "separated")
    values = [
        float(
            geometry_result_metrics(
                results[name],
                workspace_width,
                workspace_height,
            )["normalized_p95"]
        )
        for name in order
    ]
    figure, axis = plt.subplots(figsize=(12.8, 7.2), dpi=150)
    bars = axis.bar(order, values, color=plt.get_cmap("tab10").colors[:5])
    axis.bar_label(bars, fmt="%.4f", padding=4)
    axis.set_ylabel("P95 normalizado por la diagonal del workspace")
    axis.set_title("Comparación final — P95 normalizado por geometría", fontsize=18)
    axis.grid(axis="y", alpha=0.25)
    axis.text(
        0.5,
        -0.14,
        "Valores calculados desde las cinco asignaciones de este run.",
        transform=axis.transAxes,
        ha="center",
        fontsize=11,
    )
    figure.tight_layout()
    frame = _figure_rgb(figure)
    plt.close(figure)
    return frame


def animate_all_geometries_recruitment(
    *,
    cases: dict[str, tuple[list[Robot], list[Load]]],
    results: dict[str, HungarianResult],
    output_path: Path,
    workspace_width: float,
    workspace_height: float,
    fps: int,
) -> dict[str, Any]:
    """Crea un resumen secuencial de 7 s por geometría y cierre comparativo."""
    descriptions = {
        "uniform": "Robots y cargas se muestrean uniformemente en el workspace.",
        "clustered": "Las cargas se concentran alrededor de dos centros; robots uniformes.",
        "separated": "Robots y cargas nacen en zonas opuestas del eje x.",
        "ring": "Robots en anillo exterior y cargas cerca del centro.",
        "corridor": "Robots y cargas se muestrean alrededor de un eje longitudinal.",
    }
    scene_images: dict[tuple[str, str], NDArray[np.uint8]] = {}
    for geometry_name in GEOMETRY_NAMES:
        robots, loads = cases[geometry_name]
        result = results[geometry_name]
        metrics = geometry_result_metrics(
            result,
            workspace_width,
            workspace_height,
        )
        scene_images[(geometry_name, "transition")] = _render_transition_frame(
            geometry_name=geometry_name,
            description=descriptions[geometry_name],
            metrics=metrics,
        )
        scene_images[(geometry_name, "initial")] = _render_geometry_combined_frame(
            robots=robots,
            loads=loads,
            result=None,
            geometry_name=geometry_name,
            workspace_width=workspace_width,
            workspace_height=workspace_height,
            title=f"{geometry_name} — escenario inicial",
        )
        scene_images[(geometry_name, "assigned")] = _render_geometry_combined_frame(
            robots=robots,
            loads=loads,
            result=result,
            geometry_name=geometry_name,
            workspace_width=workspace_width,
            workspace_height=workspace_height,
            title=f"{geometry_name} — asignación lógica Hungarian",
        )
    comparison_image = _render_comparison_frame(
        results=results,
        workspace_width=workspace_width,
        workspace_height=workspace_height,
    )

    seconds_per_geometry = 7.0
    final_seconds = 4.0
    frames_per_geometry = int(round(seconds_per_geometry * fps))
    total_frames = frames_per_geometry * len(GEOMETRY_NAMES) + int(
        round(final_seconds * fps)
    )
    actual_output, writer, video_format = _animation_output_and_writer(
        output_path,
        fps,
    )
    figure, axis = plt.subplots(figsize=(12.8, 7.2), dpi=150)
    figure.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
    axis.axis("off")
    image_artist = axis.imshow(
        scene_images[(GEOMETRY_NAMES[0], "transition")],
        animated=False,
    )

    def update(frame_index: int) -> list[Any]:
        sequence_limit = frames_per_geometry * len(GEOMETRY_NAMES)
        if frame_index >= sequence_limit:
            image_artist.set_data(comparison_image)
            return [image_artist]
        geometry_index, local_frame = divmod(frame_index, frames_per_geometry)
        geometry_name = GEOMETRY_NAMES[geometry_index]
        local_fraction = local_frame / max(1, frames_per_geometry - 1)
        if local_fraction < 1.25 / seconds_per_geometry:
            stage = "transition"
        elif local_fraction < 2.75 / seconds_per_geometry:
            stage = "initial"
        else:
            stage = "assigned"
        image_artist.set_data(scene_images[(geometry_name, stage)])
        return [image_artist]

    animation = FuncAnimation(
        figure,
        update,
        frames=total_frames,
        interval=1000.0 / fps,
        blit=False,
        repeat=False,
    )
    animation.save(actual_output, writer=writer, dpi=150)
    plt.close(figure)
    if not actual_output.is_file() or actual_output.stat().st_size == 0:
        raise RuntimeError(f"No se generó el vídeo combinado: {actual_output}")
    return {
        "path": actual_output,
        "format": video_format,
        "frames": total_frames,
        "fps": fps,
        "duration_seconds": total_frames / fps,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative_artifact_path(path: Path, output_dir: Path) -> str:
    return path.resolve().relative_to(output_dir.resolve()).as_posix()


def write_geometry_visualization_report(
    *,
    output_path: Path,
    records: dict[str, dict[str, Any]],
    combined_video: dict[str, Any] | None,
) -> None:
    lines = [
        "# Reporte de visualización geométrica SP1.A1",
        "",
        "Una **geometría espacial** es la distribución probabilística usada para "
        "muestrear las posiciones iniciales `(x,y)` de robots y cargas. Las "
        "regiones dibujadas describen esos generadores; no son obstáculos.",
        "",
        "Las cinco instancias comparten `N`, `K`, `M`, identificadores, masas y "
        "cuotas. Solo cambian las posiciones iniciales.",
        "",
        "## Comparación",
        "",
        "| Geometría | Coste total [m] | Media/slot [m] | P95 normalizado | Libres |",
        "|---|---:|---:|---:|---:|",
    ]
    for geometry_name in GEOMETRY_NAMES:
        record = records[geometry_name]
        lines.append(
            f"| {geometry_name} | {record['total_cost']:.3f} | "
            f"{record['mean_cost_per_slot']:.3f} | "
            f"{record['normalized_p95']:.5f} | "
            f"{len(record['idle_robots'])} |"
        )
    lines.extend(["", "## Escenarios", ""])
    for geometry_name in GEOMETRY_NAMES:
        record = records[geometry_name]
        lines.extend(
            [
                f"### {geometry_name}",
                "",
                f"- Figura: `{record['png_path']}`",
                f"- Vídeo: `{record['video_path'] or 'no generado'}`",
                f"- Coaliciones: `{json.dumps(record['coalitions'], ensure_ascii=False)}`",
                "",
            ]
        )
    if combined_video is not None:
        lines.extend(
            [
                "## Vídeo combinado",
                "",
                f"`{combined_video['relative_path']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Límite metodológico",
            "",
            "**Hungarian produce una asignación lógica estática; el movimiento "
            "mostrado es solo una ilustración cinemática.** No valida "
            "navegación, evitación de obstáculos, contacto, control ni "
            "transporte físico.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run_geometry_visualization(
    *,
    seed: int,
    m_slots: int,
    delta: float,
    q_bar: float,
    workspace_width: float,
    workspace_height: float,
    fps: int,
    duration_seconds: float,
    make_videos: bool,
    include_motion_preview: bool,
    output_dir: Path,
    show: bool,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = output_dir / "plots" / "geometries"
    videos_dir = output_dir / "videos" / "geometries"
    cases = build_geometry_visualization_cases(
        seed=seed,
        m_slots=m_slots,
        delta=delta,
        q_bar=q_bar,
        workspace_width=workspace_width,
        workspace_height=workspace_height,
    )
    results = solve_geometry_visualization_cases(cases=cases, q_bar=q_bar)

    png_paths: dict[str, Path] = {}
    for geometry_name in GEOMETRY_NAMES:
        robots, loads = cases[geometry_name]
        png_path = plots_dir / f"{geometry_name}_assignment.png"
        line_count = plot_geometry_case(
            robots,
            loads,
            results[geometry_name],
            geometry_name,
            workspace_width,
            workspace_height,
            png_path,
            show=show,
        )
        if line_count != len(results[geometry_name].assignments):
            raise RuntimeError(
                f"{geometry_name}: el número de enlaces no coincide con M."
            )
        png_paths[geometry_name] = png_path
    overview_paths = plot_geometry_overviews(
        cases=cases,
        results=results,
        workspace_width=workspace_width,
        workspace_height=workspace_height,
        output_dir=plots_dir,
        show=show,
    )

    video_metadata: dict[str, dict[str, Any]] = {}
    combined_metadata: dict[str, Any] | None = None
    if make_videos:
        for geometry_name in GEOMETRY_NAMES:
            robots, loads = cases[geometry_name]
            video_metadata[geometry_name] = animate_geometry_recruitment(
                robots,
                loads,
                results[geometry_name],
                geometry_name,
                videos_dir / f"{geometry_name}_recruitment.mp4",
                workspace_width,
                workspace_height,
                fps=fps,
                duration_seconds=duration_seconds,
                include_motion_preview=include_motion_preview,
            )
        combined_metadata = animate_all_geometries_recruitment(
            cases=cases,
            results=results,
            output_path=videos_dir / "all_geometries_recruitment.mp4",
            workspace_width=workspace_width,
            workspace_height=workspace_height,
            fps=fps,
        )

    records: dict[str, dict[str, Any]] = {}
    for geometry_name in GEOMETRY_NAMES:
        robots, loads = cases[geometry_name]
        result = results[geometry_name]
        metrics = geometry_result_metrics(
            result,
            workspace_width,
            workspace_height,
        )
        video = video_metadata.get(geometry_name)
        video_path = Path(video["path"]) if video is not None else None
        records[geometry_name] = {
            "seed": seed,
            "N": len(robots),
            "K": len(loads),
            "M": len(result.slots),
            "requested_delta": delta,
            "realized_delta": balance_delta(len(robots), len(result.slots)),
            "quotas": {
                load.id: result.required_cardinality[load.id]
                for load in loads
            },
            "masses_kg": {load.id: load.mass for load in loads},
            "initial_positions": {
                "robots": {
                    robot.id: [robot.x, robot.y]
                    for robot in robots
                },
                "loads": {
                    load.id: [load.x, load.y]
                    for load in loads
                },
            },
            "coalitions": result.coalitions,
            "idle_robots": result.idle_robots,
            "total_cost": metrics["total_cost"],
            "mean_cost_per_slot": metrics["mean_cost_per_slot"],
            "normalized_p95": metrics["normalized_p95"],
            "solver_wall_ns": result.timings.solver_wall_ns,
            "png_path": _relative_artifact_path(
                png_paths[geometry_name],
                output_dir,
            ),
            "video_path": (
                _relative_artifact_path(video_path, output_dir)
                if video_path is not None
                else None
            ),
            "video_format": video["format"] if video is not None else None,
            "frames": video["frames"] if video is not None else 0,
            "fps": video["fps"] if video is not None else fps,
            "duration_seconds": (
                video["duration_seconds"]
                if video is not None
                else duration_seconds
            ),
            "sha256": {
                "png": sha256_file(png_paths[geometry_name]),
                "video": (
                    sha256_file(video_path)
                    if video_path is not None
                    else None
                ),
            },
        }

    combined_record: dict[str, Any] | None = None
    if combined_metadata is not None:
        combined_path = Path(combined_metadata["path"])
        combined_record = {
            **{
                key: value
                for key, value in combined_metadata.items()
                if key != "path"
            },
            "relative_path": _relative_artifact_path(
                combined_path,
                output_dir,
            ),
            "sha256": sha256_file(combined_path),
        }

    report_path = output_dir / "GEOMETRY_VISUALIZATION_REPORT.md"
    write_geometry_visualization_report(
        output_path=report_path,
        records=records,
        combined_video=combined_record,
    )
    manifest = {
        "schema_version": 1,
        "generator": "scripts/sp1_a1_hungarian.py",
        "configuration": {
            "seed": seed,
            "m_slots": m_slots,
            "delta": delta,
            "q_bar": q_bar,
            "workspace_width": workspace_width,
            "workspace_height": workspace_height,
            "fps": fps,
            "duration_seconds": duration_seconds,
            "make_videos": make_videos,
            "include_motion_preview": include_motion_preview,
        },
        "scenarios": records,
        "common_artifacts": {
            "initial_overview": {
                "path": _relative_artifact_path(overview_paths[0], output_dir),
                "sha256": sha256_file(overview_paths[0]),
            },
            "assignment_overview": {
                "path": _relative_artifact_path(overview_paths[1], output_dir),
                "sha256": sha256_file(overview_paths[1]),
            },
            "combined_video": combined_record,
            "report": {
                "path": _relative_artifact_path(report_path, output_dir),
                "sha256": sha256_file(report_path),
            },
        },
    }
    manifest_path = output_dir / "geometry_visualization_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Visualización geométrica completada: {output_dir.resolve()}")
    return manifest


# ===============================================================
# == Communication model ========================================
# ===============================================================

def encoded_size(payload: dict[str, Any]) -> int:
    return len(
        json.dumps(
            payload,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )


def assignment_map(result: HungarianResult) -> dict[str, str | None]:
    mapping: dict[str, str | None] = {
        robot_id: None for robot_id in result.idle_robots
    }
    for assignment in result.assignments:
        mapping[assignment.robot_id] = assignment.load_id
    return mapping


def estimate_communication(
    *,
    original_robots: list[Robot],
    active_robots: list[Robot],
    result: HungarianResult,
    max_retries: int,
) -> CommunicationStats:
    """
    Modelo explícito para el baseline centralizado:

    1. cada robot activo envía un estado al coordinador;
    2. el coordinador envía una decisión a cada robot activo;
    3. cada robot no respondiente genera max_retries consultas sin respuesta.

    No se cuentan mensajes robot-robot, porque Hungarian no es distribuido.
    """
    active_ids = {robot.id for robot in active_robots}
    failed_robots = [
        robot for robot in original_robots if robot.id not in active_ids
    ]

    total_bytes = 0
    logical_messages = 0

    for robot in active_robots:
        state_payload = {
            "type": "robot_state",
            "robot_id": robot.id,
            "x": robot.x,
            "y": robot.y,
            "capacity": robot.capacity,
            "battery": robot.battery,
            "responding": True,
        }
        total_bytes += encoded_size(state_payload)
        logical_messages += 1

    decisions = assignment_map(result)
    for robot in active_robots:
        decision_payload = {
            "type": "assignment",
            "robot_id": robot.id,
            "load_id": decisions.get(robot.id),
            "feasible": result.feasible,
        }
        total_bytes += encoded_size(decision_payload)
        logical_messages += 1

    retry_messages = 0
    for robot in failed_robots:
        retry_payload = {
            "type": "state_request_retry",
            "robot_id": robot.id,
        }
        retry_size = encoded_size(retry_payload)
        total_bytes += retry_size * max_retries
        logical_messages += max_retries
        retry_messages += max_retries

    communication_rounds = 2 + (max_retries if failed_robots else 0)

    return CommunicationStats(
        logical_messages=logical_messages,
        communication_bytes=total_bytes,
        communication_rounds=communication_rounds,
        retry_messages=retry_messages,
        nonresponding_count=len(failed_robots),
    )


# ===============================================================
# == Monte Carlo metrics ========================================
# ===============================================================

def sequential_greedy_cost(cost_matrix: FloatArray) -> float:
    """
    Baseline greedy determinista con la misma cardinalidad que Hungarian.

    Si hay más robots que slots, recorre slots y toma el robot libre más
    cercano. En escasez recorre robots y toma el slot libre más cercano.
    """
    robot_count, slot_count = cost_matrix.shape
    if robot_count == 0 or slot_count == 0:
        return 0.0

    total = 0.0
    if robot_count >= slot_count:
        available = np.ones(robot_count, dtype=bool)
        for slot_index in range(slot_count):
            candidates = np.where(available, cost_matrix[:, slot_index], np.inf)
            robot_index = int(np.argmin(candidates))
            total += float(cost_matrix[robot_index, slot_index])
            available[robot_index] = False
        return total

    available = np.ones(slot_count, dtype=bool)
    for robot_index in range(robot_count):
        candidates = np.where(available, cost_matrix[robot_index, :], np.inf)
        slot_index = int(np.argmin(candidates))
        total += float(cost_matrix[robot_index, slot_index])
        available[slot_index] = False
    return total


def assignment_cost_lower_bound(cost_matrix: FloatArray) -> float:
    """Cota inferior relajada para una asignación rectangular de cardinalidad máxima."""
    robot_count, slot_count = cost_matrix.shape
    if robot_count >= slot_count:
        return float(np.sum(np.min(cost_matrix, axis=0)))
    return float(np.sum(np.min(cost_matrix, axis=1)))


def gini_coefficient(values: Sequence[float] | FloatArray) -> float:
    """Dispersión de costes en [0, 1], donde 0 indica costes iguales."""
    array = np.sort(np.asarray(values, dtype=np.float64))
    if array.size == 0:
        return math.nan
    total = float(np.sum(array))
    if total == 0.0:
        return 0.0
    indices = np.arange(1, array.size + 1, dtype=np.float64)
    value = float(
        2.0 * np.sum(indices * array) / (array.size * total)
        - (array.size + 1.0) / array.size
    )
    return min(1.0, max(0.0, value))


def jain_index(values: Sequence[float] | FloatArray) -> float:
    """Uniformidad de los costes en [1/n, 1], donde 1 indica igualdad."""
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0:
        return math.nan
    squared_sum = float(np.sum(array**2))
    if squared_sum == 0.0:
        return 1.0
    return float(np.sum(array) ** 2 / (array.size * squared_sum))


def result_metrics(
    *,
    study: str,
    seed: int,
    robots: list[Robot],
    loads: list[Load],
    quotas: IntArray,
    result: HungarianResult,
    communication: CommunicationStats,
    workspace_width: float,
    workspace_height: float,
    quota_mode: str,
    spatial_mode: str,
    requested_delta: float,
    treatment: str = "none",
    original_robot_count: int | None = None,
    failure_count: int = 0,
    failed_robot_was_assigned: bool = False,
    base_total_cost: float = math.nan,
    relative_cost_increase: float = math.nan,
    assignment_churn: float = math.nan,
) -> dict[str, Any]:
    metrics_start = time.perf_counter_ns()
    robot_count = len(robots)
    slot_count = len(result.slots)
    load_count = len(loads)
    assigned_count = len(result.assignments)
    workspace_diagonal = math.hypot(workspace_width, workspace_height)

    mean_assigned_cost = (
        result.total_cost / assigned_count if assigned_count > 0 else math.nan
    )
    normalized_cost = (
        mean_assigned_cost / workspace_diagonal
        if assigned_count > 0 and workspace_diagonal > 0
        else math.nan
    )

    cost_asymmetry = coefficient_of_variation(result.cost_matrix.ravel())
    quota_asymmetry = coefficient_of_variation(quotas)
    assignment_costs = np.asarray(
        [assignment.cost for assignment in result.assignments],
        dtype=np.float64,
    )
    cost_p50 = (
        float(np.quantile(assignment_costs, 0.50))
        if assignment_costs.size > 0
        else math.nan
    )
    cost_p95 = (
        float(np.quantile(assignment_costs, 0.95))
        if assignment_costs.size > 0
        else math.nan
    )
    cost_max = (
        float(np.max(assignment_costs))
        if assignment_costs.size > 0
        else math.nan
    )
    cost_std = (
        float(np.std(assignment_costs))
        if assignment_costs.size > 0
        else math.nan
    )

    greedy_cost = sequential_greedy_cost(result.cost_matrix)
    lower_bound = assignment_cost_lower_bound(result.cost_matrix)
    greedy_ratio = (
        greedy_cost / result.total_cost
        if result.total_cost > 0.0
        else 1.0
    )
    greedy_saving = (
        (greedy_cost - result.total_cost) / greedy_cost
        if greedy_cost > 0.0
        else 0.0
    )
    lower_bound_gap = (
        (result.total_cost - lower_bound) / result.total_cost
        if result.total_cost > 0.0
        else 0.0
    )

    load_costs: dict[str, list[float]] = defaultdict(list)
    for assignment in result.assignments:
        load_costs[assignment.load_id].append(assignment.cost)
    load_mean_costs = np.asarray(
        [np.mean(values) for values in load_costs.values()],
        dtype=np.float64,
    )
    load_cost_cv = (
        coefficient_of_variation(load_mean_costs)
        if load_mean_costs.size > 0
        else math.nan
    )

    metrics = {
        "study": study,
        "seed": seed,
        "N": robot_count,
        "N_original": original_robot_count if original_robot_count is not None else robot_count,
        "K": load_count,
        "M": slot_count,
        "size_N_plus_M": robot_count + slot_count,
        "matrix_elements": robot_count * slot_count,
        "requested_delta": requested_delta,
        "observed_delta": balance_delta(robot_count, slot_count),
        "rho_M_over_N": slot_count / robot_count,
        "quota_mode": quota_mode,
        "spatial_mode": spatial_mode,
        "treatment": treatment,
        "structurally_feasible": robot_count >= slot_count,
        "mission_feasible": result.feasible,
        "coverage": result.coverage,
        "assigned_slot_count": assigned_count,
        "missing_slot_count": result.missing_slots,
        "idle_robot_count": len(result.idle_robots),
        "idle_fraction": len(result.idle_robots) / robot_count,
        "quota_asymmetry_cv": quota_asymmetry,
        "cost_asymmetry_cv": cost_asymmetry,
        "total_cost": result.total_cost,
        "mean_cost_per_assigned_slot": mean_assigned_cost,
        "normalized_cost_per_assigned_slot": normalized_cost,
        "assignment_cost_p50": cost_p50,
        "assignment_cost_p95": cost_p95,
        "assignment_cost_max": cost_max,
        "assignment_cost_std": cost_std,
        "assignment_cost_cv": coefficient_of_variation(assignment_costs),
        "assignment_cost_gini": gini_coefficient(assignment_costs),
        "assignment_cost_jain": jain_index(assignment_costs),
        "normalized_assignment_cost_p95": cost_p95 / workspace_diagonal,
        "normalized_assignment_cost_max": cost_max / workspace_diagonal,
        "load_mean_cost_cv": load_cost_cv,
        "served_load_fraction": len(load_costs) / load_count,
        "robot_utilization": assigned_count / robot_count,
        "greedy_total_cost": greedy_cost,
        "greedy_to_hungarian_ratio": greedy_ratio,
        "hungarian_saving_vs_greedy": greedy_saving,
        "assignment_cost_lower_bound": lower_bound,
        "relative_gap_to_lower_bound": lower_bound_gap,
        "slots_wall_ns": result.timings.slots_wall_ns,
        "matrix_wall_ns": result.timings.matrix_wall_ns,
        "solver_wall_ns": result.timings.solver_wall_ns,
        "post_wall_ns": result.timings.post_wall_ns,
        "total_wall_ns": result.timings.total_wall_ns,
        "total_cpu_ns": result.timings.total_cpu_ns,
        "matrix_bytes": int(result.cost_matrix.nbytes),
        "solver_ns_per_matrix_element": (
            result.timings.solver_wall_ns / result.cost_matrix.size
        ),
        "matrix_build_ns_per_element": (
            result.timings.matrix_wall_ns / result.cost_matrix.size
        ),
        "failure_count": failure_count,
        "failure_rate": (
            failure_count / original_robot_count
            if original_robot_count not in (None, 0)
            else 0.0
        ),
        "failed_robot_was_assigned": failed_robot_was_assigned,
        "recovery_feasible": result.feasible,
        "base_total_cost": base_total_cost,
        "relative_cost_increase": relative_cost_increase,
        "assignment_churn": assignment_churn,
        "logical_messages": communication.logical_messages,
        "communication_bytes": communication.communication_bytes,
        "logical_messages_per_assigned_slot": (
            communication.logical_messages / assigned_count
        ),
        "communication_bytes_per_assigned_slot": (
            communication.communication_bytes / assigned_count
        ),
        "communication_rounds": communication.communication_rounds,
        "retry_messages": communication.retry_messages,
        "nonresponding_count": communication.nonresponding_count,
    }
    metrics["metrics_wall_ns"] = time.perf_counter_ns() - metrics_start
    return metrics


def changed_assignment_fraction(
    base_result: HungarianResult,
    new_result: HungarianResult,
    surviving_robot_ids: set[str],
) -> float:
    if not surviving_robot_ids:
        return math.nan

    base_map = assignment_map(base_result)
    new_map = assignment_map(new_result)
    changed = sum(
        base_map.get(robot_id) != new_map.get(robot_id)
        for robot_id in surviving_robot_ids
    )
    return changed / len(surviving_robot_ids)


def choose_critical_assigned_robot(
    robots: list[Robot],
    result: HungarianResult,
) -> str:
    """
    Aproxima el robot asignado más crítico por el margen de sustitución local.

    Si no hay robots libres, cualquier fallo asignado hace N-1<M; se elige el
    robot con menor coste actual para mantener una regla determinista.
    """
    if not result.assignments:
        raise ValueError("No hay robots asignados.")

    robot_index_by_id = {robot.id: index for index, robot in enumerate(robots)}
    slot_index_by_id = {slot.slot_id: index for index, slot in enumerate(result.slots)}
    idle_indices = [robot_index_by_id[robot_id] for robot_id in result.idle_robots]

    if not idle_indices:
        selected = min(
            result.assignments,
            key=lambda assignment: (assignment.cost, assignment.robot_id),
        )
        return selected.robot_id

    best_robot_id = result.assignments[0].robot_id
    best_penalty = -math.inf

    for assignment in result.assignments:
        slot_index = slot_index_by_id[assignment.slot_id]
        replacement_cost = float(
            np.min(result.cost_matrix[idle_indices, slot_index])
        )
        penalty = replacement_cost - assignment.cost
        if penalty > best_penalty:
            best_penalty = penalty
            best_robot_id = assignment.robot_id

    return best_robot_id


def select_failed_robot_ids(
    *,
    treatment: str,
    robots: list[Robot],
    base_result: HungarianResult,
    rng: np.random.Generator,
) -> set[str] | None:
    all_ids = np.array([robot.id for robot in robots], dtype=object)
    assigned_ids = np.array(
        [assignment.robot_id for assignment in base_result.assignments],
        dtype=object,
    )

    if treatment == "no_failure":
        return set()

    if treatment == "idle_robot_failure":
        if not base_result.idle_robots:
            return None
        return {str(rng.choice(np.array(base_result.idle_robots, dtype=object)))}

    if treatment == "random_assigned_failure":
        return {str(rng.choice(assigned_ids))}

    if treatment == "critical_assigned_failure":
        return {choose_critical_assigned_robot(robots, base_result)}

    random_failure_fractions = {
        "random_5_percent": 0.05,
        "random_10_percent": 0.10,
        "random_20_percent": 0.20,
        "random_30_percent": 0.30,
    }
    if treatment in random_failure_fractions:
        fraction = random_failure_fractions[treatment]
        count = max(1, int(round(fraction * len(robots))))
        selected = rng.choice(all_ids, size=min(count, len(all_ids)), replace=False)
        return {str(value) for value in selected.tolist()}

    raise ValueError(f"Tratamiento de fallo desconocido: {treatment}")


# ===============================================================
# == Monte Carlo campaigns ======================================
# ===============================================================

def run_scaling_study(config: MonteCarloConfig) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    total_cells = len(config.scaling_m_values) * len(config.scaling_deltas)
    cell_index = 0

    for total_slots in config.scaling_m_values:
        for requested_delta in config.scaling_deltas:
            cell_index += 1
            robot_count = robot_count_from_delta(total_slots, requested_delta)
            print(
                f"[scaling {cell_index}/{total_cells}] "
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
                robots, loads, quotas = generate_world(
                    robot_count=robot_count,
                    total_slots=total_slots,
                    q_bar=config.q_bar,
                    mean_quota=config.mean_quota,
                    quota_mode="symmetric",
                    spatial_mode="uniform",
                    workspace_width=config.workspace_width,
                    workspace_height=config.workspace_height,
                    seed=seed,
                )
                result = solve_hungarian(
                    robots=robots,
                    loads=loads,
                    q_bar=config.q_bar,
                    allow_partial=True,
                )
                communication = estimate_communication(
                    original_robots=robots,
                    active_robots=robots,
                    result=result,
                    max_retries=config.max_retries,
                )
                records.append(
                    result_metrics(
                        study="scaling",
                        seed=seed,
                        robots=robots,
                        loads=loads,
                        quotas=quotas,
                        result=result,
                        communication=communication,
                        workspace_width=config.workspace_width,
                        workspace_height=config.workspace_height,
                        quota_mode="symmetric",
                        spatial_mode="uniform",
                        requested_delta=requested_delta,
                    )
                )

    return records


def run_balance_study(config: MonteCarloConfig) -> list[dict[str, Any]]:
    """
    Barre casi todo el dominio de δ con tamaños moderados.

    Los extremos matemáticos -1 y +1 no son instancias finitas: el primero
    implica N=0 y el segundo N→∞. Por eso se muestrea el interior.
    """
    records: list[dict[str, Any]] = []
    total_cells = len(config.balance_m_values) * len(config.balance_deltas)
    cell_index = 0

    for total_slots in config.balance_m_values:
        for requested_delta in config.balance_deltas:
            cell_index += 1
            robot_count = robot_count_from_delta(total_slots, requested_delta)
            print(
                f"[balance {cell_index}/{total_cells}] "
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
                robots, loads, quotas = generate_world(
                    robot_count=robot_count,
                    total_slots=total_slots,
                    q_bar=config.q_bar,
                    mean_quota=config.mean_quota,
                    quota_mode="symmetric",
                    spatial_mode="uniform",
                    workspace_width=config.workspace_width,
                    workspace_height=config.workspace_height,
                    seed=seed,
                )
                result = solve_hungarian(
                    robots=robots,
                    loads=loads,
                    q_bar=config.q_bar,
                    allow_partial=True,
                )
                communication = estimate_communication(
                    original_robots=robots,
                    active_robots=robots,
                    result=result,
                    max_retries=config.max_retries,
                )
                records.append(
                    result_metrics(
                        study="balance",
                        seed=seed,
                        robots=robots,
                        loads=loads,
                        quotas=quotas,
                        result=result,
                        communication=communication,
                        workspace_width=config.workspace_width,
                        workspace_height=config.workspace_height,
                        quota_mode="symmetric",
                        spatial_mode="uniform",
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
    cell_index = 0

    for total_slots in config.asymmetry_m_values:
        robot_count = robot_count_from_delta(total_slots, config.asymmetry_delta)
        for quota_mode in config.quota_modes:
            for spatial_mode in config.spatial_modes:
                cell_index += 1
                print(
                    f"[asymmetry {cell_index}/{total_cells}] "
                    f"M={total_slots}, N={robot_count}, "
                    f"quota={quota_mode}, spatial={spatial_mode}"
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
                    robots, loads, quotas = generate_world(
                        robot_count=robot_count,
                        total_slots=total_slots,
                        q_bar=config.q_bar,
                        mean_quota=config.mean_quota,
                        quota_mode=quota_mode,
                        spatial_mode=spatial_mode,
                        workspace_width=config.workspace_width,
                        workspace_height=config.workspace_height,
                        seed=seed,
                    )
                    result = solve_hungarian(
                        robots=robots,
                        loads=loads,
                        q_bar=config.q_bar,
                        allow_partial=False,
                    )
                    communication = estimate_communication(
                        original_robots=robots,
                        active_robots=robots,
                        result=result,
                        max_retries=config.max_retries,
                    )
                    records.append(
                        result_metrics(
                            study="asymmetry",
                            seed=seed,
                            robots=robots,
                            loads=loads,
                            quotas=quotas,
                            result=result,
                            communication=communication,
                            workspace_width=config.workspace_width,
                            workspace_height=config.workspace_height,
                            quota_mode=quota_mode,
                            spatial_mode=spatial_mode,
                            requested_delta=config.asymmetry_delta,
                        )
                    )

    return records


def run_failure_study(config: MonteCarloConfig) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    total_cells = len(config.failure_m_values) * len(config.failure_deltas)
    cell_index = 0

    for total_slots in config.failure_m_values:
        for requested_delta in config.failure_deltas:
            cell_index += 1
            robot_count = robot_count_from_delta(total_slots, requested_delta)
            print(
                f"[failures {cell_index}/{total_cells}] "
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
                robots, loads, quotas = generate_world(
                    robot_count=robot_count,
                    total_slots=total_slots,
                    q_bar=config.q_bar,
                    mean_quota=config.mean_quota,
                    quota_mode="moderate",
                    spatial_mode="uniform",
                    workspace_width=config.workspace_width,
                    workspace_height=config.workspace_height,
                    seed=world_seed,
                )
                base_result = solve_hungarian(
                    robots=robots,
                    loads=loads,
                    q_bar=config.q_bar,
                    allow_partial=False,
                )
                base_assigned_ids = {
                    assignment.robot_id for assignment in base_result.assignments
                }

                for treatment in config.failure_treatments:
                    treatment_seed = stable_seed(
                        config.base_seed,
                        "failure_treatment",
                        world_seed,
                        treatment,
                    )
                    rng = np.random.default_rng(treatment_seed)
                    failed_ids = select_failed_robot_ids(
                        treatment=treatment,
                        robots=robots,
                        base_result=base_result,
                        rng=rng,
                    )
                    if failed_ids is None:
                        continue

                    active_robots = [
                        robot for robot in robots if robot.id not in failed_ids
                    ]
                    recovery_result = solve_hungarian(
                        robots=active_robots,
                        loads=loads,
                        q_bar=config.q_bar,
                        allow_partial=True,
                    )
                    communication = estimate_communication(
                        original_robots=robots,
                        active_robots=active_robots,
                        result=recovery_result,
                        max_retries=config.max_retries,
                    )

                    surviving_ids = {robot.id for robot in active_robots}
                    churn = changed_assignment_fraction(
                        base_result=base_result,
                        new_result=recovery_result,
                        surviving_robot_ids=surviving_ids,
                    )

                    if recovery_result.feasible and base_result.total_cost > 0:
                        relative_cost_increase = (
                            recovery_result.total_cost - base_result.total_cost
                        ) / base_result.total_cost
                    else:
                        relative_cost_increase = math.nan

                    failed_was_assigned = any(
                        robot_id in base_assigned_ids for robot_id in failed_ids
                    )

                    records.append(
                        result_metrics(
                            study="failures",
                            seed=treatment_seed,
                            robots=active_robots,
                            loads=loads,
                            quotas=quotas,
                            result=recovery_result,
                            communication=communication,
                            workspace_width=config.workspace_width,
                            workspace_height=config.workspace_height,
                            quota_mode="moderate",
                            spatial_mode="uniform",
                            requested_delta=requested_delta,
                            treatment=treatment,
                            original_robot_count=len(robots),
                            failure_count=len(failed_ids),
                            failed_robot_was_assigned=failed_was_assigned,
                            base_total_cost=base_result.total_cost,
                            relative_cost_increase=relative_cost_increase,
                            assignment_churn=churn,
                        )
                    )

    return records


# ===============================================================
# == CSV and summaries ==========================================
# ===============================================================

def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        return

    fieldnames = list(records[0].keys())
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def parse_csv_value(value: str) -> Any:
    """Recupera bool/int/float de un CSV sin perder las etiquetas de texto."""
    normalized = value.strip()
    if normalized == "True":
        return True
    if normalized == "False":
        return False
    if normalized.lower() in {"nan", "inf", "-inf"}:
        return float(normalized)

    try:
        if any(marker in normalized for marker in (".", "e", "E")):
            return float(normalized)
        return int(normalized)
    except ValueError:
        return value


def read_csv_records(path: Path) -> list[dict[str, Any]]:
    """Lee los registros persistidos para regenerar figuras reproduciblemente."""
    if not path.is_file():
        raise FileNotFoundError(f"No existe el CSV requerido: {path}")

    with path.open(newline="", encoding="utf-8") as file:
        return [
            {field: parse_csv_value(value) for field, value in row.items()}
            for row in csv.DictReader(file)
        ]


def finite_values(records: Iterable[dict[str, Any]], field: str) -> FloatArray:
    values: list[float] = []
    for record in records:
        value = record.get(field, math.nan)
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(numeric):
            values.append(numeric)
    return np.asarray(values, dtype=np.float64)


def summarize_groups(
    records: list[dict[str, Any]],
    *,
    group_fields: tuple[str, ...],
    metric_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = tuple(record[field] for field in group_fields)
        grouped[key].append(record)

    summaries: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items(), key=lambda item: tuple(str(x) for x in item[0])):
        summary = {field: value for field, value in zip(group_fields, key, strict=True)}
        summary["replicates"] = len(group)
        summary["feasibility_rate"] = float(
            np.mean([bool(record["mission_feasible"]) for record in group])
        )
        summary["mean_coverage"] = float(
            np.mean([float(record["coverage"]) for record in group])
        )

        for metric in metric_fields:
            values = finite_values(group, metric)
            if values.size == 0:
                summary[f"{metric}_mean"] = math.nan
                summary[f"{metric}_median"] = math.nan
                summary[f"{metric}_p05"] = math.nan
                summary[f"{metric}_p95"] = math.nan
                continue

            summary[f"{metric}_mean"] = float(np.mean(values))
            summary[f"{metric}_median"] = float(np.median(values))
            summary[f"{metric}_p05"] = float(np.quantile(values, 0.05))
            summary[f"{metric}_p95"] = float(np.quantile(values, 0.95))

        summaries.append(summary)

    return summaries


def scaling_exponents(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    deltas = sorted({float(record["requested_delta"]) for record in records})

    for delta in deltas:
        delta_records = [
            record for record in records
            if float(record["requested_delta"]) == delta
        ]
        grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for record in delta_records:
            grouped[int(record["size_N_plus_M"])].append(record)

        sizes: list[float] = []
        medians: list[float] = []
        for size, group in sorted(grouped.items()):
            values = finite_values(group, "solver_wall_ns")
            if values.size > 0:
                sizes.append(float(size))
                medians.append(float(np.median(values)))

        # Smoke deliberately keeps only two sizes per delta. Two points are
        # sufficient to exercise the log-log pipeline and persist a diagnostic
        # exponent; quick/full provide the larger grids needed for analysis.
        if len(sizes) < 2:
            continue

        x = np.log(np.asarray(sizes, dtype=np.float64))
        y = np.log(np.asarray(medians, dtype=np.float64))
        slope, intercept = np.polyfit(x, y, 1)
        predicted = intercept + slope * x
        ss_res = float(np.sum((y - predicted) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0

        results.append(
            {
                "requested_delta": delta,
                "empirical_exponent_p": float(slope),
                "log_intercept": float(intercept),
                "r_squared": r_squared,
                "size_points": len(sizes),
                "min_size_N_plus_M": min(sizes),
                "max_size_N_plus_M": max(sizes),
            }
        )

    return results


# ===============================================================
# == Monte Carlo plots ==========================================
# ===============================================================

def save_figure(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()


def median_percentile_band(
    records: list[dict[str, Any]],
    metric: str,
    *,
    scale: float = 1.0,
) -> tuple[float, float, float]:
    """Devuelve mediana, P05 y P95 para visualizar las réplicas Monte Carlo."""
    values = finite_values(records, metric) * scale
    if values.size == 0:
        return math.nan, math.nan, math.nan
    return (
        float(np.median(values)),
        float(np.quantile(values, 0.05)),
        float(np.quantile(values, 0.95)),
    )


def wilson_interval(successes: int, sample_size: int) -> tuple[float, float]:
    """Intervalo de Wilson bilateral al 95 % para una proporción binomial."""
    if sample_size <= 0:
        return math.nan, math.nan

    z = 1.959963984540054
    proportion = successes / sample_size
    denominator = 1.0 + z**2 / sample_size
    center = (proportion + z**2 / (2.0 * sample_size)) / denominator
    half_width = (
        z
        * math.sqrt(
            proportion * (1.0 - proportion) / sample_size
            + z**2 / (4.0 * sample_size**2)
        )
        / denominator
    )
    return max(0.0, center - half_width), min(1.0, center + half_width)


def plot_scaling_solver_time(records: list[dict[str, Any]], output_dir: Path) -> None:
    plt.figure(figsize=(9, 6))
    for delta in sorted({float(record["requested_delta"]) for record in records}):
        delta_records = [
            record for record in records
            if float(record["requested_delta"]) == delta
        ]
        grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for record in delta_records:
            grouped[int(record["size_N_plus_M"])].append(record)

        x_values: list[int] = []
        y_values: list[float] = []
        lower_values: list[float] = []
        upper_values: list[float] = []
        for size, group in sorted(grouped.items()):
            median, lower, upper = median_percentile_band(
                group,
                "solver_wall_ns",
                scale=1e-6,
            )
            if math.isfinite(median):
                x_values.append(size)
                y_values.append(median)
                lower_values.append(lower)
                upper_values.append(upper)

        plt.loglog(
            x_values,
            y_values,
            marker="o",
            label=f"δ={delta:+.2f}",
        )
        plt.fill_between(
            x_values,
            lower_values,
            upper_values,
            alpha=0.10,
        )

    plt.xlabel("Tamaño S = N + M")
    plt.ylabel("Tiempo mediano del solver [ms]")
    plt.title("SP1.A1 — Escalabilidad del solver (mediana y P05–P95)")
    plt.grid(True, which="both", alpha=0.3)
    plt.legend()
    save_figure(output_dir / "scaling_solver_time.png")


def plot_scaling_total_time(records: list[dict[str, Any]], output_dir: Path) -> None:
    plt.figure(figsize=(9, 6))
    for delta in sorted({float(record["requested_delta"]) for record in records}):
        delta_records = [
            record for record in records
            if float(record["requested_delta"]) == delta
        ]
        grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for record in delta_records:
            grouped[int(record["size_N_plus_M"])].append(record)

        x_values: list[int] = []
        y_values: list[float] = []
        lower_values: list[float] = []
        upper_values: list[float] = []
        for size, group in sorted(grouped.items()):
            median, lower, upper = median_percentile_band(
                group,
                "total_wall_ns",
                scale=1e-6,
            )
            if math.isfinite(median):
                x_values.append(size)
                y_values.append(median)
                lower_values.append(lower)
                upper_values.append(upper)

        plt.loglog(
            x_values,
            y_values,
            marker="o",
            label=f"δ={delta:+.2f}",
        )
        plt.fill_between(
            x_values,
            lower_values,
            upper_values,
            alpha=0.10,
        )

    plt.xlabel("Tamaño S = N + M")
    plt.ylabel("Tiempo total mediano [ms]")
    plt.title("SP1.A1 — Coste total (mediana y P05–P95)")
    plt.grid(True, which="both", alpha=0.3)
    plt.legend()
    save_figure(output_dir / "scaling_total_time.png")


def plot_coverage_by_delta(records: list[dict[str, Any]], output_dir: Path) -> None:
    plt.figure(figsize=(9, 6))
    for total_slots in sorted({int(record["M"]) for record in records}):
        m_records = [record for record in records if int(record["M"]) == total_slots]
        grouped: dict[float, list[dict[str, Any]]] = defaultdict(list)
        for record in m_records:
            grouped[float(record["requested_delta"])].append(record)

        deltas: list[float] = []
        coverages: list[float] = []
        lower_values: list[float] = []
        upper_values: list[float] = []
        for delta, group in sorted(grouped.items()):
            values = finite_values(group, "coverage")
            deltas.append(delta)
            coverages.append(float(np.mean(values)))
            lower_values.append(float(np.quantile(values, 0.05)))
            upper_values.append(float(np.quantile(values, 0.95)))

        plt.plot(deltas, coverages, marker="o", label=f"M={total_slots}")
        plt.fill_between(deltas, lower_values, upper_values, alpha=0.06)

    plt.axvline(0.0, linestyle="--", linewidth=1.0)
    plt.xlabel("Balance normalizado δ = (N-M)/(N+M)")
    plt.ylabel("Cobertura media de slots")
    plt.title("SP1.A1 — Escasez, balance y superávit")
    plt.ylim(-0.02, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend()
    save_figure(output_dir / "coverage_by_delta.png")


def plot_balance_coverage(records: list[dict[str, Any]], output_dir: Path) -> None:
    plt.figure(figsize=(10, 6))
    for total_slots in sorted({int(record["M"]) for record in records}):
        grouped: dict[float, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            if int(record["M"]) == total_slots:
                grouped[float(record["requested_delta"])].append(record)

        deltas: list[float] = []
        medians: list[float] = []
        lower_values: list[float] = []
        upper_values: list[float] = []
        for delta, group in sorted(grouped.items()):
            median, lower, upper = median_percentile_band(group, "coverage")
            deltas.append(delta)
            medians.append(median)
            lower_values.append(lower)
            upper_values.append(upper)

        plt.plot(deltas, medians, marker=".", label=f"M={total_slots}")
        plt.fill_between(deltas, lower_values, upper_values, alpha=0.08)

    plt.axvline(0.0, linestyle="--", linewidth=1.0)
    plt.xlim(-1.0, 1.0)
    plt.ylim(-0.02, 1.05)
    plt.xlabel("Balance solicitado δ; extremos ±1 son límites no finitos")
    plt.ylabel("Cobertura mediana de slots")
    plt.title("SP1.A1 — Cobertura en casi todo el dominio de balance")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save_figure(output_dir / "balance_coverage_dense.png")


def plot_balance_tail_cost(records: list[dict[str, Any]], output_dir: Path) -> None:
    plt.figure(figsize=(10, 6))
    for total_slots in sorted({int(record["M"]) for record in records}):
        grouped: dict[float, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            if int(record["M"]) == total_slots:
                grouped[float(record["requested_delta"])].append(record)

        deltas: list[float] = []
        medians: list[float] = []
        lower_values: list[float] = []
        upper_values: list[float] = []
        for delta, group in sorted(grouped.items()):
            median, lower, upper = median_percentile_band(
                group,
                "normalized_assignment_cost_p95",
            )
            deltas.append(delta)
            medians.append(median)
            lower_values.append(lower)
            upper_values.append(upper)

        plt.plot(deltas, medians, marker=".", label=f"M={total_slots}")
        plt.fill_between(deltas, lower_values, upper_values, alpha=0.08)

    plt.axvline(0.0, linestyle="--", linewidth=1.0)
    plt.xlim(-1.0, 1.0)
    plt.xlabel("Balance solicitado δ; extremos ±1 son límites no finitos")
    plt.ylabel("P95 normalizado de distancia asignada")
    plt.title("SP1.A1 — Cola de coste frente al balance")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save_figure(output_dir / "balance_tail_cost.png")


def plot_memory_scaling(records: list[dict[str, Any]], output_dir: Path) -> None:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[int(record["matrix_elements"])].append(record)

    x = np.asarray(sorted(grouped), dtype=np.float64)
    y = np.asarray(
        [
            np.median(finite_values(grouped[int(elements)], "matrix_bytes"))
            / (1024**2)
            for elements in x
        ],
        dtype=np.float64,
    )
    plt.figure(figsize=(9, 6))
    plt.plot(x, y, marker="o", markersize=3)
    plt.xlabel("Elementos de la matriz N·M")
    plt.ylabel("Memoria de C [MiB]")
    plt.title("SP1.A1 — Memoria determinista de la matriz de costes")
    plt.grid(True, alpha=0.3)
    save_figure(output_dir / "matrix_memory.png")


def plot_messages_scaling(records: list[dict[str, Any]], output_dir: Path) -> None:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[int(record["N"])].append(record)

    n_values: list[int] = []
    messages: list[float] = []
    bytes_values: list[float] = []
    for n_value, group in sorted(grouped.items()):
        n_values.append(n_value)
        messages.append(float(np.median(finite_values(group, "logical_messages"))))
        bytes_values.append(float(np.median(finite_values(group, "communication_bytes"))))

    plt.figure(figsize=(9, 6))
    plt.plot(n_values, messages, marker="o")
    plt.xlabel("Número de robots N")
    plt.ylabel("Mensajes lógicos medianos")
    plt.title("SP1.A1 — Comunicación centralizada por ronda")
    plt.grid(True, alpha=0.3)
    save_figure(output_dir / "messages_by_N.png")

    plt.figure(figsize=(9, 6))
    plt.plot(n_values, np.asarray(bytes_values) / 1024.0, marker="o")
    plt.xlabel("Número de robots N")
    plt.ylabel("Volumen mediano [KiB]")
    plt.title("SP1.A1 — Volumen de comunicación")
    plt.grid(True, alpha=0.3)
    save_figure(output_dir / "communication_bytes_by_N.png")


def plot_greedy_quality(records: list[dict[str, Any]], output_dir: Path) -> None:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[int(record["M"])].append(record)

    m_values: list[int] = []
    medians: list[float] = []
    lower_values: list[float] = []
    upper_values: list[float] = []
    for total_slots, group in sorted(grouped.items()):
        median, lower, upper = median_percentile_band(
            group,
            "greedy_to_hungarian_ratio",
        )
        m_values.append(total_slots)
        medians.append(median)
        lower_values.append(lower)
        upper_values.append(upper)

    plt.figure(figsize=(9, 6))
    plt.semilogx(m_values, medians, marker="o")
    plt.fill_between(m_values, lower_values, upper_values, alpha=0.18)
    plt.axhline(1.0, linestyle="--", linewidth=1.0, color="#333333")
    plt.xlabel("Número de slots M")
    plt.ylabel("Coste greedy / coste Hungarian")
    plt.title("SP1.A1 — Ventaja de optimalidad frente a greedy")
    plt.grid(True, which="both", alpha=0.3)
    save_figure(output_dir / "greedy_quality_ratio.png")


def plot_solver_efficiency(records: list[dict[str, Any]], output_dir: Path) -> None:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[int(record["M"])].append(record)

    m_values: list[int] = []
    medians: list[float] = []
    lower_values: list[float] = []
    upper_values: list[float] = []
    for total_slots, group in sorted(grouped.items()):
        median, lower, upper = median_percentile_band(
            group,
            "solver_ns_per_matrix_element",
        )
        m_values.append(total_slots)
        medians.append(median)
        lower_values.append(lower)
        upper_values.append(upper)

    plt.figure(figsize=(9, 6))
    plt.loglog(m_values, medians, marker="o")
    plt.fill_between(m_values, lower_values, upper_values, alpha=0.18)
    plt.xlabel("Número de slots M")
    plt.ylabel("Tiempo del solver [ns / elemento de C]")
    plt.title("SP1.A1 — Eficiencia computacional normalizada")
    plt.grid(True, which="both", alpha=0.3)
    save_figure(output_dir / "solver_efficiency_per_element.png")


def plot_asymmetry_cost(records: list[dict[str, Any]], output_dir: Path) -> None:
    plt.figure(figsize=(9, 6))
    for spatial_mode in sorted({str(record["spatial_mode"]) for record in records}):
        selected = [
            record for record in records
            if str(record["spatial_mode"]) == spatial_mode
        ]
        x = np.asarray(
            [float(record["quota_asymmetry_cv"]) for record in selected],
            dtype=np.float64,
        )
        y = np.asarray(
            [float(record["normalized_cost_per_assigned_slot"]) for record in selected],
            dtype=np.float64,
        )
        plt.scatter(
            x,
            y,
            s=14,
            alpha=0.18,
            label=spatial_mode,
            rasterized=True,
        )

    plt.xlabel("Asimetría observada de cuotas CV(nₖ)")
    plt.ylabel("Coste normalizado por slot")
    plt.title("SP1.A1 — Cuotas y asimetría espacial")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save_figure(output_dir / "asymmetry_normalized_cost.png")


def plot_distance_tail_by_spatial_mode(
    records: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    modes = sorted({str(record["spatial_mode"]) for record in records})
    data = [
        finite_values(
            [record for record in records if record["spatial_mode"] == mode],
            "normalized_assignment_cost_p95",
        )
        for mode in modes
    ]

    plt.figure(figsize=(10, 6))
    plt.boxplot(data, tick_labels=modes, showfliers=False)
    plt.xticks(rotation=20, ha="right")
    plt.ylabel("P95 normalizado de distancia asignada")
    plt.title("SP1.A1 — Coste de cola por geometría espacial")
    plt.grid(True, axis="y", alpha=0.3)
    save_figure(output_dir / "distance_tail_by_spatial_mode.png")


def plot_cost_fairness_by_quota_mode(
    records: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    modes = sorted({str(record["quota_mode"]) for record in records})
    data = [
        finite_values(
            [record for record in records if record["quota_mode"] == mode],
            "assignment_cost_gini",
        )
        for mode in modes
    ]

    plt.figure(figsize=(10, 6))
    plt.boxplot(data, tick_labels=modes, showfliers=False)
    plt.xticks(rotation=20, ha="right")
    plt.ylabel("Gini de costes asignados [0=igualdad]")
    plt.title("SP1.A1 — Dispersión del coste por asimetría de cuotas")
    plt.grid(True, axis="y", alpha=0.3)
    save_figure(output_dir / "cost_fairness_by_quota_mode.png")


def treatment_order(records: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "no_failure",
        "idle_robot_failure",
        "random_assigned_failure",
        "critical_assigned_failure",
        "random_5_percent",
        "random_10_percent",
        "random_20_percent",
        "random_30_percent",
    ]
    present = {str(record["treatment"]) for record in records}
    return [name for name in preferred if name in present]


def plot_failure_feasibility(records: list[dict[str, Any]], output_dir: Path) -> None:
    treatments = treatment_order(records)
    rates: list[float] = []
    lower_errors: list[float] = []
    upper_errors: list[float] = []
    for treatment in treatments:
        selected = [record for record in records if record["treatment"] == treatment]
        successes = sum(bool(record["mission_feasible"]) for record in selected)
        rate = successes / len(selected)
        lower, upper = wilson_interval(successes, len(selected))
        rates.append(rate)
        lower_errors.append(max(0.0, rate - lower))
        upper_errors.append(max(0.0, upper - rate))

    plt.figure(figsize=(10, 6))
    plt.bar(
        np.arange(len(treatments)),
        rates,
        yerr=np.asarray([lower_errors, upper_errors]),
        capsize=4,
    )
    plt.xticks(np.arange(len(treatments)), treatments, rotation=25, ha="right")
    plt.ylabel("Tasa de factibilidad")
    plt.title("SP1.A1 — Robustez ante fallos (IC 95 % de Wilson)")
    plt.ylim(0.0, 1.05)
    plt.grid(True, axis="y", alpha=0.3)
    save_figure(output_dir / "failure_feasibility.png")


def plot_failure_churn(records: list[dict[str, Any]], output_dir: Path) -> None:
    treatments = treatment_order(records)
    data: list[FloatArray] = []
    valid_labels: list[str] = []

    for treatment in treatments:
        selected = [record for record in records if record["treatment"] == treatment]
        values = finite_values(selected, "assignment_churn")
        if values.size > 0:
            data.append(values)
            valid_labels.append(treatment)

    if not data:
        return

    plt.figure(figsize=(10, 6))
    plt.boxplot(data, tick_labels=valid_labels, showfliers=False)
    plt.xticks(rotation=25, ha="right")
    plt.ylabel("Fracción de robots supervivientes reasignados")
    plt.title("SP1.A1 — Churn de asignación después del fallo")
    plt.grid(True, axis="y", alpha=0.3)
    save_figure(output_dir / "failure_assignment_churn.png")


def plot_failure_cost_increase(records: list[dict[str, Any]], output_dir: Path) -> None:
    treatments = treatment_order(records)
    data: list[FloatArray] = []
    valid_labels: list[str] = []

    for treatment in treatments:
        selected = [record for record in records if record["treatment"] == treatment]
        values = finite_values(selected, "relative_cost_increase")
        if values.size > 0:
            data.append(values)
            valid_labels.append(treatment)

    if not data:
        return

    plt.figure(figsize=(10, 6))
    plt.boxplot(data, tick_labels=valid_labels, showfliers=False)
    plt.xticks(rotation=25, ha="right")
    plt.ylabel("Incremento relativo del coste")
    plt.title("SP1.A1 — Coste de recuperación")
    plt.grid(True, axis="y", alpha=0.3)
    save_figure(output_dir / "failure_relative_cost.png")


def random_failure_sweep() -> tuple[tuple[str, float], ...]:
    return (
        ("no_failure", 0.00),
        ("random_5_percent", 0.05),
        ("random_10_percent", 0.10),
        ("random_20_percent", 0.20),
        ("random_30_percent", 0.30),
    )


def plot_random_failure_feasibility(
    records: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    plt.figure(figsize=(9, 6))
    deltas = sorted({float(record["requested_delta"]) for record in records})
    for delta in deltas:
        x_values: list[float] = []
        rates: list[float] = []
        lower_values: list[float] = []
        upper_values: list[float] = []
        for treatment, nominal_rate in random_failure_sweep():
            selected = [
                record for record in records
                if record["treatment"] == treatment
                and float(record["requested_delta"]) == delta
            ]
            successes = sum(bool(record["mission_feasible"]) for record in selected)
            rate = successes / len(selected)
            lower, upper = wilson_interval(successes, len(selected))
            x_values.append(nominal_rate)
            rates.append(rate)
            lower_values.append(lower)
            upper_values.append(upper)

        plt.plot(x_values, rates, marker="o", label=f"δ={delta:+.2f}")
        plt.fill_between(x_values, lower_values, upper_values, alpha=0.12)

    plt.xlabel("Proporción nominal de robots fallidos")
    plt.ylabel("Tasa de factibilidad")
    plt.title("SP1.A1 — Umbral de robustez por reserva estructural")
    plt.ylim(0.0, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend()
    save_figure(output_dir / "random_failure_feasibility_curve.png")


def plot_random_failure_cost(
    records: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    plt.figure(figsize=(9, 6))
    deltas = sorted({float(record["requested_delta"]) for record in records})
    for delta in deltas:
        x_values: list[float] = []
        medians: list[float] = []
        lower_values: list[float] = []
        upper_values: list[float] = []
        for treatment, nominal_rate in random_failure_sweep():
            selected = [
                record for record in records
                if record["treatment"] == treatment
                and float(record["requested_delta"]) == delta
            ]
            median, lower, upper = median_percentile_band(
                selected,
                "relative_cost_increase",
            )
            x_values.append(nominal_rate)
            medians.append(median)
            lower_values.append(lower)
            upper_values.append(upper)

        plt.plot(x_values, medians, marker="o", label=f"δ={delta:+.2f}")
        plt.fill_between(x_values, lower_values, upper_values, alpha=0.12)

    plt.xlabel("Proporción nominal de robots fallidos")
    plt.ylabel("Incremento relativo del coste, solo recuperaciones factibles")
    plt.title("SP1.A1 — Coste de recuperación por reserva estructural")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save_figure(output_dir / "random_failure_cost_curve.png")


def generate_all_plots(
    *,
    scaling_records: list[dict[str, Any]],
    balance_records: list[dict[str, Any]],
    asymmetry_records: list[dict[str, Any]],
    failure_records: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    plots_dir = output_dir / "plots"
    plot_scaling_solver_time(scaling_records, plots_dir)
    plot_scaling_total_time(scaling_records, plots_dir)
    plot_coverage_by_delta(scaling_records, plots_dir)
    plot_balance_coverage(balance_records, plots_dir)
    plot_balance_tail_cost(balance_records, plots_dir)
    plot_memory_scaling(scaling_records, plots_dir)
    plot_messages_scaling(scaling_records, plots_dir)
    plot_greedy_quality(scaling_records, plots_dir)
    plot_solver_efficiency(scaling_records, plots_dir)
    plot_asymmetry_cost(asymmetry_records, plots_dir)
    plot_distance_tail_by_spatial_mode(asymmetry_records, plots_dir)
    plot_cost_fairness_by_quota_mode(asymmetry_records, plots_dir)
    plot_failure_feasibility(failure_records, plots_dir)
    plot_failure_churn(failure_records, plots_dir)
    plot_failure_cost_increase(failure_records, plots_dir)
    plot_random_failure_feasibility(failure_records, plots_dir)
    plot_random_failure_cost(failure_records, plots_dir)


def regenerate_plots_from_csv(output_dir: Path) -> None:
    """Regenera las figuras sin repetir la campaña numérica."""
    scaling_records = read_csv_records(output_dir / "mc_scaling.csv")
    balance_records = read_csv_records(output_dir / "mc_balance.csv")
    asymmetry_records = read_csv_records(output_dir / "mc_asymmetry.csv")
    failure_records = read_csv_records(output_dir / "mc_failures.csv")
    generate_all_plots(
        scaling_records=scaling_records,
        balance_records=balance_records,
        asymmetry_records=asymmetry_records,
        failure_records=failure_records,
        output_dir=output_dir,
    )
    print(f"Figuras regeneradas desde CSV: {(output_dir / 'plots').resolve()}")


# ===============================================================
# == Study orchestration ========================================
# ===============================================================

DENSE_SWEEP_MIN_POINTS = 12
DENSE_SCALING_DELTAS = (
    -0.40,
    -0.33,
    -0.27,
    -0.20,
    -0.13,
    -0.07,
    0.00,
    0.07,
    0.13,
    0.20,
    0.27,
    0.33,
    0.40,
)
EXTENDED_BALANCE_DELTAS = tuple(
    round(-0.95 + 0.05 * index, 2)
    for index in range(39)
)


def config_for_profile(profile: str) -> MonteCarloConfig:
    common = {
        "q_bar": 5.0,
        "workspace_width": 100.0,
        "workspace_height": 100.0,
        "mean_quota": 3.0,
        "base_seed": 20260728,
        "asymmetry_delta": 0.20,
        "quota_modes": ("symmetric", "low", "moderate", "high", "extreme"),
        "spatial_modes": (
            "uniform",
            "clustered",
            "separated",
            "ring",
            "corridor",
        ),
        "failure_deltas": (0.00, 0.20, 0.33),
        "failure_treatments": (
            "no_failure",
            "idle_robot_failure",
            "random_assigned_failure",
            "critical_assigned_failure",
            "random_5_percent",
            "random_10_percent",
            "random_20_percent",
            "random_30_percent",
        ),
        "max_retries": 3,
    }

    if profile == "smoke":
        return MonteCarloConfig(
            **common,
            seeds_per_cell=2,
            scaling_m_values=(10, 20),
            scaling_deltas=(-0.33, -0.20, 0.00, 0.20, 0.33),
            balance_m_values=(20,),
            balance_deltas=(-0.95, -0.50, 0.00, 0.50, 0.95),
            asymmetry_m_values=(20,),
            failure_m_values=(20,),
        )

    if profile == "quick":
        return MonteCarloConfig(
            **common,
            seeds_per_cell=10,
            scaling_m_values=(10, 13, 17, 22, 29, 38, 49, 64, 83, 108, 132, 160),
            scaling_deltas=DENSE_SCALING_DELTAS,
            balance_m_values=(20, 80),
            balance_deltas=EXTENDED_BALANCE_DELTAS,
            asymmetry_m_values=(40, 160),
            failure_m_values=(40, 160),
        )

    if profile == "full":
        return MonteCarloConfig(
            **common,
            seeds_per_cell=60,
            scaling_m_values=(
                10,
                14,
                20,
                28,
                40,
                56,
                80,
                112,
                160,
                226,
                320,
                452,
                640,
            ),
            scaling_deltas=DENSE_SCALING_DELTAS,
            balance_m_values=(20, 40, 80, 160),
            balance_deltas=EXTENDED_BALANCE_DELTAS,
            asymmetry_m_values=(40, 160, 640),
            failure_m_values=(40, 160, 640),
        )

    raise ValueError(f"Perfil desconocido: {profile}")


def run_monte_carlo(config: MonteCarloConfig, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    print("\n" + "=" * 72)
    print("SP1.A1 — ESTUDIO MONTE CARLO")
    print("=" * 72)
    print(json.dumps(asdict(config), indent=2, ensure_ascii=False))

    scaling_records = run_scaling_study(config)
    balance_records = run_balance_study(config)
    asymmetry_records = run_asymmetry_study(config)
    failure_records = run_failure_study(config)
    all_records = (
        scaling_records
        + balance_records
        + asymmetry_records
        + failure_records
    )

    write_csv(output_dir / "mc_scaling.csv", scaling_records)
    write_csv(output_dir / "mc_balance.csv", balance_records)
    write_csv(output_dir / "mc_asymmetry.csv", asymmetry_records)
    write_csv(output_dir / "mc_failures.csv", failure_records)
    write_csv(output_dir / "mc_all_runs.csv", all_records)

    scaling_summary = summarize_groups(
        scaling_records,
        group_fields=("M", "requested_delta"),
        metric_fields=(
            "solver_wall_ns",
            "total_wall_ns",
            "total_cpu_ns",
            "matrix_bytes",
            "normalized_cost_per_assigned_slot",
            "normalized_assignment_cost_p95",
            "greedy_to_hungarian_ratio",
            "hungarian_saving_vs_greedy",
            "relative_gap_to_lower_bound",
            "assignment_cost_gini",
            "robot_utilization",
            "solver_ns_per_matrix_element",
            "metrics_wall_ns",
            "logical_messages",
            "communication_bytes",
        ),
    )
    balance_summary = summarize_groups(
        balance_records,
        group_fields=("M", "requested_delta"),
        metric_fields=(
            "coverage",
            "normalized_cost_per_assigned_slot",
            "normalized_assignment_cost_p95",
            "assignment_cost_max",
            "greedy_to_hungarian_ratio",
            "robot_utilization",
            "solver_wall_ns",
            "matrix_bytes",
        ),
    )
    asymmetry_summary = summarize_groups(
        asymmetry_records,
        group_fields=("M", "quota_mode", "spatial_mode"),
        metric_fields=(
            "quota_asymmetry_cv",
            "cost_asymmetry_cv",
            "normalized_cost_per_assigned_slot",
            "normalized_assignment_cost_p95",
            "assignment_cost_gini",
            "assignment_cost_jain",
            "load_mean_cost_cv",
            "solver_wall_ns",
            "total_wall_ns",
        ),
    )
    failure_summary = summarize_groups(
        failure_records,
        group_fields=("M", "requested_delta", "treatment"),
        metric_fields=(
            "coverage",
            "relative_cost_increase",
            "assignment_churn",
            "normalized_assignment_cost_p95",
            "greedy_to_hungarian_ratio",
            "robot_utilization",
            "solver_wall_ns",
            "total_wall_ns",
            "logical_messages",
            "communication_bytes",
        ),
    )

    write_csv(output_dir / "summary_scaling.csv", scaling_summary)
    write_csv(output_dir / "summary_balance.csv", balance_summary)
    write_csv(output_dir / "summary_asymmetry.csv", asymmetry_summary)
    write_csv(output_dir / "summary_failures.csv", failure_summary)
    write_csv(output_dir / "scaling_exponents.csv", scaling_exponents(scaling_records))

    with (output_dir / "config.json").open("w", encoding="utf-8") as file:
        json.dump(asdict(config), file, indent=2, ensure_ascii=False)

    generate_all_plots(
        scaling_records=scaling_records,
        balance_records=balance_records,
        asymmetry_records=asymmetry_records,
        failure_records=failure_records,
        output_dir=output_dir,
    )

    print("\nEstudio completado.")
    print(f"Resultados: {output_dir.resolve()}")
    print(f"Ejecuciones totales: {len(all_records)}")


# ===============================================================
# == Original demonstration =====================================
# ===============================================================

def run_demo(output_dir: Path, show: bool) -> None:
    q_bar = 5.0

    robots = [
        Robot(id="R1", x=0.0, y=0.0, capacity=q_bar),
        Robot(id="R2", x=1.0, y=1.0, capacity=q_bar),
        Robot(id="R3", x=2.0, y=0.5, capacity=q_bar),
        Robot(id="R4", x=8.0, y=1.0, capacity=q_bar),
        Robot(id="R5", x=7.0, y=3.0, capacity=q_bar),
        Robot(id="R6", x=5.5, y=5.0, capacity=q_bar),
        Robot(id="R7", x=2.5, y=5.5, capacity=q_bar),
        Robot(id="R8", x=9.0, y=6.0, capacity=q_bar),
    ]

    loads = [
        Load(id="L1", x=0.5, y=0.2, mass=5.0),
        Load(id="L2", x=7.5, y=2.0, mass=8.0),
        Load(id="L3", x=4.0, y=5.0, mass=11.0),
    ]

    result = solve_hungarian(
        robots=robots,
        loads=loads,
        q_bar=q_bar,
        allow_partial=False,
    )
    validate_result(
        result=result,
        robots=robots,
        loads=loads,
        q_bar=q_bar,
    )
    print_result(result)
    print_cost_matrix(robots=robots, result=result)
    plot_hungarian_assignment(
        robots=robots,
        loads=loads,
        result=result,
        output_path=output_dir / "sp1_a1_hungarian.png",
        show=show,
    )


# ===============================================================
# == CLI ========================================================
# ===============================================================

def parse_legacy_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "SP1.A1: Hungarian homogéneo + campañas Monte Carlo de escala, "
            "balance extremo, asimetría, fallos, calidad, CPU y comunicación."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("demo", "montecarlo", "plots", "all"),
        default="all",
        help="Qué ejecutar; plots regenera figuras desde CSV existentes.",
    )
    parser.add_argument(
        "--profile",
        choices=("smoke", "quick", "full"),
        default="quick",
        help=(
            "smoke: prueba rápida; quick: campaña de trabajo; "
            "full: campaña confirmatoria densa con 60 semillas por celda."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("sp1_a1_results"),
        help="Directorio para CSV, resúmenes y figuras.",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="No abrir la figura interactiva del demo.",
    )
    return parser.parse_args()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "SP1.A1: Hungarian homogéneo, campañas Monte Carlo y "
            "visualización reproducible de geometrías espaciales."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("demo", "montecarlo", "plots", "geometry-viz", "all"),
        default="all",
        help=(
            "Qué ejecutar; plots regenera PNG desde CSV/configuración y "
            "geometry-viz crea el paquete geométrico."
        ),
    )
    parser.add_argument(
        "--profile",
        choices=("smoke", "quick", "full"),
        default="quick",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("sp1_a1_results"),
    )
    parser.add_argument("--viz-seed", type=int, default=20260728)
    parser.add_argument("--viz-m", type=int, default=20)
    parser.add_argument("--viz-delta", type=float, default=0.20)
    parser.add_argument("--viz-fps", type=int, default=30)
    parser.add_argument("--viz-duration", type=float, default=12.0)

    video_group = parser.add_mutually_exclusive_group()
    video_group.add_argument(
        "--make-videos",
        dest="make_videos",
        action="store_true",
    )
    video_group.add_argument(
        "--no-make-videos",
        dest="make_videos",
        action="store_false",
    )
    parser.set_defaults(make_videos=None)

    motion_group = parser.add_mutually_exclusive_group()
    motion_group.add_argument(
        "--motion-preview",
        dest="motion_preview",
        action="store_true",
    )
    motion_group.add_argument(
        "--no-motion-preview",
        dest="motion_preview",
        action="store_false",
    )
    parser.set_defaults(motion_preview=True)

    show_group = parser.add_mutually_exclusive_group()
    show_group.add_argument("--show", dest="show", action="store_true")
    show_group.add_argument("--no-show", dest="show", action="store_false")
    parser.set_defaults(show=False)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = config_for_profile(args.profile)

    if args.mode in {"demo", "all"}:
        run_demo(output_dir=args.output_dir, show=args.show)

    if args.mode in {"montecarlo", "all"}:
        run_monte_carlo(config=config, output_dir=args.output_dir)

    if args.mode == "plots":
        required_csv = (
            "mc_scaling.csv",
            "mc_balance.csv",
            "mc_asymmetry.csv",
            "mc_failures.csv",
        )
        if all((args.output_dir / name).is_file() for name in required_csv):
            regenerate_plots_from_csv(output_dir=args.output_dir)
        else:
            print(
                "No se encontraron todos los CSV Monte Carlo; "
                "se regenerarán únicamente los PNG geométricos."
            )

    if args.mode in {"plots", "geometry-viz", "all"}:
        make_videos = (
            args.make_videos
            if args.make_videos is not None
            else args.mode == "geometry-viz"
        )
        run_geometry_visualization(
            seed=args.viz_seed,
            m_slots=args.viz_m,
            delta=args.viz_delta,
            q_bar=config.q_bar,
            workspace_width=config.workspace_width,
            workspace_height=config.workspace_height,
            fps=args.viz_fps,
            duration_seconds=args.viz_duration,
            make_videos=make_videos,
            include_motion_preview=args.motion_preview,
            output_dir=args.output_dir,
            show=args.show,
        )


if __name__ == "__main__":
    main()

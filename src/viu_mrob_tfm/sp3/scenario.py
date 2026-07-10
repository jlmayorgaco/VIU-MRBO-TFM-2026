"""Scenario generator for SP3 role/slot wrench-feasibility experiments."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

import numpy as np

from viu_mrob_tfm.domain import CapacityModel, LoadSpec, RobotRuntimeState, RobotSpec, WarehouseMap, WorldState
from viu_mrob_tfm.domain.load import WrenchDemand
from viu_mrob_tfm.domain.robot import BatteryModel
from viu_mrob_tfm.scenarios.base import BaseScenario, ScenarioMetadata


@dataclass(frozen=True, slots=True)
class ContactSlot:
    """Planar one-way contact slot attached to a load."""

    offset_xy: np.ndarray
    direction_xy: np.ndarray
    role: str
    max_robots_per_slot: int = 1

    def __post_init__(self) -> None:
        offset = np.asarray(self.offset_xy, dtype=float)
        direction = np.asarray(self.direction_xy, dtype=float)
        if offset.shape != (2,) or direction.shape != (2,):
            raise ValueError("ContactSlot offset_xy and direction_xy must be 2D vectors.")
        norm = float(np.linalg.norm(direction))
        if norm <= 1e-12:
            raise ValueError("ContactSlot direction_xy must be nonzero.")
        if self.max_robots_per_slot != 1:
            raise ValueError("SP3 v1 supports max_robots_per_slot = 1 only.")
        object.__setattr__(self, "offset_xy", offset)
        object.__setattr__(self, "direction_xy", direction / norm)


@dataclass(frozen=True, slots=True)
class SP3Problem:
    """World plus SP3-only contact-slot geometry."""

    world: WorldState
    load_slots: tuple[tuple[ContactSlot, ...], ...]
    scenario_generator: str
    scenario_variant_id: str
    communication_radius: float = float("inf")
    wrench_tolerance: float = 0.05
    force_ref_n: float = 60.0
    torque_ref_nm: float = 60.0


@dataclass(frozen=True, slots=True)
class SP3WrenchScenarioParams:
    """Parameters for one SP3 wrench-aware world."""

    generator: str = "point_load_degenerate"
    n_robots: int = 6
    n_loads: int = 1
    world_size: tuple[float, float] = (18.0, 18.0)
    robot_force_n: float = 36.0
    robot_payload_kg: float = 28.0
    robot_force_cv: float = 0.04
    position_noise_std: float = 0.15
    communication_radius: float = float("inf")
    wrench_tolerance: float = 0.05
    force_ref_n: float = 60.0
    torque_ref_nm: float = 60.0


class SP3WrenchScenario(BaseScenario):
    """Build deterministic SP3 role/slot worlds from a seed."""

    scenario_id = "SP3_wrench"
    metadata = ScenarioMetadata(
        name="SP3 role-slot wrench feasibility",
        description="Coalition recruitment with explicit load contact slots and planar wrench feasibility.",
        hypothesis="Scalar capacity can be feasible while role/slot wrench feasibility fails.",
    )

    def __init__(self, params: SP3WrenchScenarioParams | None = None) -> None:
        self.params = params or SP3WrenchScenarioParams()

    def build(self, seed: int = 2026) -> SP3Problem:
        params = self.params
        key = params.generator.lower()
        if params.n_robots < 1:
            raise ValueError("SP3 requires at least one robot.")
        if params.n_loads < 1:
            raise ValueError("SP3 requires at least one load.")
        rng = np.random.default_rng(seed)
        width, height = params.world_size
        map_size = float(max(width, height))
        blueprints = _load_blueprints(key, int(params.n_loads))
        loads: list[LoadSpec] = []
        slot_groups: list[tuple[ContactSlot, ...]] = []
        slot_targets: list[np.ndarray] = []
        centers = _load_centers(key, len(blueprints), width, height)

        for load_idx, blueprint in enumerate(blueprints):
            pickup = centers[load_idx] + rng.normal(0.0, params.position_noise_std, size=2)
            destination = pickup + np.array([2.0, 0.0], dtype=float)
            wrench = np.asarray(blueprint["wrench"], dtype=float)
            slots = tuple(
                ContactSlot(
                    offset_xy=np.asarray(slot["offset"], dtype=float),
                    direction_xy=np.asarray(slot["direction"], dtype=float),
                    role=str(slot["role"]),
                )
                for slot in blueprint["slots"]
            )
            loads.append(
                LoadSpec(
                    identifier=f"load-{load_idx + 1:02d}",
                    pickup=pickup,
                    destination=destination,
                    mass_kg=float(blueprint["mass_kg"]),
                    length_m=float(blueprint["length_m"]),
                    width_m=float(blueprint["width_m"]),
                    min_capacity_kg=float(blueprint["scalar_demand_kg"]),
                    min_coalition_size=int(blueprint["min_coalition_size"]),
                    reward=float(blueprint["reward"]),
                    wrench=WrenchDemand(force_xy=wrench[:2], torque_z=float(wrench[2])),
                )
            )
            slot_groups.append(slots)
            for slot in slots:
                slot_targets.append(pickup + slot.offset_xy)

        robots: list[RobotRuntimeState] = []
        target_positions = _robot_start_positions(slot_targets, params.n_robots, params.world_size, rng)
        sigma = max(float(params.robot_force_cv), 1e-9)
        force_limits = rng.lognormal(mean=np.log(float(params.robot_force_n)), sigma=sigma, size=params.n_robots)
        force_limits = np.clip(force_limits, 0.65 * params.robot_force_n, 1.35 * params.robot_force_n)
        for idx in range(params.n_robots):
            force = float(force_limits[idx])
            payload = float(max(8.0, params.robot_payload_kg * force / max(params.robot_force_n, 1e-9)))
            robots.append(
                RobotRuntimeState(
                    spec=RobotSpec(
                        identifier=f"amr-{idx + 1:02d}",
                        capacity=CapacityModel(
                            payload_kg=payload,
                            force_limit_n=force,
                            torque_limit_nm=1.5 * force,
                        ),
                        battery=BatteryModel(
                            capacity_wh=float(rng.uniform(420.0, 640.0)),
                            reserve_fraction=0.15,
                            discharge_per_meter=float(rng.uniform(0.008, 0.014)),
                        ),
                        max_speed=float(rng.uniform(0.52, 0.78)),
                    ),
                    position=target_positions[idx],
                    heading=float(rng.uniform(-np.pi, np.pi)),
                    battery_fraction=float(rng.uniform(0.72, 1.0)),
                )
            )

        return SP3Problem(
            world=WorldState(robots=robots, loads=loads, map=WarehouseMap(size_m=map_size)),
            load_slots=tuple(slot_groups),
            scenario_generator=key,
            scenario_variant_id=f"{key}_seed{seed}",
            communication_radius=float(params.communication_radius),
            wrench_tolerance=float(params.wrench_tolerance),
            force_ref_n=float(params.force_ref_n),
            torque_ref_nm=float(params.torque_ref_nm),
        )


def scenario_params_for_generator(generator: str) -> tuple[SP3WrenchScenarioParams, ...]:
    """Return deterministic parameter bundles for named SP3 generators."""

    key = generator.lower()
    if key in {"setup", "sp3_0", "sp3.0"}:
        return (SP3WrenchScenarioParams(generator="bar_torque_pure", n_robots=4, n_loads=1, position_noise_std=0.0),)
    if key in {
        "point_load_degenerate",
        "bar_torque_pure",
        "one_sided_push",
        "off_center_com",
        "long_payload_slots",
        "slot_saturation",
        "pose_transport_rotate",
        "pose_push_overactuated",
        "pose_push_drag_balanced",
        "pose_cargo_scarce",
    }:
        n_robots = {
            "point_load_degenerate": 4,
            "bar_torque_pure": 4,
            "one_sided_push": 5,
            "off_center_com": 6,
            "long_payload_slots": 8,
            "slot_saturation": 6,
            "pose_transport_rotate": 6,
            "pose_push_overactuated": 8,
            "pose_push_drag_balanced": 4,
            "pose_cargo_scarce": 3,
        }[key]
        n_loads = {
            "long_payload_slots": 2,
            "pose_push_overactuated": 2,
            "pose_push_drag_balanced": 4,
            "pose_cargo_scarce": 5,
        }.get(key, 1)
        return (SP3WrenchScenarioParams(generator=key, n_robots=n_robots, n_loads=n_loads),)
    if key in {"monte_carlo", "sp3_mc"}:
        return (SP3WrenchScenarioParams(generator="monte_carlo", n_robots=8, n_loads=2),)
    raise ValueError(f"Unknown SP3 scenario generator: {generator}")


def sample_monte_carlo_params(seed: int, base: SP3WrenchScenarioParams | None = None) -> SP3WrenchScenarioParams:
    """Sample one SP3 Monte Carlo parameter bundle from a seed."""

    rng = np.random.default_rng(seed)
    params = base or SP3WrenchScenarioParams(generator="monte_carlo")
    generator = str(rng.choice(["bar_torque_pure", "one_sided_push", "off_center_com", "long_payload_slots", "slot_saturation"]))
    n_robots = {"bar_torque_pure": 4, "one_sided_push": 5, "off_center_com": 6, "long_payload_slots": 8, "slot_saturation": 6}[generator]
    n_loads = 2 if generator == "long_payload_slots" else 1
    return replace(
        params,
        generator=generator,
        n_robots=n_robots,
        n_loads=n_loads,
        robot_force_n=float(rng.uniform(30.0, 44.0)),
        robot_payload_kg=float(rng.uniform(22.0, 34.0)),
        robot_force_cv=float(rng.uniform(0.02, 0.12)),
        position_noise_std=float(rng.uniform(0.02, 0.35)),
        communication_radius=float(rng.choice([np.inf, 10.0, 7.0, 5.0])),
    )


def iter_sp3_problems(generators: Iterable[str], seeds: Iterable[int]) -> Iterable[tuple[str, str, int, SP3WrenchScenarioParams, SP3Problem]]:
    """Yield SP3 problems for named generators and seeds."""

    for generator in generators:
        key = generator.lower()
        base_params = scenario_params_for_generator(key)
        for seed in seeds:
            if key in {"monte_carlo", "sp3_mc"}:
                params = sample_monte_carlo_params(seed, base_params[0])
                problem = SP3WrenchScenario(params).build(seed)
                yield key, f"{key}_{params.generator}_seed{seed}", seed, params, problem
            else:
                for idx, params in enumerate(base_params):
                    problem = SP3WrenchScenario(params).build(seed + 997 * idx)
                    yield key, f"{key}_v{idx:02d}", seed, params, problem


def _load_centers(key: str, count: int, width: float, height: float) -> list[np.ndarray]:
    if count == 1:
        return [np.zeros(2, dtype=float)]
    xs = np.linspace(-0.25 * width, 0.25 * width, count)
    return [np.array([float(x), 0.15 * height * ((idx % 2) * 2 - 1)], dtype=float) for idx, x in enumerate(xs)]


def _robot_start_positions(slot_targets: list[np.ndarray], n_robots: int, world_size: tuple[float, float], rng: np.random.Generator) -> np.ndarray:
    width, height = world_size
    half = np.array([0.5 * width, 0.5 * height], dtype=float)
    positions: list[np.ndarray] = []
    for target in slot_targets[:n_robots]:
        positions.append(np.asarray(target, dtype=float) + rng.normal(0.0, 1.2, size=2))
    while len(positions) < n_robots:
        positions.append(rng.uniform(-0.75 * half, 0.75 * half))
    return np.clip(np.vstack(positions), -0.9 * half, 0.9 * half)


def _load_blueprints(key: str, n_loads: int) -> list[dict[str, object]]:
    if key == "point_load_degenerate":
        return [
            {
                "wrench": [48.0, 0.0, 0.0],
                "mass_kg": 42.0,
                "scalar_demand_kg": 42.0,
                "min_coalition_size": 2,
                "length_m": 0.9,
                "width_m": 0.9,
                "reward": 2.0,
                "slots": [
                    {"offset": [0.0, 0.0], "direction": [1.0, 0.0], "role": "point_push_a"},
                    {"offset": [0.0, 0.0], "direction": [1.0, 0.0], "role": "point_push_b"},
                ],
            }
        ]
    if key == "bar_torque_pure":
        return [
            {
                "wrench": [0.0, 0.0, -60.0],
                "mass_kg": 38.0,
                "scalar_demand_kg": 38.0,
                "min_coalition_size": 2,
                "length_m": 3.2,
                "width_m": 0.55,
                "reward": 3.5,
                "slots": [
                    {"offset": [0.0, 1.0], "direction": [1.0, 0.0], "role": "upper_push_right"},
                    {"offset": [0.0, -1.0], "direction": [-1.0, 0.0], "role": "lower_push_left"},
                ],
            }
        ]
    if key == "one_sided_push":
        return [
            {
                "wrench": [-54.0, 0.0, 0.0],
                "mass_kg": 44.0,
                "scalar_demand_kg": 44.0,
                "min_coalition_size": 2,
                "length_m": 2.4,
                "width_m": 0.9,
                "reward": 2.7,
                "slots": [
                    {"offset": [-0.9, 0.45], "direction": [1.0, 0.0], "role": "left_side_push_right_a"},
                    {"offset": [-0.9, -0.45], "direction": [1.0, 0.0], "role": "left_side_push_right_b"},
                    {"offset": [-0.9, 0.0], "direction": [1.0, 0.0], "role": "left_side_push_right_c"},
                ],
            }
        ]
    if key == "off_center_com":
        return [
            {
                "wrench": [54.0, 0.0, -42.0],
                "mass_kg": 46.0,
                "scalar_demand_kg": 46.0,
                "min_coalition_size": 2,
                "length_m": 2.8,
                "width_m": 1.0,
                "reward": 3.0,
                "slots": [
                    {"offset": [0.0, 0.95], "direction": [1.0, 0.0], "role": "top_push_right"},
                    {"offset": [0.0, -0.95], "direction": [1.0, 0.0], "role": "bottom_push_right"},
                    {"offset": [-1.15, 0.0], "direction": [0.0, 1.0], "role": "rear_push_up"},
                ],
            }
        ]
    if key == "pose_transport_rotate":
        return [
            {
                "wrench": [26.0, 14.0, 58.0],
                "mass_kg": 40.0,
                "scalar_demand_kg": 40.0,
                "min_coalition_size": 4,
                "length_m": 3.4,
                "width_m": 1.25,
                "reward": 4.0,
                "slots": [
                    {"offset": [0.0, 0.95], "direction": [-1.0, 0.0], "role": "top_push_left_positive_tau"},
                    {"offset": [0.0, -0.95], "direction": [1.0, 0.0], "role": "bottom_push_right_positive_tau"},
                    {"offset": [0.0, 0.0], "direction": [1.0, 0.0], "role": "center_push_right_translation_x"},
                    {"offset": [0.0, -0.6], "direction": [0.0, 1.0], "role": "bottom_center_push_up_translation_y"},
                ],
            }
        ]
    if key == "pose_push_overactuated":
        return [
            {
                "wrench": [78.0, 0.0, 24.0],
                "mass_kg": 56.0,
                "scalar_demand_kg": 56.0,
                "min_coalition_size": 3,
                "length_m": 3.0,
                "width_m": 1.1,
                "reward": 5.0,
                "slots": [
                    {"offset": [-1.10, 0.48], "direction": [1.0, 0.0], "role": "rear_left_push_forward"},
                    {"offset": [-1.10, -0.48], "direction": [1.0, 0.0], "role": "rear_right_push_forward"},
                    {"offset": [0.70, -0.55], "direction": [0.0, 1.0], "role": "side_push_up_torque"},
                    {"offset": [1.20, 0.00], "direction": [-1.0, 0.0], "role": "front_drag_brake"},
                ],
            },
            {
                "wrench": [32.0, 0.0, 0.0],
                "mass_kg": 24.0,
                "scalar_demand_kg": 24.0,
                "min_coalition_size": 1,
                "length_m": 1.6,
                "width_m": 0.8,
                "reward": 1.0,
                "slots": [
                    {"offset": [-0.55, 0.0], "direction": [1.0, 0.0], "role": "secondary_push"},
                ],
            },
        ][:n_loads]
    if key == "pose_push_drag_balanced":
        return [
            {
                "wrench": [28.0, 52.0, -42.0],
                "mass_kg": 48.0,
                "scalar_demand_kg": 48.0,
                "min_coalition_size": 3,
                "length_m": 2.8,
                "width_m": 1.15,
                "reward": 5.5,
                "slots": [
                    {"offset": [-1.00, -0.45], "direction": [1.0, 0.0], "role": "rear_push_x"},
                    {"offset": [1.00, 0.45], "direction": [-1.0, 0.0], "role": "front_drag_x"},
                    {"offset": [-0.35, -0.62], "direction": [0.0, 1.0], "role": "lower_push_y"},
                    {"offset": [0.75, 0.62], "direction": [0.0, -1.0], "role": "upper_drag_y"},
                ],
            },
            {
                "wrench": [30.0, 0.0, 0.0],
                "mass_kg": 26.0,
                "scalar_demand_kg": 26.0,
                "min_coalition_size": 1,
                "length_m": 1.7,
                "width_m": 0.8,
                "reward": 1.1,
                "slots": [{"offset": [-0.6, 0.0], "direction": [1.0, 0.0], "role": "distractor_push_x"}],
            },
            {
                "wrench": [0.0, 30.0, 0.0],
                "mass_kg": 26.0,
                "scalar_demand_kg": 26.0,
                "min_coalition_size": 1,
                "length_m": 1.7,
                "width_m": 0.8,
                "reward": 1.1,
                "slots": [{"offset": [0.0, -0.6], "direction": [0.0, 1.0], "role": "distractor_push_y"}],
            },
            {
                "wrench": [24.0, 0.0, 10.0],
                "mass_kg": 22.0,
                "scalar_demand_kg": 22.0,
                "min_coalition_size": 1,
                "length_m": 1.4,
                "width_m": 0.7,
                "reward": 1.0,
                "slots": [{"offset": [0.0, -0.45], "direction": [1.0, 0.0], "role": "distractor_torque"}],
            },
        ][:n_loads]
    if key == "pose_cargo_scarce":
        return [
            {
                "wrench": [38.0, -36.0, 72.0],
                "mass_kg": 68.0,
                "scalar_demand_kg": 68.0,
                "min_coalition_size": 3,
                "length_m": 4.2,
                "width_m": 1.35,
                "reward": 6.0,
                "slots": [
                    {"offset": [0.0, 0.95], "direction": [-1.0, 0.0], "role": "top_drag_left_positive_tau"},
                    {"offset": [0.0, -0.95], "direction": [1.0, 0.0], "role": "bottom_push_right_positive_tau"},
                    {"offset": [-1.65, 0.0], "direction": [0.0, -1.0], "role": "rear_push_down_translation"},
                    {"offset": [1.65, 0.0], "direction": [0.0, -1.0], "role": "front_push_down_translation"},
                ],
            },
            {
                "wrench": [26.0, 0.0, 0.0],
                "mass_kg": 20.0,
                "scalar_demand_kg": 20.0,
                "min_coalition_size": 1,
                "length_m": 1.3,
                "width_m": 0.7,
                "reward": 0.9,
                "slots": [{"offset": [-0.45, 0.0], "direction": [1.0, 0.0], "role": "small_cargo_push"}],
            },
            {
                "wrench": [0.0, 24.0, 0.0],
                "mass_kg": 20.0,
                "scalar_demand_kg": 20.0,
                "min_coalition_size": 1,
                "length_m": 1.3,
                "width_m": 0.7,
                "reward": 0.9,
                "slots": [{"offset": [0.0, -0.45], "direction": [0.0, 1.0], "role": "small_cargo_lift_y"}],
            },
            {
                "wrench": [20.0, 0.0, -8.0],
                "mass_kg": 18.0,
                "scalar_demand_kg": 18.0,
                "min_coalition_size": 1,
                "length_m": 1.2,
                "width_m": 0.6,
                "reward": 0.8,
                "slots": [{"offset": [0.0, 0.35], "direction": [1.0, 0.0], "role": "small_cargo_torque"}],
            },
            {
                "wrench": [18.0, 18.0, 0.0],
                "mass_kg": 18.0,
                "scalar_demand_kg": 18.0,
                "min_coalition_size": 1,
                "length_m": 1.2,
                "width_m": 0.6,
                "reward": 0.8,
                "slots": [{"offset": [-0.35, -0.35], "direction": [0.707, 0.707], "role": "small_cargo_diag"}],
            },
        ][:n_loads]
    if key == "long_payload_slots":
        return [
            {
                "wrench": [70.0, 0.0, 0.0],
                "mass_kg": 62.0,
                "scalar_demand_kg": 62.0,
                "min_coalition_size": 3,
                "length_m": 4.6,
                "width_m": 0.7,
                "reward": 4.0,
                "slots": [
                    {"offset": [-1.8, 0.45], "direction": [1.0, 0.0], "role": "front_left_push"},
                    {"offset": [-1.8, -0.45], "direction": [1.0, 0.0], "role": "front_right_push"},
                    {"offset": [1.8, 0.0], "direction": [1.0, 0.0], "role": "rear_center_push"},
                ],
            },
            {
                "wrench": [0.0, 48.0, 0.0],
                "mass_kg": 44.0,
                "scalar_demand_kg": 44.0,
                "min_coalition_size": 2,
                "length_m": 3.2,
                "width_m": 0.8,
                "reward": 3.0,
                "slots": [
                    {"offset": [-1.2, 0.0], "direction": [0.0, 1.0], "role": "left_push_up"},
                    {"offset": [1.2, 0.0], "direction": [0.0, 1.0], "role": "right_push_up"},
                ],
            },
        ][:n_loads]
    if key == "slot_saturation":
        return [
            {
                "wrench": [0.0, 0.0, -95.0],
                "mass_kg": 52.0,
                "scalar_demand_kg": 52.0,
                "min_coalition_size": 2,
                "length_m": 2.2,
                "width_m": 0.75,
                "reward": 3.2,
                "slots": [
                    {"offset": [0.0, 0.45], "direction": [1.0, 0.0], "role": "short_arm_top"},
                    {"offset": [0.0, -0.45], "direction": [-1.0, 0.0], "role": "short_arm_bottom"},
                ],
            }
        ]
    raise ValueError(f"Unknown SP3 load blueprint: {key}")

"""Scenario generator for SP6 operational robustness and recovery."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

import numpy as np

from viu_mrob_tfm.domain import CapacityModel, LoadSpec, Obstacle, RobotRuntimeState, RobotSpec, WarehouseMap, WorldState
from viu_mrob_tfm.domain.load import WrenchDemand
from viu_mrob_tfm.domain.robot import BatteryModel
from viu_mrob_tfm.scenarios.base import BaseScenario, ScenarioMetadata
from viu_mrob_tfm.sp3.scenario import ContactSlot


@dataclass(frozen=True, slots=True)
class SP6EventSpec:
    """One exogenous degradation event in an SP6 rollout."""

    kind: str = "communication_radius_decay"
    time_s: float = 8.0
    robot_indices: tuple[int, ...] = ()
    communication_radius_after_m: float | None = None
    battery_fraction_after: float | None = None
    blocked_obstacle: Obstacle | None = None
    load_demand_multiplier: float = 1.0
    observation_delay_s: float = 0.0
    speed_scale_after: float = 1.0
    force_scale_after: float = 1.0


@dataclass(frozen=True, slots=True)
class SP6RobustnessScenarioParams:
    """Parameters for one SP6 robustness world."""

    generator: str = "communication_radius_decay"
    n_robots: int = 8
    n_loads: int = 3
    world_size: tuple[float, float] = (24.0, 20.0)
    robot_radius_m: float = 0.30
    target_tolerance_m: float = 0.45
    safety_margin_m: float = 0.08
    dt_s: float = 0.14
    horizon_s: float = 52.0
    communication_radius: float = float("inf")
    position_noise_std: float = 0.12
    robot_payload_kg: float = 34.0
    robot_force_n: float = 96.0
    robot_force_cv: float = 0.08
    max_speed_mean: float = 0.76


@dataclass(frozen=True, slots=True)
class SP6Problem:
    """World, tasks and robustness event for SP6."""

    world: WorldState
    load_slots: tuple[tuple[ContactSlot, ...], ...]
    initial_load_poses: np.ndarray
    target_load_poses: np.ndarray
    scenario_generator: str
    scenario_variant_id: str
    event: SP6EventSpec
    robot_radius_m: float
    formation_tolerance_m: float
    pose_tolerance_m: float
    orientation_tolerance_rad: float
    target_tolerance_m: float
    safety_margin_m: float
    dt_s: float
    horizon_s: float
    communication_radius: float
    force_ref_n: float = 120.0
    torque_ref_nm: float = 120.0

    def active_obstacles_at(self, t_s: float) -> tuple[Obstacle, ...]:
        obstacles = list(self.world.map.obstacles)
        if self.event.blocked_obstacle is not None and t_s >= self.event.time_s:
            obstacles.append(self.event.blocked_obstacle)
        return tuple(obstacles)

    def communication_radius_at(self, t_s: float, *, observed: bool = True) -> float:
        if self.event.communication_radius_after_m is None:
            return float(self.communication_radius)
        event_time = self.event.time_s + (self.event.observation_delay_s if observed else 0.0)
        return float(self.event.communication_radius_after_m if t_s >= event_time else self.communication_radius)

    def load_demand_at(self, load_idx: int, t_s: float, *, observed: bool = True) -> float:
        load = self.world.loads[load_idx]
        demand = float(load.min_capacity_kg or load.mass_kg)
        if self.event.kind != "infeasible_load_detection":
            return demand
        event_time = self.event.time_s + (self.event.observation_delay_s if observed else 0.0)
        if t_s >= event_time and load_idx == 0:
            return demand * float(self.event.load_demand_multiplier)
        return demand


class SP6RobustnessScenario(BaseScenario):
    """Build deterministic SP6 operational degradation worlds."""

    scenario_id = "SP6_robustness"
    metadata = ScenarioMetadata(
        name="SP6 operational robustness",
        description="Coalition recovery under communication degradation, robot failures, battery loss, blockages and infeasible tasks.",
        hypothesis="Guarded recovery policies preserve more task completion under disruptions than unguarded greedy baselines at comparable safety.",
    )

    def __init__(self, params: SP6RobustnessScenarioParams | None = None) -> None:
        self.params = params or SP6RobustnessScenarioParams()

    def build(self, seed: int = 2026) -> SP6Problem:
        params = self.params
        if params.n_robots < 1 or params.n_loads < 1:
            raise ValueError("SP6 requires at least one robot and one load.")
        if params.dt_s <= 0.0 or params.horizon_s <= 0.0:
            raise ValueError("SP6 time constants must be positive.")

        rng = np.random.default_rng(seed)
        key = params.generator.lower()
        width, height = params.world_size
        map_size = float(max(width, height))
        load_specs = _loads_for(params, rng)
        starts = _robot_starts(params, load_specs, rng)
        load_slots = tuple(_slots_for_load(load, idx) for idx, load in enumerate(load_specs))
        initial_poses = _initial_load_poses(load_specs)
        target_poses = _target_load_poses(load_specs)
        base_obstacles = _base_obstacles(key, width, height)
        event = _event_for(key, params, width, height)
        robots = _robots_for(params, starts, rng)
        world = WorldState(robots=robots, loads=load_specs, map=WarehouseMap(size_m=map_size, obstacles=tuple(base_obstacles)))
        return SP6Problem(
            world=world,
            load_slots=load_slots,
            initial_load_poses=initial_poses,
            target_load_poses=target_poses,
            scenario_generator=key,
            scenario_variant_id=f"{key}_seed{seed}",
            event=event,
            robot_radius_m=float(params.robot_radius_m),
            formation_tolerance_m=1.25,
            pose_tolerance_m=0.38,
            orientation_tolerance_rad=float(np.deg2rad(7.0)),
            target_tolerance_m=float(params.target_tolerance_m),
            safety_margin_m=float(params.safety_margin_m),
            dt_s=float(params.dt_s),
            horizon_s=float(params.horizon_s),
            communication_radius=float(params.communication_radius),
        )


def scenario_params_for_generator(generator: str) -> tuple[SP6RobustnessScenarioParams, ...]:
    """Return deterministic parameter bundles for named SP6 generators."""

    key = generator.lower()
    if key in {"setup", "sp6_0", "sp6.0"}:
        return (SP6RobustnessScenarioParams(generator="communication_radius_decay", n_robots=6, n_loads=2, horizon_s=46.0),)
    if key == "communication_radius_decay":
        return (SP6RobustnessScenarioParams(generator=key, n_robots=8, n_loads=3, horizon_s=52.0, communication_radius=float("inf")),)
    if key == "robot_dropout_mid_task":
        return (SP6RobustnessScenarioParams(generator=key, n_robots=8, n_loads=3, horizon_s=54.0),)
    if key == "battery_depletion_reallocation":
        return (SP6RobustnessScenarioParams(generator=key, n_robots=8, n_loads=3, horizon_s=54.0),)
    if key == "blocked_corridor_recovery":
        return (SP6RobustnessScenarioParams(generator=key, n_robots=9, n_loads=3, horizon_s=60.0),)
    if key == "infeasible_load_detection":
        return (SP6RobustnessScenarioParams(generator=key, n_robots=6, n_loads=3, horizon_s=60.0, robot_payload_kg=30.0),)
    if key == "delayed_information_consensus":
        return (SP6RobustnessScenarioParams(generator=key, n_robots=8, n_loads=3, horizon_s=56.0, communication_radius=5.0),)
    if key == "multi_load_priority_shift":
        return (SP6RobustnessScenarioParams(generator=key, n_robots=10, n_loads=4, horizon_s=58.0),)
    if key in {"monte_carlo", "sp6_mc"}:
        return (SP6RobustnessScenarioParams(generator="monte_carlo", n_robots=8, n_loads=3, horizon_s=54.0),)
    raise ValueError(f"Unknown SP6 scenario generator: {generator}")


def sample_monte_carlo_params(seed: int, base: SP6RobustnessScenarioParams | None = None) -> SP6RobustnessScenarioParams:
    """Sample one SP6 Monte Carlo parameter bundle from a seed."""

    rng = np.random.default_rng(seed)
    params = base or SP6RobustnessScenarioParams(generator="monte_carlo")
    generator = str(
        rng.choice(
            [
                "communication_radius_decay",
                "robot_dropout_mid_task",
                "battery_depletion_reallocation",
                "blocked_corridor_recovery",
                "infeasible_load_detection",
                "delayed_information_consensus",
                "multi_load_priority_shift",
            ]
        )
    )
    base_params = scenario_params_for_generator(generator)[0]
    return replace(
        base_params,
        n_robots=int(rng.choice([6, 8, 9, 10])),
        n_loads=int(rng.choice([2, 3, 4])),
        robot_payload_kg=float(rng.uniform(28.0, 42.0)),
        robot_force_n=float(rng.uniform(82.0, 112.0)),
        robot_force_cv=float(rng.uniform(0.03, 0.12)),
        communication_radius=float(rng.choice([np.inf, 8.0, 5.0, 3.2])),
        horizon_s=float(base_params.horizon_s + rng.uniform(-3.0, 5.0)),
        position_noise_std=float(rng.uniform(0.02, 0.20)),
        max_speed_mean=float(rng.uniform(0.66, 0.84)),
    )


def iter_sp6_problems(generators: Iterable[str], seeds: Iterable[int]) -> Iterable[tuple[str, str, int, SP6RobustnessScenarioParams, SP6Problem]]:
    """Yield SP6 problems for named generators and seeds."""

    for generator in generators:
        key = generator.lower()
        base_params = scenario_params_for_generator(key)
        for seed in seeds:
            if key in {"monte_carlo", "sp6_mc"}:
                params = sample_monte_carlo_params(seed, base_params[0])
                problem = SP6RobustnessScenario(params).build(seed)
                yield key, f"{key}_{params.generator}_seed{seed}", seed, params, problem
            else:
                for idx, params in enumerate(base_params):
                    problem = SP6RobustnessScenario(params).build(seed + 997 * idx)
                    yield key, f"{key}_v{idx:02d}", seed, params, problem


def _robot_starts(params: SP6RobustnessScenarioParams, loads: list[LoadSpec], rng: np.random.Generator) -> np.ndarray:
    width, height = params.world_size
    starts = []
    for idx in range(params.n_robots):
        load = loads[idx % len(loads)]
        local_rank = idx // len(loads)
        angle = -0.9 + 0.55 * (local_rank % 4)
        radius = 2.15 + 0.22 * (local_rank % 3)
        offset = radius * np.array([np.cos(angle + 0.20 * (idx % 2)), np.sin(angle)], dtype=float)
        starts.append(np.asarray(load.pickup, dtype=float) + offset)
    starts = np.vstack(starts)
    starts += rng.normal(0.0, params.position_noise_std, size=starts.shape)
    half = np.array([0.5 * width, 0.5 * height], dtype=float)
    starts = np.clip(starts, -0.88 * half, 0.88 * half)
    return starts


def _loads_for(params: SP6RobustnessScenarioParams, rng: np.random.Generator) -> list[LoadSpec]:
    width, height = params.world_size
    ys = np.linspace(-0.28 * height, 0.28 * height, params.n_loads)
    loads: list[LoadSpec] = []
    for idx in range(params.n_loads):
        mass = float(44.0 + 8.0 * (idx % 3))
        min_size = 2 if idx % 2 == 0 else 3
        pickup = np.array([-0.06 * width, ys[idx]], dtype=float) + rng.normal(0.0, 0.05, size=2)
        destination = np.array([0.24 * width, -0.55 * ys[idx]], dtype=float)
        reward = float(5.0 - 0.45 * idx)
        loads.append(
            LoadSpec(
                identifier=f"load-{idx + 1:02d}",
                pickup=pickup,
                destination=destination,
                mass_kg=mass,
                length_m=2.2 + 0.3 * (idx % 2),
                width_m=1.0,
                min_capacity_kg=mass,
                min_coalition_size=min_size,
                reward=reward,
                wrench=WrenchDemand(force_xy=np.array([70.0 + 8.0 * idx, 22.0], dtype=float), torque_z=24.0 + 6.0 * idx),
            )
        )
    return loads


def _robots_for(params: SP6RobustnessScenarioParams, starts: np.ndarray, rng: np.random.Generator) -> list[RobotRuntimeState]:
    robots: list[RobotRuntimeState] = []
    payloads = rng.lognormal(mean=np.log(params.robot_payload_kg), sigma=max(params.robot_force_cv, 1e-9), size=params.n_robots)
    forces = rng.lognormal(mean=np.log(params.robot_force_n), sigma=max(params.robot_force_cv, 1e-9), size=params.n_robots)
    speeds = rng.lognormal(mean=np.log(params.max_speed_mean), sigma=0.06, size=params.n_robots)
    for idx in range(params.n_robots):
        robots.append(
            RobotRuntimeState(
                spec=RobotSpec(
                    identifier=f"amr-{idx + 1:02d}",
                    capacity=CapacityModel(payload_kg=float(payloads[idx]), force_limit_n=float(forces[idx]), torque_limit_nm=float(22.0 + 0.10 * forces[idx])),
                    battery=BatteryModel(capacity_wh=float(rng.uniform(440.0, 680.0)), reserve_fraction=0.15, discharge_per_meter=float(rng.uniform(0.010, 0.018))),
                    max_speed=float(np.clip(speeds[idx], 0.52, 0.98)),
                ),
                position=starts[idx],
                heading=float(rng.uniform(-np.pi, np.pi)),
                battery_fraction=float(rng.uniform(0.72, 1.0)),
            )
        )
    return robots


def _base_obstacles(key: str, width: float, height: float) -> list[Obstacle]:
    if key in {"blocked_corridor_recovery", "delayed_information_consensus"}:
        return [
            Obstacle(center=np.array([0.10 * width, 0.24 * height], dtype=float), radius=0.90, influence_radius=2.0),
            Obstacle(center=np.array([0.10 * width, -0.24 * height], dtype=float), radius=0.90, influence_radius=2.0),
        ]
    if key in {"battery_depletion_reallocation", "multi_load_priority_shift"}:
        return [Obstacle(center=np.array([0.08 * width, 0.0], dtype=float), radius=0.80, influence_radius=1.9)]
    return []


def _event_for(key: str, params: SP6RobustnessScenarioParams, width: float, height: float) -> SP6EventSpec:
    event_time = 0.34 * float(params.horizon_s)
    if key == "communication_radius_decay":
        return SP6EventSpec(kind=key, time_s=event_time, communication_radius_after_m=3.2)
    if key == "robot_dropout_mid_task":
        return SP6EventSpec(kind=key, time_s=event_time, robot_indices=(0, max(1, params.n_robots // 2)), speed_scale_after=0.0, force_scale_after=0.0)
    if key == "battery_depletion_reallocation":
        return SP6EventSpec(kind=key, time_s=event_time, robot_indices=(1, max(2, params.n_robots - 2)), battery_fraction_after=0.24, speed_scale_after=0.35, force_scale_after=0.45)
    if key == "blocked_corridor_recovery":
        return SP6EventSpec(
            kind=key,
            time_s=event_time,
            blocked_obstacle=Obstacle(center=np.array([0.10 * width, 0.0], dtype=float), radius=1.25, influence_radius=2.8),
        )
    if key == "infeasible_load_detection":
        return SP6EventSpec(kind=key, time_s=event_time, robot_indices=(0,), load_demand_multiplier=7.0)
    if key == "delayed_information_consensus":
        return SP6EventSpec(kind=key, time_s=event_time, robot_indices=(0,), communication_radius_after_m=3.4, observation_delay_s=4.0, speed_scale_after=0.45, force_scale_after=0.55)
    if key == "multi_load_priority_shift":
        return SP6EventSpec(kind=key, time_s=event_time, robot_indices=(0,), load_demand_multiplier=1.35)
    return SP6EventSpec(kind="communication_radius_decay", time_s=event_time, communication_radius_after_m=3.5)


def _slots_for_load(load: LoadSpec, load_idx: int) -> tuple[ContactSlot, ...]:
    half_l = 0.5 * float(load.length_m)
    half_w = 0.5 * float(load.width_m)
    if load_idx % 2 == 0:
        slots = [
            ([-0.82 * half_l, -0.55 * half_w], [1.0, 0.0], "rear_left_push"),
            ([-0.82 * half_l, 0.55 * half_w], [1.0, 0.0], "rear_right_push"),
            ([0.62 * half_l, -0.68 * half_w], [0.0, 1.0], "side_up_torque"),
            ([0.78 * half_l, 0.42 * half_w], [-1.0, 0.0], "front_brake_torque"),
        ]
    else:
        slots = [
            ([-0.78 * half_l, 0.0], [1.0, 0.0], "rear_push"),
            ([0.18 * half_l, -0.82 * half_w], [0.0, 1.0], "side_lift"),
            ([0.72 * half_l, 0.72 * half_w], [-1.0, 0.0], "front_stabilizer"),
        ]
    return tuple(ContactSlot(offset_xy=np.asarray(offset, dtype=float), direction_xy=np.asarray(direction, dtype=float), role=role) for offset, direction, role in slots)


def _initial_load_poses(loads: list[LoadSpec]) -> np.ndarray:
    poses = []
    for idx, load in enumerate(loads):
        theta = np.deg2rad(-18.0 + 9.0 * (idx % 3))
        poses.append([float(load.pickup[0]), float(load.pickup[1]), float(theta)])
    return np.asarray(poses, dtype=float)


def _target_load_poses(loads: list[LoadSpec]) -> np.ndarray:
    poses = []
    for idx, load in enumerate(loads):
        theta = np.deg2rad(26.0 - 8.0 * (idx % 3))
        poses.append([float(load.destination[0]), float(load.destination[1]), float(theta)])
    return np.asarray(poses, dtype=float)

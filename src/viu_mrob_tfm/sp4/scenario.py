"""Scenario generator for SP4 post-allocation AMR motion and arrival experiments."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

import numpy as np

from viu_mrob_tfm.domain import CapacityModel, LoadSpec, Obstacle, RobotRuntimeState, RobotSpec, WarehouseMap, WorldState
from viu_mrob_tfm.domain.robot import BatteryModel
from viu_mrob_tfm.scenarios.base import BaseScenario, ScenarioMetadata


@dataclass(frozen=True, slots=True)
class SP4MotionScenarioParams:
    """Parameters for one SP4 motion world.

    SP4 is intentionally a post-allocation motion benchmark. Each AMR receives a
    target position that represents a load/slot staging point already chosen by
    SP1-SP3. The benchmark evaluates whether the robots can arrive safely and
    cheaply from random initial positions under finite horizon, obstacles and
    local communication.
    """

    generator: str = "open_field_arrival"
    n_robots: int = 6
    world_size: tuple[float, float] = (18.0, 18.0)
    robot_radius_m: float = 0.28
    target_tolerance_m: float = 0.35
    safety_margin_m: float = 0.08
    dt_s: float = 0.12
    horizon_s: float = 22.0
    communication_radius: float = float("inf")
    position_noise_std: float = 0.08
    obstacle_noise_std: float = 0.04
    max_speed_mean: float = 0.72
    max_speed_cv: float = 0.06


@dataclass(frozen=True, slots=True)
class SP4Problem:
    """World plus SP4 motion targets and safety constants."""

    world: WorldState
    target_xy: np.ndarray
    target_labels: tuple[str, ...]
    scenario_generator: str
    scenario_variant_id: str
    robot_radius_m: float
    target_tolerance_m: float
    safety_margin_m: float
    dt_s: float
    horizon_s: float
    communication_radius: float

    def __post_init__(self) -> None:
        targets = np.asarray(self.target_xy, dtype=float)
        if targets.shape != (len(self.world.robots), 2):
            raise ValueError("SP4 target_xy must have shape (n_robots, 2).")
        if len(self.target_labels) != len(self.world.robots):
            raise ValueError("SP4 target_labels must match the robot count.")
        object.__setattr__(self, "target_xy", targets)


class SP4MotionScenario(BaseScenario):
    """Build deterministic SP4 navigation worlds from a seed."""

    scenario_id = "SP4_motion"
    metadata = ScenarioMetadata(
        name="SP4 motion and arrival",
        description="Post-allocation AMR motion from initial positions to assigned load/slot targets.",
        hypothesis="Safe motion-aware policies reduce collisions and arrival delay compared with direct motion.",
    )

    def __init__(self, params: SP4MotionScenarioParams | None = None) -> None:
        self.params = params or SP4MotionScenarioParams()

    def build(self, seed: int = 2026) -> SP4Problem:
        params = self.params
        if params.n_robots < 1:
            raise ValueError("SP4 requires at least one robot.")
        if params.robot_radius_m <= 0.0:
            raise ValueError("robot_radius_m must be positive.")
        if params.dt_s <= 0.0 or params.horizon_s <= 0.0:
            raise ValueError("SP4 dt_s and horizon_s must be positive.")

        rng = np.random.default_rng(seed)
        key = params.generator.lower()
        starts, targets, obstacles = _layout(key, params, rng)
        speed_sigma = max(float(params.max_speed_cv), 1e-9)
        speeds = rng.lognormal(mean=np.log(float(params.max_speed_mean)), sigma=speed_sigma, size=params.n_robots)
        speeds = np.clip(speeds, 0.55 * params.max_speed_mean, 1.35 * params.max_speed_mean)

        robots: list[RobotRuntimeState] = []
        for idx in range(params.n_robots):
            robots.append(
                RobotRuntimeState(
                    spec=RobotSpec(
                        identifier=f"amr-{idx + 1:02d}",
                        capacity=CapacityModel(payload_kg=25.0, force_limit_n=250.0, torque_limit_nm=30.0),
                        battery=BatteryModel(
                            capacity_wh=float(rng.uniform(420.0, 660.0)),
                            reserve_fraction=0.15,
                            discharge_per_meter=float(rng.uniform(0.010, 0.018)),
                        ),
                        max_speed=float(speeds[idx]),
                    ),
                    position=starts[idx],
                    heading=float(rng.uniform(-np.pi, np.pi)),
                    battery_fraction=float(rng.uniform(0.70, 1.0)),
                )
            )

        loads = [
            LoadSpec(
                identifier=f"target-{idx + 1:02d}",
                pickup=targets[idx],
                destination=targets[idx],
                mass_kg=20.0,
                min_capacity_kg=20.0,
                min_coalition_size=1,
                reward=1.0,
            )
            for idx in range(params.n_robots)
        ]
        world = WorldState(
            robots=robots,
            loads=loads,
            map=WarehouseMap(size_m=float(max(params.world_size)), obstacles=tuple(obstacles)),
        )
        return SP4Problem(
            world=world,
            target_xy=targets,
            target_labels=tuple(load.identifier for load in loads),
            scenario_generator=key,
            scenario_variant_id=f"{key}_seed{seed}",
            robot_radius_m=float(params.robot_radius_m),
            target_tolerance_m=float(params.target_tolerance_m),
            safety_margin_m=float(params.safety_margin_m),
            dt_s=float(params.dt_s),
            horizon_s=float(params.horizon_s),
            communication_radius=float(params.communication_radius),
        )


def scenario_params_for_generator(generator: str) -> tuple[SP4MotionScenarioParams, ...]:
    """Return deterministic parameter bundles for named SP4 generators."""

    key = generator.lower()
    if key in {"setup", "sp4_0", "sp4.0"}:
        return (SP4MotionScenarioParams(generator="open_field_arrival", n_robots=4, horizon_s=22.0),)
    if key == "open_field_arrival":
        return (SP4MotionScenarioParams(generator=key, n_robots=6, horizon_s=24.0),)
    if key == "crossing_traffic":
        return (SP4MotionScenarioParams(generator=key, n_robots=6, horizon_s=34.0),)
    if key == "narrow_passage":
        return (SP4MotionScenarioParams(generator=key, n_robots=6, horizon_s=36.0),)
    if key == "cluttered_warehouse":
        return (SP4MotionScenarioParams(generator=key, n_robots=8, horizon_s=40.0),)
    if key == "communication_limited":
        return (SP4MotionScenarioParams(generator=key, n_robots=8, communication_radius=3.2, horizon_s=36.0),)
    if key == "long_distance_energy":
        return (SP4MotionScenarioParams(generator=key, n_robots=6, world_size=(24.0, 24.0), horizon_s=44.0),)
    if key in {"monte_carlo", "sp4_mc"}:
        return (SP4MotionScenarioParams(generator="monte_carlo", n_robots=8, horizon_s=28.0),)
    raise ValueError(f"Unknown SP4 scenario generator: {generator}")


def sample_monte_carlo_params(seed: int, base: SP4MotionScenarioParams | None = None) -> SP4MotionScenarioParams:
    """Sample one SP4 Monte Carlo parameter bundle from a seed."""

    rng = np.random.default_rng(seed)
    params = base or SP4MotionScenarioParams(generator="monte_carlo")
    generator = str(
        rng.choice(
            [
                "open_field_arrival",
                "crossing_traffic",
                "narrow_passage",
                "cluttered_warehouse",
                "communication_limited",
                "long_distance_energy",
            ]
        )
    )
    n_robots = int(rng.choice([5, 6, 8, 10]))
    world_size = (float(rng.uniform(16.0, 24.0)), float(rng.uniform(16.0, 24.0)))
    comm = float(rng.choice([np.inf, 8.0, 5.0, 3.2]))
    if generator == "communication_limited":
        comm = float(rng.choice([4.0, 3.2, 2.6]))
    return replace(
        params,
        generator=generator,
        n_robots=n_robots,
        world_size=world_size,
        communication_radius=comm,
        horizon_s=float(rng.uniform(30.0, 44.0)),
        position_noise_std=float(rng.uniform(0.02, 0.18)),
        obstacle_noise_std=float(rng.uniform(0.0, 0.08)),
        max_speed_mean=float(rng.uniform(0.62, 0.82)),
        max_speed_cv=float(rng.uniform(0.02, 0.10)),
    )


def iter_sp4_problems(generators: Iterable[str], seeds: Iterable[int]) -> Iterable[tuple[str, str, int, SP4MotionScenarioParams, SP4Problem]]:
    """Yield SP4 problems for named generators and seeds."""

    for generator in generators:
        key = generator.lower()
        base_params = scenario_params_for_generator(key)
        for seed in seeds:
            if key in {"monte_carlo", "sp4_mc"}:
                params = sample_monte_carlo_params(seed, base_params[0])
                problem = SP4MotionScenario(params).build(seed)
                yield key, f"{key}_{params.generator}_seed{seed}", seed, params, problem
            else:
                for idx, params in enumerate(base_params):
                    problem = SP4MotionScenario(params).build(seed + 997 * idx)
                    yield key, f"{key}_v{idx:02d}", seed, params, problem


def _layout(
    key: str,
    params: SP4MotionScenarioParams,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, list[Obstacle]]:
    width, height = params.world_size
    n = params.n_robots
    if key == "open_field_arrival":
        ys = np.linspace(-0.32 * height, 0.32 * height, n)
        starts = np.column_stack([np.full(n, -0.36 * width), ys])
        targets = np.column_stack([np.full(n, 0.36 * width), ys])
        obstacles: list[Obstacle] = []
    elif key in {"crossing_traffic", "communication_limited"}:
        ys = np.linspace(-0.34 * height, 0.34 * height, n)
        starts = np.column_stack([np.where(np.arange(n) % 2 == 0, -0.38 * width, 0.38 * width), ys])
        targets = np.column_stack([-starts[:, 0], -0.82 * ys])
        obstacles = []
    elif key == "narrow_passage":
        ys = np.linspace(-0.34 * height, 0.34 * height, n)
        starts = np.column_stack([np.full(n, -0.40 * width), ys])
        targets = np.column_stack([np.full(n, 0.40 * width), -0.85 * ys])
        obstacles = [
            Obstacle(center=np.array([0.0, 1.55], dtype=float), radius=1.35, influence_radius=2.25),
            Obstacle(center=np.array([0.0, -1.55], dtype=float), radius=1.35, influence_radius=2.25),
        ]
    elif key == "cluttered_warehouse":
        ys = np.linspace(-0.36 * height, 0.36 * height, n)
        starts = np.column_stack([np.full(n, -0.39 * width), ys])
        targets = np.column_stack([np.full(n, 0.39 * width), np.roll(ys, n // 2)])
        obstacles = [
            Obstacle(center=np.array([-0.14 * width, -0.16 * height], dtype=float), radius=0.72, influence_radius=1.65),
            Obstacle(center=np.array([-0.08 * width, 0.18 * height], dtype=float), radius=0.62, influence_radius=1.45),
            Obstacle(center=np.array([0.10 * width, -0.08 * height], dtype=float), radius=0.70, influence_radius=1.55),
            Obstacle(center=np.array([0.18 * width, 0.20 * height], dtype=float), radius=0.66, influence_radius=1.55),
        ]
    elif key == "long_distance_energy":
        angles = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
        starts = 0.42 * min(width, height) * np.column_stack([np.cos(angles), np.sin(angles)])
        targets = -0.42 * min(width, height) * np.column_stack([np.cos(angles + 0.35), np.sin(angles + 0.35)])
        obstacles = [
            Obstacle(center=np.array([0.0, 0.0], dtype=float), radius=1.10, influence_radius=2.20),
        ]
    else:
        raise ValueError(f"Unknown SP4 layout: {key}")

    starts = np.asarray(starts, dtype=float)
    targets = np.asarray(targets, dtype=float)
    if params.position_noise_std > 0.0:
        starts = starts + rng.normal(0.0, params.position_noise_std, size=starts.shape)
        targets = targets + rng.normal(0.0, 0.5 * params.position_noise_std, size=targets.shape)
    if params.obstacle_noise_std > 0.0 and obstacles:
        obstacles = [
            Obstacle(
                center=obs.center + rng.normal(0.0, params.obstacle_noise_std, size=2),
                radius=obs.radius,
                influence_radius=obs.influence_radius,
            )
            for obs in obstacles
        ]
    half = np.array([0.5 * width, 0.5 * height], dtype=float)
    starts = np.clip(starts, -0.88 * half, 0.88 * half)
    targets = np.clip(targets, -0.88 * half, 0.88 * half)
    return starts, targets, obstacles

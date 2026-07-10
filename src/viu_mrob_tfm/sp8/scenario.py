"""Warehouse-scale SP8 scenario generator.

SP8 intentionally uses a mesoscopic/vectorized model. It is designed to answer
scale questions that exact coalition search and time-expanded MPC cannot answer
within thesis runtimes: hundreds to thousands of AMRs, many simultaneous payload
tasks, wrench/torque feasibility, moving payload routes and static/mobile
obstacle fields.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

import numpy as np


FLEET_LADDER_ROBOT_COUNTS: tuple[int, ...] = (
    5,
    10,
    25,
    50,
    100,
    250,
    500,
    1000,
    1250,
    1500,
    2000,
    2500,
    5000,
    7500,
    10000,
    12500,
    15000,
    20000,
    25000,
    50000,
)


@dataclass(frozen=True, slots=True)
class SP8ScaleParams:
    scenario_id: str = "debug_small"
    n_robots: int = 64
    n_loads: int = 16
    world_size_m: float = 120.0
    obstacle_count: int = 12
    mobile_obstacle_count: int = 4
    communication_radius_m: float = 18.0
    load_mass_range_kg: tuple[float, float] = (30.0, 140.0)
    load_length_range_m: tuple[float, float] = (1.0, 4.0)
    robot_force_range_n: tuple[float, float] = (80.0, 220.0)
    robot_payload_range_kg: tuple[float, float] = (25.0, 80.0)
    obstacle_radius_range_m: tuple[float, float] = (1.1, 4.0)
    mobile_radius_range_m: tuple[float, float] = (1.2, 3.5)
    horizon_s: float = 180.0
    target_speed_mps: float = 0.72
    warehouse_archetype: str = "generic"


@dataclass(frozen=True, slots=True)
class SP8Problem:
    params: SP8ScaleParams
    robot_xy: np.ndarray
    robot_force_n: np.ndarray
    robot_payload_kg: np.ndarray
    robot_speed_mps: np.ndarray
    load_pickup_xy: np.ndarray
    load_target_xy: np.ndarray
    load_mass_kg: np.ndarray
    load_length_m: np.ndarray
    load_width_m: np.ndarray
    wrench_demands: np.ndarray
    required_robots: np.ndarray
    load_reward: np.ndarray
    obstacle_xy: np.ndarray
    obstacle_radius_m: np.ndarray
    mobile_start_xy: np.ndarray
    mobile_end_xy: np.ndarray
    mobile_radius_m: np.ndarray


def scenario_params_for_generator(generator: str) -> tuple[SP8ScaleParams, ...]:
    key = generator.lower()
    if key in {"debug", "setup", "sp8_0", "sp8.0"}:
        return (
            SP8ScaleParams(
                scenario_id="debug_64r_16l",
                n_robots=64,
                n_loads=16,
                world_size_m=95.0,
                obstacle_count=8,
                mobile_obstacle_count=3,
                warehouse_archetype="debug",
            ),
        )
    if key == "scale_ladder":
        return (
            SP8ScaleParams("scale_64r_16l", 64, 16, 110.0, 10, 3, 18.0, warehouse_archetype="small_exact"),
            SP8ScaleParams("scale_128r_32l", 128, 32, 150.0, 16, 5, 20.0, warehouse_archetype="medium_stress"),
            SP8ScaleParams("scale_256r_64l", 256, 64, 210.0, 26, 8, 22.0, warehouse_archetype="large_zone"),
            SP8ScaleParams("scale_512r_128l", 512, 128, 300.0, 42, 12, 24.0, warehouse_archetype="warehouse_scale"),
        )
    if key in {"fleet_ladder_extended", "fleet_ladder", "scale_ladder_extended"}:
        return tuple(_fleet_ladder_params())
    if key == "warehouse_large":
        return (
            SP8ScaleParams("amazon_like_1000r_250l", 1000, 250, 480.0, 80, 25, 28.0, warehouse_archetype="amazon_like_sortable_zone"),
            SP8ScaleParams("cainiao_like_1200r_320l", 1200, 320, 520.0, 90, 30, 30.0, warehouse_archetype="cainiao_like_robot_warehouse"),
        )
    if key == "mega_peak":
        return (
            SP8ScaleParams("mega_2000r_600l", 2000, 600, 760.0, 150, 45, 34.0, warehouse_archetype="mega_wave_peak"),
            SP8ScaleParams("mega_3000r_900l", 3000, 900, 950.0, 210, 60, 36.0, warehouse_archetype="mega_wave_peak"),
        )
    if key == "obstacle_monte_carlo":
        return (SP8ScaleParams(scenario_id="obstacle_monte_carlo", n_robots=256, n_loads=64, warehouse_archetype="random_obstacle_mc"),)
    raise ValueError(f"Unknown SP8 scenario generator: {generator}")


def _fleet_ladder_params() -> list[SP8ScaleParams]:
    params: list[SP8ScaleParams] = []
    for n_robots in FLEET_LADDER_ROBOT_COUNTS:
        n_loads = max(1, int(round(0.25 * n_robots)))
        world = float(max(28.0, 13.5 * np.sqrt(float(n_robots))))
        obstacle_count = int(np.clip(round(1.85 * np.sqrt(float(n_robots))), 2, 850))
        mobile_count = int(np.clip(round(0.42 * np.sqrt(float(n_robots))), 1, 260))
        comm_radius = float(np.clip(10.0 + 2.2 * np.log2(max(n_robots, 2)), 14.0, 48.0))
        params.append(
            SP8ScaleParams(
                scenario_id=f"fleet_{n_robots}r_{n_loads}l",
                n_robots=n_robots,
                n_loads=n_loads,
                world_size_m=world,
                obstacle_count=obstacle_count,
                mobile_obstacle_count=mobile_count,
                communication_radius_m=comm_radius,
                horizon_s=float(np.clip(110.0 + 5.5 * np.sqrt(float(n_robots)), 130.0, 900.0)),
                warehouse_archetype="fleet_ladder_extended",
            )
        )
    return params


def iter_sp8_problems(generators: Iterable[str], seeds: Iterable[int]) -> Iterable[tuple[str, str, int, SP8ScaleParams, SP8Problem]]:
    for generator in generators:
        key = str(generator).lower()
        for seed in seeds:
            if key == "obstacle_monte_carlo":
                params = sample_monte_carlo_params(seed)
                yield key, f"{params.scenario_id}_seed{seed}", seed, params, build_sp8_problem(params, seed)
                continue
            for idx, params in enumerate(scenario_params_for_generator(key)):
                build_seed = seed + 1009 * idx
                yield key, f"{params.scenario_id}_seed{seed}", seed, params, build_sp8_problem(params, build_seed)


def sample_monte_carlo_params(seed: int) -> SP8ScaleParams:
    rng = np.random.default_rng(seed)
    n_robots = int(rng.choice([128, 256, 384, 512]))
    ratio = float(rng.choice([0.18, 0.25, 0.35, 0.50]))
    n_loads = max(8, int(round(n_robots * ratio)))
    world = float(np.sqrt(n_robots) * rng.uniform(13.0, 17.5))
    return SP8ScaleParams(
        scenario_id=f"mc_{n_robots}r_{n_loads}l_obs{int(rng.integers(12, 60))}",
        n_robots=n_robots,
        n_loads=n_loads,
        world_size_m=world,
        obstacle_count=int(rng.integers(12, 60)),
        mobile_obstacle_count=int(rng.integers(4, 18)),
        communication_radius_m=float(rng.choice([14.0, 18.0, 24.0, 32.0])),
        obstacle_radius_range_m=(float(rng.uniform(0.8, 1.6)), float(rng.uniform(2.8, 6.5))),
        mobile_radius_range_m=(float(rng.uniform(1.0, 1.8)), float(rng.uniform(2.4, 5.5))),
        horizon_s=float(rng.uniform(140.0, 260.0)),
        warehouse_archetype="random_obstacle_mc",
    )


def build_sp8_problem(params: SP8ScaleParams, seed: int) -> SP8Problem:
    rng = np.random.default_rng(seed)
    half = 0.5 * params.world_size_m
    robot_xy = rng.uniform(-0.92 * half, 0.92 * half, size=(params.n_robots, 2))
    load_pickup_xy = rng.uniform(-0.78 * half, 0.78 * half, size=(params.n_loads, 2))
    target_offsets = rng.normal(0.0, 0.36 * half, size=(params.n_loads, 2))
    load_target_xy = np.clip(load_pickup_xy + target_offsets, -0.86 * half, 0.86 * half)
    load_mass = rng.uniform(*params.load_mass_range_kg, size=params.n_loads)
    length = rng.uniform(*params.load_length_range_m, size=params.n_loads)
    width = rng.uniform(0.65, 1.55, size=params.n_loads)
    robot_force = rng.uniform(*params.robot_force_range_n, size=params.n_robots)
    robot_payload = rng.uniform(*params.robot_payload_range_kg, size=params.n_robots)
    robot_speed = rng.uniform(0.55, 1.05, size=params.n_robots)

    direction = load_target_xy - load_pickup_xy
    norms = np.linalg.norm(direction, axis=1)
    unit = direction / np.maximum(norms[:, None], 1e-9)
    force_mag = 0.45 * load_mass + rng.uniform(25.0, 85.0, size=params.n_loads)
    torque = rng.normal(0.0, 0.42 * load_mass * length)
    high_torque = rng.random(params.n_loads) < 0.32
    torque[high_torque] += rng.choice([-1.0, 1.0], size=int(np.sum(high_torque))) * rng.uniform(40.0, 160.0, size=int(np.sum(high_torque)))
    wrench_demands = np.column_stack([force_mag * unit[:, 0], force_mag * unit[:, 1], torque])
    required = np.clip(np.ceil(load_mass / np.percentile(robot_payload, 62)).astype(int), 1, 6)
    reward = 1.0 + 0.012 * load_mass + 0.002 * np.abs(torque) + rng.uniform(0.0, 1.0, size=params.n_loads)

    obstacle_xy = rng.uniform(-0.86 * half, 0.86 * half, size=(params.obstacle_count, 2))
    obstacle_radius = rng.uniform(*params.obstacle_radius_range_m, size=params.obstacle_count)
    mobile_start = rng.uniform(-0.86 * half, 0.86 * half, size=(params.mobile_obstacle_count, 2))
    mobile_end = rng.uniform(-0.86 * half, 0.86 * half, size=(params.mobile_obstacle_count, 2))
    mobile_radius = rng.uniform(*params.mobile_radius_range_m, size=params.mobile_obstacle_count)
    return SP8Problem(
        params=params,
        robot_xy=robot_xy,
        robot_force_n=robot_force,
        robot_payload_kg=robot_payload,
        robot_speed_mps=robot_speed,
        load_pickup_xy=load_pickup_xy,
        load_target_xy=load_target_xy,
        load_mass_kg=load_mass,
        load_length_m=length,
        load_width_m=width,
        wrench_demands=wrench_demands,
        required_robots=required,
        load_reward=reward,
        obstacle_xy=obstacle_xy,
        obstacle_radius_m=obstacle_radius,
        mobile_start_xy=mobile_start,
        mobile_end_xy=mobile_end,
        mobile_radius_m=mobile_radius,
    )


def scaled_params(params: SP8ScaleParams, *, n_robots: int | None = None, n_loads: int | None = None) -> SP8ScaleParams:
    return replace(
        params,
        n_robots=params.n_robots if n_robots is None else int(n_robots),
        n_loads=params.n_loads if n_loads is None else int(n_loads),
    )

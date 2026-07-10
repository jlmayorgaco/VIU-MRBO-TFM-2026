"""Scenario generator for SP2 effective-capacity coalition experiments."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

import numpy as np

from viu_mrob_tfm.domain import CapacityModel, LoadSpec, RobotRuntimeState, RobotSpec, WarehouseMap, WorldState
from viu_mrob_tfm.domain.robot import BatteryModel
from viu_mrob_tfm.scenarios.base import BaseScenario, ScenarioMetadata


@dataclass(frozen=True, slots=True)
class SP2CapacityScenarioParams:
    """Parameters for one SP2 capacity-aware world."""

    n_robots: int = 8
    n_loads: int = 3
    capacity_ratio: float = 0.85
    robot_payload_mean_kg: float = 45.0
    robot_payload_cv: float = 0.35
    load_mass_cv: float = 0.45
    battery_variation: bool = True
    communication_radius: float = float("inf")
    position_noise_std: float = 0.2
    world_size: tuple[float, float] = (24.0, 24.0)
    reward_mode: str = "capacity_priority"
    min_battery_fraction: float = 0.38
    distance_decay_m: float = 22.0


class SP2CapacityScenario(BaseScenario):
    """Build a deterministic SP2 world from a seed and parameter bundle."""

    scenario_id = "SP2_capacity"
    metadata = ScenarioMetadata(
        name="SP2 effective capacity",
        description="Capacity-aware coalition recruitment for heterogeneous AMRs and loads.",
        hypothesis="Effective-capacity methods differ when load demand cannot be reduced to robot count.",
    )

    def __init__(self, params: SP2CapacityScenarioParams | None = None) -> None:
        self.params = params or SP2CapacityScenarioParams()

    def build(self, seed: int = 2026) -> WorldState:
        params = self.params
        if params.n_robots < 1:
            raise ValueError("SP2 requires at least one robot.")
        if params.n_loads < 1:
            raise ValueError("SP2 requires at least one load.")
        if params.robot_payload_mean_kg <= 0.0:
            raise ValueError("robot_payload_mean_kg must be positive.")
        if params.capacity_ratio <= 0.0:
            raise ValueError("capacity_ratio must be positive.")

        rng = np.random.default_rng(seed)
        width, height = params.world_size
        map_size = float(max(width, height))
        half = np.array([0.5 * width, 0.5 * height], dtype=float)

        payloads = _robot_payloads(params, rng)
        robots = []
        for idx, payload in enumerate(payloads):
            battery = float(rng.uniform(params.min_battery_fraction, 1.0)) if params.battery_variation else 1.0
            speed = float(rng.uniform(0.52, 0.78))
            robots.append(
                RobotRuntimeState(
                    spec=RobotSpec(
                        identifier=f"amr-{idx + 1:02d}",
                        capacity=CapacityModel(
                            payload_kg=float(payload),
                            force_limit_n=9.81 * float(payload),
                            torque_limit_nm=1.8 * float(payload),
                        ),
                        battery=BatteryModel(
                            capacity_wh=float(rng.uniform(420.0, 680.0)),
                            reserve_fraction=0.16,
                            discharge_per_meter=float(rng.uniform(0.008, 0.014)),
                        ),
                        max_speed=speed,
                    ),
                    position=rng.uniform(-0.82 * half, 0.82 * half),
                    heading=float(rng.uniform(-np.pi, np.pi)),
                    battery_fraction=battery,
                )
            )

        target_total_capacity = params.capacity_ratio * float(np.sum(payloads))
        masses = _load_masses(params, rng, target_total_capacity)
        loads = []
        for idx, mass in enumerate(masses):
            pickup = rng.uniform(-0.72 * half, 0.72 * half)
            if params.position_noise_std > 0.0:
                pickup = pickup + rng.normal(0.0, params.position_noise_std, size=2)
                pickup = np.clip(pickup, -0.9 * half, 0.9 * half)
            destination = rng.uniform(-0.72 * half, 0.72 * half)
            length = float(rng.uniform(0.8, 2.6) * (1.0 + 0.008 * mass))
            width_m = float(rng.uniform(0.55, 1.35))
            min_coalition = max(1, int(np.ceil(float(mass) / max(float(np.percentile(payloads, 75)), 1.0))))
            reward = _load_reward(params.reward_mode, float(mass), length, idx, rng)
            loads.append(
                LoadSpec(
                    identifier=f"load-{idx + 1:02d}",
                    pickup=pickup,
                    destination=destination,
                    mass_kg=float(mass),
                    length_m=length,
                    width_m=width_m,
                    min_capacity_kg=float(mass),
                    min_coalition_size=min_coalition,
                    reward=reward,
                )
            )
        return WorldState(robots=robots, loads=loads, map=WarehouseMap(size_m=map_size))


def scenario_params_for_generator(generator: str) -> tuple[SP2CapacityScenarioParams, ...]:
    """Return deterministic parameter grids for named SP2 generators."""

    key = generator.lower()
    if key in {"setup", "sp2_0", "sp2.0"}:
        return (
            SP2CapacityScenarioParams(
                n_robots=5,
                n_loads=2,
                capacity_ratio=0.75,
                robot_payload_cv=0.2,
                battery_variation=False,
                position_noise_std=0.0,
                world_size=(14.0, 14.0),
            ),
        )
    if key in {"light_mixed", "sp2_1", "sp2.1"}:
        return tuple(
            SP2CapacityScenarioParams(n_robots=n, n_loads=loads, capacity_ratio=ratio, robot_payload_cv=0.28)
            for n in (6, 8)
            for loads in (3, 4)
            for ratio in (0.45, 0.65)
        )
    if key in {"balanced_capacity", "sp2_2", "sp2.2"}:
        return tuple(
            SP2CapacityScenarioParams(n_robots=n, n_loads=loads, capacity_ratio=ratio, robot_payload_cv=cv)
            for n in (8, 10)
            for loads in (3, 4)
            for ratio in (0.85, 1.0)
            for cv in (0.25, 0.45)
        )
    if key in {"heavy_capacity", "sp2_3", "sp2.3"}:
        return tuple(
            SP2CapacityScenarioParams(n_robots=n, n_loads=loads, capacity_ratio=ratio, robot_payload_cv=0.5, load_mass_cv=0.58)
            for n in (8, 10)
            for loads in (4, 5)
            for ratio in (1.15, 1.35)
        )
    if key in {"battery_constrained", "sp2_4", "sp2.4"}:
        return tuple(
            SP2CapacityScenarioParams(
                n_robots=8,
                n_loads=4,
                capacity_ratio=ratio,
                battery_variation=True,
                min_battery_fraction=0.22,
                communication_radius=radius,
            )
            for ratio in (0.85, 1.15)
            for radius in (float("inf"), 8.0, 5.0)
        )
    if key in {"monte_carlo", "sp2_5", "sp2.5"}:
        return (SP2CapacityScenarioParams(),)
    raise ValueError(f"Unknown SP2 scenario generator: {generator}")


def sample_monte_carlo_params(seed: int, base: SP2CapacityScenarioParams | None = None) -> SP2CapacityScenarioParams:
    """Sample one SP2 Monte Carlo parameter bundle from a seed."""

    rng = np.random.default_rng(seed)
    params = base or SP2CapacityScenarioParams()
    return replace(
        params,
        n_robots=int(rng.choice([6, 8, 10, 12])),
        n_loads=int(rng.choice([2, 3, 4, 5])),
        capacity_ratio=float(rng.uniform(0.45, 1.45)),
        robot_payload_mean_kg=float(rng.uniform(32.0, 62.0)),
        robot_payload_cv=float(rng.uniform(0.15, 0.58)),
        load_mass_cv=float(rng.uniform(0.22, 0.65)),
        battery_variation=bool(rng.choice([True, True, False])),
        min_battery_fraction=float(rng.uniform(0.2, 0.55)),
        communication_radius=float(rng.choice([np.inf, 10.0, 7.0, 5.0, 3.5])),
        position_noise_std=float(rng.uniform(0.0, 0.45)),
        reward_mode=str(rng.choice(["capacity_priority", "deadline_proxy", "random"])),
        distance_decay_m=float(rng.uniform(16.0, 30.0)),
    )


def iter_sp2_worlds(generators: Iterable[str], seeds: Iterable[int]) -> Iterable[tuple[str, str, int, SP2CapacityScenarioParams, WorldState]]:
    """Yield scenario variant metadata and built worlds for named SP2 generators."""

    for generator in generators:
        key = generator.lower()
        base_params = scenario_params_for_generator(key)
        for seed in seeds:
            if key in {"monte_carlo", "sp2_5", "sp2.5"}:
                params = sample_monte_carlo_params(seed, base_params[0])
                yield key, f"{key}_seed{seed}", seed, params, SP2CapacityScenario(params).build(seed)
            else:
                for idx, params in enumerate(base_params):
                    yield key, f"{key}_v{idx:02d}", seed, params, SP2CapacityScenario(params).build(seed + 997 * idx)


def _robot_payloads(params: SP2CapacityScenarioParams, rng: np.random.Generator) -> np.ndarray:
    sigma = max(params.robot_payload_cv, 1.0e-6)
    payloads = rng.lognormal(mean=np.log(params.robot_payload_mean_kg), sigma=sigma, size=params.n_robots)
    low = 0.35 * params.robot_payload_mean_kg
    high = 2.15 * params.robot_payload_mean_kg
    return np.clip(payloads, low, high).astype(float)


def _load_masses(params: SP2CapacityScenarioParams, rng: np.random.Generator, target_total_capacity: float) -> np.ndarray:
    weights = rng.lognormal(mean=0.0, sigma=max(params.load_mass_cv, 1.0e-6), size=params.n_loads)
    weights = weights / max(float(np.sum(weights)), 1.0e-9)
    masses = target_total_capacity * weights
    floor = 0.18 * params.robot_payload_mean_kg
    return np.maximum(masses, floor).astype(float)


def _load_reward(mode: str, mass: float, length_m: float, idx: int, rng: np.random.Generator) -> float:
    if mode == "deadline_proxy":
        return float(1.2 + 0.015 * mass + 0.25 * length_m + 0.08 * idx)
    if mode == "random":
        return float(rng.uniform(0.8, 4.2) + 0.008 * mass + 0.12 * length_m)
    return float(1.0 + 0.02 * mass + 0.18 * length_m + 0.04 * idx)

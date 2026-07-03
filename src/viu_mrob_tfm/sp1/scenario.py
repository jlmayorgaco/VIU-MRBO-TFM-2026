"""Scenario generator for SP1 recruitment and coalition assignment."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

import numpy as np

from viu_mrob_tfm.domain import CapacityModel, LoadSpec, RobotRuntimeState, RobotSpec, WarehouseMap, WorldState
from viu_mrob_tfm.scenarios.base import BaseScenario, ScenarioMetadata


@dataclass(frozen=True, slots=True)
class SP1RecruitmentScenarioParams:
    """Parameters for one SP1 recruitment world.

    SP1 is intentionally allocation-only: no transport dynamics, traffic,
    obstacles, failures, or closed-loop motion are introduced here.
    """

    n_robots: int = 6
    n_loads: int = 2
    demand_ratio: float = 0.75
    min_cardinality_choices: tuple[int, ...] = (1, 2, 3)
    heterogeneous_robots: bool = False
    reward_mode: str = "uniform"
    communication_radius: float = float("inf")
    position_noise_std: float = 0.25
    world_size: tuple[float, float] = (20.0, 20.0)
    robot_payload_kg: float = 25.0


class SP1RecruitmentScenario(BaseScenario):
    """Build a deterministic SP1 world from a seed and parameter bundle."""

    scenario_id = "SP1_recruitment"
    metadata = ScenarioMetadata(
        name="SP1 recruitment",
        description="Allocation-only coalition recruitment for heterogeneous loads.",
        hypothesis="Recruitment methods differ under under, balanced, and over demand.",
    )

    def __init__(self, params: SP1RecruitmentScenarioParams | None = None) -> None:
        self.params = params or SP1RecruitmentScenarioParams()

    def build(self, seed: int = 2026) -> WorldState:
        params = self.params
        if params.n_robots < 1:
            raise ValueError("SP1 requires at least one robot.")
        if params.n_loads < 1:
            raise ValueError("SP1 requires at least one load.")
        if params.robot_payload_kg <= 0.0:
            raise ValueError("robot_payload_kg must be positive.")
        if not params.min_cardinality_choices:
            raise ValueError("min_cardinality_choices cannot be empty.")

        rng = np.random.default_rng(seed)
        width, height = params.world_size
        map_size = float(max(width, height))
        half = np.array([0.5 * width, 0.5 * height], dtype=float)

        payloads = _robot_payloads(params, rng)
        robots = [
            RobotRuntimeState(
                spec=RobotSpec(
                    identifier=f"amr-{idx + 1:02d}",
                    capacity=CapacityModel(
                        payload_kg=float(payload),
                        force_limit_n=10.0 * float(payload),
                        torque_limit_nm=2.0 * float(payload),
                    ),
                ),
                position=rng.uniform(-0.82 * half, 0.82 * half),
                heading=float(rng.uniform(-np.pi, np.pi)),
                battery_fraction=1.0,
            )
            for idx, payload in enumerate(payloads)
        ]

        demands = _load_demands(params, rng)
        loads = []
        for idx, demand in enumerate(demands):
            pickup = rng.uniform(-0.72 * half, 0.72 * half)
            if params.position_noise_std > 0.0:
                pickup = pickup + rng.normal(0.0, params.position_noise_std, size=2)
                pickup = np.clip(pickup, -0.9 * half, 0.9 * half)
            destination = rng.uniform(-0.72 * half, 0.72 * half)
            nominal_payload = params.robot_payload_kg
            margin = rng.uniform(0.05, 0.22) * nominal_payload
            mass_kg = max(1.0, float(demand) * nominal_payload - margin)
            reward = _load_reward(params.reward_mode, int(demand), idx, rng)
            loads.append(
                LoadSpec(
                    identifier=f"load-{idx + 1:02d}",
                    pickup=pickup,
                    destination=destination,
                    mass_kg=mass_kg,
                    min_capacity_kg=mass_kg,
                    min_coalition_size=int(demand),
                    reward=reward,
                )
            )

        return WorldState(robots=robots, loads=loads, map=WarehouseMap(size_m=map_size))


def scenario_params_for_generator(generator: str) -> tuple[SP1RecruitmentScenarioParams, ...]:
    """Return deterministic parameter grids for named SP1 generators."""

    key = generator.lower()
    if key in {"setup", "sp1_0", "sp1.0"}:
        return (
            SP1RecruitmentScenarioParams(
                n_robots=4,
                n_loads=1,
                demand_ratio=0.5,
                min_cardinality_choices=(2,),
                position_noise_std=0.0,
                world_size=(12.0, 12.0),
            ),
        )
    if key in {"under_demand", "sp1_1", "sp1.1"}:
        return tuple(
            SP1RecruitmentScenarioParams(n_robots=n, n_loads=3, demand_ratio=ratio, heterogeneous_robots=hetero)
            for n in (6, 8)
            for ratio in (0.5, 0.75)
            for hetero in (False, True)
        )
    if key in {"balanced_demand", "sp1_2", "sp1.2"}:
        return tuple(
            SP1RecruitmentScenarioParams(n_robots=n, n_loads=3, demand_ratio=1.0, heterogeneous_robots=hetero)
            for n in (6, 8)
            for hetero in (False, True)
        )
    if key in {"over_demand", "sp1_3", "sp1.3"}:
        return tuple(
            SP1RecruitmentScenarioParams(n_robots=n, n_loads=4, demand_ratio=ratio, heterogeneous_robots=hetero)
            for n in (6, 8)
            for ratio in (1.25, 1.5)
            for hetero in (False, True)
        )
    if key in {"monte_carlo", "sp1_4", "sp1.4"}:
        return (SP1RecruitmentScenarioParams(),)
    raise ValueError(f"Unknown SP1 scenario generator: {generator}")


def sample_monte_carlo_params(seed: int, base: SP1RecruitmentScenarioParams | None = None) -> SP1RecruitmentScenarioParams:
    """Sample one SP1.4 Monte Carlo parameter bundle from a seed."""

    rng = np.random.default_rng(seed)
    params = base or SP1RecruitmentScenarioParams()
    n_robots = int(rng.choice([6, 8, 10, 12]))
    demand_ratio = float(rng.uniform(0.5, 1.7))
    communication_radius = float(rng.choice([np.inf, 10.0, 6.0, 4.0]))
    n_loads = int(rng.choice([2, 3, 4, 5]))
    return replace(
        params,
        n_robots=n_robots,
        n_loads=n_loads,
        demand_ratio=demand_ratio,
        heterogeneous_robots=bool(rng.choice([False, True])),
        communication_radius=communication_radius,
        position_noise_std=float(rng.uniform(0.0, 0.5)),
        reward_mode=str(rng.choice(["uniform", "proportional", "random"])),
    )


def iter_sp1_worlds(generators: Iterable[str], seeds: Iterable[int]) -> Iterable[tuple[str, str, int, SP1RecruitmentScenarioParams, WorldState]]:
    """Yield scenario variant metadata and built worlds for a list of generators."""

    for generator in generators:
        key = generator.lower()
        base_params = scenario_params_for_generator(key)
        for seed in seeds:
            if key in {"monte_carlo", "sp1_4", "sp1.4"}:
                params = sample_monte_carlo_params(seed, base_params[0])
                variant_id = f"{key}_seed{seed}"
                yield key, variant_id, seed, params, SP1RecruitmentScenario(params).build(seed)
            else:
                for idx, params in enumerate(base_params):
                    variant_id = f"{key}_v{idx:02d}"
                    yield key, variant_id, seed, params, SP1RecruitmentScenario(params).build(seed + 997 * idx)


def _robot_payloads(params: SP1RecruitmentScenarioParams, rng: np.random.Generator) -> np.ndarray:
    if not params.heterogeneous_robots:
        return np.full(params.n_robots, params.robot_payload_kg, dtype=float)
    low = 0.72 * params.robot_payload_kg
    high = 1.34 * params.robot_payload_kg
    return rng.uniform(low, high, size=params.n_robots)


def _load_demands(params: SP1RecruitmentScenarioParams, rng: np.random.Generator) -> np.ndarray:
    choices = np.asarray(params.min_cardinality_choices, dtype=int)
    choices = choices[choices > 0]
    if choices.size == 0:
        raise ValueError("min_cardinality_choices must contain positive integers.")

    demands = rng.choice(choices, size=params.n_loads, replace=True).astype(int)
    target = max(params.n_loads, int(round(params.demand_ratio * params.n_robots)))
    target = min(target, int(max(choices) * params.n_loads))

    while int(np.sum(demands)) < target:
        candidates = np.flatnonzero(demands < int(max(choices)))
        if candidates.size == 0:
            break
        demands[int(rng.choice(candidates))] += 1
    while int(np.sum(demands)) > target:
        candidates = np.flatnonzero(demands > 1)
        if candidates.size == 0:
            break
        demands[int(rng.choice(candidates))] -= 1
    return demands


def _load_reward(mode: str, demand: int, idx: int, rng: np.random.Generator) -> float:
    if mode == "proportional":
        return float(1.0 + 0.55 * demand + 0.05 * idx)
    if mode == "random":
        return float(rng.uniform(0.8, 3.8) + 0.2 * demand)
    return float(1.0 + 0.35 * demand + 0.04 * idx)

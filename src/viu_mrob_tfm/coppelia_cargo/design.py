"""Paired factorial design for the Cargo campaign."""

from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import asdict, dataclass

import numpy as np

from .config import AccelerationProfile, CampaignConfig


def _sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class FactorialCell:
    index: int
    cell_id: str
    payload_mass_kg: float
    friction_regime: str
    friction_coefficient: float
    coalition: str
    active_robot_count: int
    longitudinal_acceleration_m_s2: float

    def as_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class WorldSpec:
    cell: FactorialCell
    seed_index: int
    seed: int
    actual_payload_mass_kg: float
    actual_friction_coefficient: float
    com_offset_body_m: tuple[float, float]
    initial_pose_m_rad: tuple[float, float, float]
    target_pose_m_rad: tuple[float, float, float]
    contact_offsets_body_m: tuple[tuple[float, float], ...]
    active_robot_count: int
    profile: AccelerationProfile
    yaw_inertia_kg_m2: float
    world_hash: str

    def as_record(self) -> dict[str, object]:
        return {
            **self.cell.as_record(),
            "seed_index": self.seed_index,
            "seed": self.seed,
            "actual_payload_mass_kg": self.actual_payload_mass_kg,
            "actual_friction_coefficient": self.actual_friction_coefficient,
            "com_offset_x_m": self.com_offset_body_m[0],
            "com_offset_y_m": self.com_offset_body_m[1],
            "initial_x_m": self.initial_pose_m_rad[0],
            "initial_y_m": self.initial_pose_m_rad[1],
            "initial_yaw_rad": self.initial_pose_m_rad[2],
            "target_x_m": self.target_pose_m_rad[0],
            "target_y_m": self.target_pose_m_rad[1],
            "target_yaw_rad": self.target_pose_m_rad[2],
            "contact_offsets_body_m": json.dumps(self.contact_offsets_body_m),
            "active_robot_count": self.active_robot_count,
            "profile_peak_acceleration": json.dumps(
                self.profile.peak_acceleration_world_m_s2_rad_s2
            ),
            "profile_peak_twist": json.dumps(
                self.profile.peak_twist_world_m_s_rad_s
            ),
            "yaw_inertia_kg_m2": self.yaw_inertia_kg_m2,
            "world_hash": self.world_hash,
        }


@dataclass(frozen=True, slots=True)
class RunSpec:
    run_id: str
    phase: str
    guard: str
    dt_s: float
    world: WorldSpec

    def as_record(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "phase": self.phase,
            "guard": self.guard,
            "dt_s": self.dt_s,
            **self.world.as_record(),
        }


def factorial_cells(config: CampaignConfig) -> tuple[FactorialCell, ...]:
    """Enumerate factors in a stable, documented order."""

    combinations = itertools.product(
        config.design.payload_mass_kg,
        config.design.friction_regime,
        config.design.coalition,
        config.design.longitudinal_acceleration_m_s2,
    )
    cells = []
    for index, (mass, friction_regime, coalition, acceleration) in enumerate(combinations):
        cells.append(
            FactorialCell(
                index=index,
                cell_id=f"C{index:02d}",
                payload_mass_kg=float(mass),
                friction_regime=str(friction_regime),
                friction_coefficient=float(
                    config.design.friction_coefficients[str(friction_regime)]
                ),
                coalition=str(coalition),
                active_robot_count=len(config.design.coalitions_m[str(coalition)]),
                longitudinal_acceleration_m_s2=float(acceleration),
            )
        )
    return tuple(cells)


def _world_payload(config: CampaignConfig, cell: FactorialCell, seed_index: int, seed: int) -> dict[str, object]:
    # SeedSequence avoids order-dependent consumption between cells.
    rng = np.random.default_rng(np.random.SeedSequence([seed, cell.index]))
    perturb = config.design.perturbations
    actual_mass = cell.payload_mass_kg * (
        1.0 + rng.uniform(-perturb.mass_relative_half_range, perturb.mass_relative_half_range)
    )
    actual_friction = max(
        1.0e-6,
        cell.friction_coefficient
        + rng.uniform(-perturb.friction_absolute_half_range, perturb.friction_absolute_half_range),
    )
    com = tuple(float(x) for x in rng.uniform(-perturb.com_jitter_m, perturb.com_jitter_m, size=2))
    base = np.asarray(config.payload.initial_pose_m_rad, dtype=float)
    base[:2] += rng.uniform(-perturb.initial_pose_jitter_m, perturb.initial_pose_jitter_m, size=2)
    base[2] += rng.uniform(-perturb.initial_yaw_jitter_rad, perturb.initial_yaw_jitter_rad)
    inertia = float(
        actual_mass * (config.payload.length_m**2 + config.payload.width_m**2) / 12.0
        + actual_mass * (com[0] ** 2 + com[1] ** 2)
    )
    profile = AccelerationProfile(
        name=f"ax_{cell.longitudinal_acceleration_m_s2:.3f}_m_s2",
        peak_acceleration_world_m_s2_rad_s2=(
            cell.longitudinal_acceleration_m_s2,
            config.design.motion_envelope.peak_lateral_acceleration_m_s2,
            config.design.motion_envelope.peak_yaw_acceleration_rad_s2,
        ),
        peak_twist_world_m_s_rad_s=config.design.motion_envelope.peak_twist_world_m_s_rad_s,
    )
    return {
        "cell": cell.as_record(),
        "seed_index": seed_index,
        "seed": seed,
        "actual_payload_mass_kg": float(actual_mass),
        "actual_friction_coefficient": float(actual_friction),
        "com_offset_body_m": com,
        "initial_pose_m_rad": tuple(float(x) for x in base),
        "target_pose_m_rad": config.payload.target_pose_m_rad,
        "contact_offsets_body_m": config.design.coalitions_m[cell.coalition],
        "active_robot_count": cell.active_robot_count,
        "profile": asdict(profile),
        "yaw_inertia_kg_m2": inertia,
    }


def build_worlds(config: CampaignConfig) -> tuple[WorldSpec, ...]:
    worlds = []
    for cell in factorial_cells(config):
        for seed_index, seed in enumerate(config.design.seeds.values):
            payload = _world_payload(config, cell, seed_index, seed)
            worlds.append(
                WorldSpec(
                    cell=cell,
                    seed_index=seed_index,
                    seed=seed,
                    actual_payload_mass_kg=float(payload["actual_payload_mass_kg"]),
                    actual_friction_coefficient=float(payload["actual_friction_coefficient"]),
                    com_offset_body_m=tuple(payload["com_offset_body_m"]),
                    initial_pose_m_rad=tuple(payload["initial_pose_m_rad"]),
                    target_pose_m_rad=tuple(payload["target_pose_m_rad"]),
                    contact_offsets_body_m=tuple(payload["contact_offsets_body_m"]),
                    active_robot_count=int(payload["active_robot_count"]),
                    profile=AccelerationProfile(**payload["profile"]),
                    yaw_inertia_kg_m2=float(payload["yaw_inertia_kg_m2"]),
                    world_hash=_sha256(payload),
                )
            )
    return tuple(worlds)


def build_run_specs(config: CampaignConfig) -> tuple[RunSpec, ...]:
    """Build primary and numerical-sensitivity runs without changing worlds."""

    worlds = build_worlds(config)
    runs: list[RunSpec] = []
    for world in worlds:
        for guard in config.guards:
            runs.append(
                RunSpec(
                    run_id=f"P-{world.cell.cell_id}-S{world.seed_index:02d}-{guard}",
                    phase="primary",
                    guard=guard,
                    dt_s=config.design.primary_dt_s,
                    world=world,
                )
            )
    selected_cells = set(config.design.sensitivity.cell_indices)
    for world in worlds:
        if world.cell.index not in selected_cells or world.seed_index >= config.design.sensitivity.seeds_per_cell:
            continue
        for guard in config.guards:
            for dt in config.design.sensitivity.dt_values_s:
                runs.append(
                    RunSpec(
                        run_id=(
                            f"D-{world.cell.cell_id}-S{world.seed_index:02d}-"
                            f"{guard}-dt{float(dt):.6f}"
                        ),
                        phase="dt_sensitivity",
                        guard=guard,
                        dt_s=float(dt),
                        world=world,
                    )
                )
    return tuple(runs)


def design_hash(runs: tuple[RunSpec, ...]) -> str:
    return _sha256([run.as_record() for run in runs])


__all__ = [
    "FactorialCell",
    "RunSpec",
    "WorldSpec",
    "build_run_specs",
    "build_worlds",
    "design_hash",
    "factorial_cells",
]

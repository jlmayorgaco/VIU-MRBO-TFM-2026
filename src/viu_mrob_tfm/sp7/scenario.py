"""SP7 communication-aware cooperative transport scenarios.

SP7 studies temporal communication and sensing during cooperative payload
transport. It reuses SP5 transport worlds and sweeps radio radius, packet loss,
latency, jitter and sensor reliability. The scientific object is no longer a
static allocation graph: it is a time-varying network while several AMRs carry
or push payloads around obstacles and moving robot groups.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

import numpy as np

from viu_mrob_tfm.sp5.scenario import SP5Problem, SP5ScenarioParams, SP5TransportScenario
from viu_mrob_tfm.sp5.scenario import scenario_params_for_generator as sp5_scenario_params_for_generator


@dataclass(frozen=True, slots=True)
class CommunicationProfile:
    """Time-varying communication/sensing disturbance model."""

    profile_id: str = "nominal_full_mesh"
    communication_radius_m: float = float("inf")
    packet_loss_probability: float = 0.0
    burst_loss_probability: float = 0.0
    delay_mean_s: float = 0.02
    delay_jitter_s: float = 0.01
    latency_tolerance_s: float = 0.18
    sensor_range_m: float = 6.0
    sensor_false_negative_probability: float = 0.02
    sensor_noise_std_m: float = 0.03
    dropout_period_s: float = 0.0
    dropout_duration_s: float = 0.0

    def severity(self) -> float:
        radius_term = 0.0 if not np.isfinite(self.communication_radius_m) else float(np.clip((8.0 - self.communication_radius_m) / 7.0, 0.0, 1.0))
        loss_term = float(np.clip(self.packet_loss_probability + 0.6 * self.burst_loss_probability, 0.0, 1.0))
        delay_term = float(np.clip((self.delay_mean_s + self.delay_jitter_s) / max(self.latency_tolerance_s, 1e-9), 0.0, 2.0) / 2.0)
        sensor_term = float(np.clip(self.sensor_false_negative_probability + self.sensor_noise_std_m / 0.45, 0.0, 1.0))
        return float(np.clip(0.38 * radius_term + 0.28 * loss_term + 0.22 * delay_term + 0.12 * sensor_term, 0.0, 1.0))


@dataclass(frozen=True, slots=True)
class SP7ScenarioParams:
    """SP5 world plus SP7 network/sensor profile."""

    scenario_id: str
    sp5_generator: str
    profile: CommunicationProfile
    n_robots: int | None = None
    n_loads: int | None = None
    transport_mode: str | None = None
    description: str = ""


def communication_profiles_for_sweep(kind: str = "default") -> tuple[CommunicationProfile, ...]:
    """Return professional communication stress profiles."""

    if kind == "debug":
        return (
            CommunicationProfile(profile_id="nominal_full_mesh", communication_radius_m=float("inf")),
            CommunicationProfile(profile_id="radius_4m_loss_delay", communication_radius_m=4.0, packet_loss_probability=0.16, burst_loss_probability=0.04, delay_mean_s=0.16, delay_jitter_s=0.10, sensor_false_negative_probability=0.10, sensor_noise_std_m=0.12),
        )
    return (
        CommunicationProfile(profile_id="nominal_full_mesh", communication_radius_m=float("inf"), packet_loss_probability=0.0, delay_mean_s=0.02, delay_jitter_s=0.01),
        CommunicationProfile(profile_id="radius_9m_low_loss", communication_radius_m=9.0, packet_loss_probability=0.03, delay_mean_s=0.05, delay_jitter_s=0.03),
        CommunicationProfile(profile_id="radius_6m_moderate_loss", communication_radius_m=6.0, packet_loss_probability=0.08, burst_loss_probability=0.02, delay_mean_s=0.10, delay_jitter_s=0.06, sensor_false_negative_probability=0.06, sensor_noise_std_m=0.08),
        CommunicationProfile(profile_id="radius_4m_loss_delay", communication_radius_m=4.0, packet_loss_probability=0.16, burst_loss_probability=0.04, delay_mean_s=0.16, delay_jitter_s=0.10, sensor_false_negative_probability=0.10, sensor_noise_std_m=0.12),
        CommunicationProfile(profile_id="radius_3m_intermittent", communication_radius_m=3.0, packet_loss_probability=0.24, burst_loss_probability=0.08, delay_mean_s=0.24, delay_jitter_s=0.16, sensor_false_negative_probability=0.16, sensor_noise_std_m=0.18, dropout_period_s=9.0, dropout_duration_s=1.4),
        CommunicationProfile(profile_id="harsh_4m_35loss_400ms", communication_radius_m=4.0, packet_loss_probability=0.35, burst_loss_probability=0.10, delay_mean_s=0.40, delay_jitter_s=0.24, latency_tolerance_s=0.22, sensor_false_negative_probability=0.22, sensor_noise_std_m=0.25, dropout_period_s=7.0, dropout_duration_s=1.8),
    )


def scenario_params_for_generator(generator: str) -> tuple[SP7ScenarioParams, ...]:
    """Return named SP7 scenario/profile sweeps."""

    key = generator.lower()
    if key in {"setup", "sp7_0", "sp7.0"}:
        return (
            SP7ScenarioParams(
                scenario_id="setup_relay_chain",
                sp5_generator="formation_corridor_push",
                profile=communication_profiles_for_sweep("debug")[1],
                description="Small relay-chain smoke case: A-B-C connectivity matters during push/drag transport.",
            ),
        )
    if key == "radius_sweep_balanced_push":
        return tuple(
            SP7ScenarioParams(
                scenario_id=f"radius_sweep_balanced_push_{profile.profile_id}",
                sp5_generator="formation_corridor_push",
                profile=profile,
                n_robots=6,
                n_loads=2,
                transport_mode="push_drag",
                description="Balanced push/drag task with radio radius sweep.",
            )
            for profile in communication_profiles_for_sweep()
        )
    if key == "multi_group_obstacle_crossing":
        return tuple(
            SP7ScenarioParams(
                scenario_id=f"multi_group_obstacle_crossing_{profile.profile_id}",
                sp5_generator="multi_group_crossing_push",
                profile=profile,
                n_robots=8,
                n_loads=3,
                transport_mode="push_drag",
                description="Several AMR groups cross while a coalition transports a payload around obstacles.",
            )
            for profile in communication_profiles_for_sweep()
        )
    if key == "cargo_sensor_degradation":
        return tuple(
            SP7ScenarioParams(
                scenario_id=f"cargo_sensor_degradation_{profile.profile_id}",
                sp5_generator="cargo_overhead_delivery",
                profile=profile,
                n_robots=5,
                n_loads=2,
                transport_mode="cargo",
                description="Cargo transport under degraded sensing and communication.",
            )
            for profile in communication_profiles_for_sweep()
        )
    if key == "over_robot_relay":
        return tuple(
            SP7ScenarioParams(
                scenario_id=f"over_robot_relay_{profile.profile_id}",
                sp5_generator="overactuated_push_drag",
                profile=profile,
                n_robots=10,
                n_loads=2,
                transport_mode="push_drag",
                description="More robots than loads: redundant AMRs can serve as relays or remain idle.",
            )
            for profile in communication_profiles_for_sweep()
        )
    if key == "under_robot_multi_load":
        return tuple(
            SP7ScenarioParams(
                scenario_id=f"under_robot_multi_load_{profile.profile_id}",
                sp5_generator="scarce_cargo_multi_load",
                profile=profile,
                n_robots=4,
                n_loads=5,
                transport_mode="cargo",
                description="More loads than robots: communication stress exposes prioritization and relay scarcity.",
            )
            for profile in communication_profiles_for_sweep()
        )
    if key in {"monte_carlo", "sp7_mc"}:
        return (SP7ScenarioParams(scenario_id="monte_carlo", sp5_generator="monte_carlo", profile=CommunicationProfile(profile_id="mc_randomized"), description="Randomized SP7 communication stress mixture."),)
    raise ValueError(f"Unknown SP7 scenario generator: {generator}")


def iter_sp7_problems(
    generators: Iterable[str],
    seeds: Iterable[int],
) -> Iterable[tuple[str, str, int, SP7ScenarioParams, SP5ScenarioParams, SP5Problem]]:
    """Yield SP7 communication-stressed SP5 transport problems."""

    for generator in generators:
        key = str(generator).lower()
        base_params = scenario_params_for_generator(key)
        for seed in seeds:
            if key in {"monte_carlo", "sp7_mc"}:
                params = sample_monte_carlo_params(seed)
                sp5_params = _sp5_params_from_sp7(params, seed)
                problem = SP5TransportScenario(sp5_params).build(seed)
                problem = _with_communication_radius(problem, params.profile.communication_radius_m)
                yield key, f"{key}_{params.scenario_id}_{params.profile.profile_id}_seed{seed}", seed, params, sp5_params, problem
                continue
            for idx, params in enumerate(base_params):
                build_seed = seed + 997 * idx
                sp5_params = _sp5_params_from_sp7(params, build_seed)
                problem = SP5TransportScenario(sp5_params).build(build_seed)
                problem = _with_communication_radius(problem, params.profile.communication_radius_m)
                yield key, f"{params.scenario_id}_seed{seed}", seed, params, sp5_params, problem


def sample_monte_carlo_params(seed: int) -> SP7ScenarioParams:
    rng = np.random.default_rng(seed)
    sp5_generator = str(
        rng.choice(
            [
                "formation_corridor_push",
                "multi_group_crossing_push",
                "cargo_overhead_delivery",
                "overactuated_push_drag",
                "scarce_cargo_multi_load",
            ]
        )
    )
    mode = "cargo" if "cargo" in sp5_generator else "push_drag"
    radius = float(rng.choice([np.inf, 10.0, 8.0, 6.0, 4.5, 3.2]))
    loss = float(rng.uniform(0.0, 0.36 if np.isfinite(radius) else 0.06))
    delay = float(rng.uniform(0.02, 0.42 if np.isfinite(radius) else 0.08))
    profile = CommunicationProfile(
        profile_id=f"mc_r{_radius_tag(radius)}_loss{int(100 * loss):02d}_delay{int(1000 * delay):03d}",
        communication_radius_m=radius,
        packet_loss_probability=loss,
        burst_loss_probability=float(rng.uniform(0.0, 0.10)),
        delay_mean_s=delay,
        delay_jitter_s=float(rng.uniform(0.01, 0.22)),
        latency_tolerance_s=float(rng.uniform(0.16, 0.28)),
        sensor_range_m=float(rng.uniform(3.8, 8.5)),
        sensor_false_negative_probability=float(rng.uniform(0.01, 0.24)),
        sensor_noise_std_m=float(rng.uniform(0.02, 0.28)),
        dropout_period_s=float(rng.choice([0.0, 7.0, 9.0, 12.0])),
        dropout_duration_s=float(rng.uniform(0.0, 2.0)),
    )
    return SP7ScenarioParams(
        scenario_id=f"mc_{sp5_generator}",
        sp5_generator=sp5_generator,
        profile=profile,
        transport_mode=mode,
        description="Random communication radius/loss/delay/sensing stress.",
    )


def _sp5_params_from_sp7(params: SP7ScenarioParams, seed: int) -> SP5ScenarioParams:
    if params.sp5_generator == "monte_carlo":
        from viu_mrob_tfm.sp5.scenario import sample_monte_carlo_params as sample_sp5

        base = sample_sp5(seed)
    else:
        base = sp5_scenario_params_for_generator(params.sp5_generator)[0]
    overrides = {}
    if params.n_robots is not None:
        overrides["n_robots"] = int(params.n_robots)
    if params.n_loads is not None:
        overrides["n_loads"] = int(params.n_loads)
    if params.transport_mode is not None:
        overrides["transport_mode"] = str(params.transport_mode)
    overrides["communication_radius"] = float(params.profile.communication_radius_m)
    overrides["horizon_s"] = float(min(base.horizon_s, 42.0))
    overrides["pickup_horizon_s"] = float(min(base.pickup_horizon_s, 5.8))
    overrides["dt_s"] = float(max(base.dt_s, 0.18))
    return replace(base, **overrides)


def _with_communication_radius(problem: SP5Problem, radius: float) -> SP5Problem:
    return replace(problem, communication_radius=float(radius))


def _radius_tag(radius: float) -> str:
    return "inf" if not np.isfinite(radius) else str(int(round(radius * 10))).zfill(2)

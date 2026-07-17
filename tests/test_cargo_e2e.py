"""Invariants for the integrated Cargo campaign."""

from __future__ import annotations

import numpy as np
import pandas as pd

from viu_mrob_tfm.integrated.experiment import (
    METHODS,
    build_audit,
    build_world,
    evaluate_hypotheses,
    simulate_method,
)


def test_world_generation_is_reproducible() -> None:
    first = build_world("degraded_network", 9600, 8)
    second = build_world("degraded_network", 9600, 8)
    assert first.world_hash == second.world_hash
    assert np.array_equal(first.communication_adjacency, second.communication_adjacency)
    assert first.packet_loss == 0.25


def test_open_mission_uses_unicycle_and_reaches_target() -> None:
    world = build_world("open_nominal", 9600, 8)
    result = simulate_method(world, "distributed_full")
    assert result.docking_success
    assert result.mission_success
    assert result.max_wheel_torque_nm <= np.max(world.wheel_torque_limits_nm) + 1e-9
    assert result.wheel_energy_j > 0.0
    assert result.phase_trace[:3] == ("RECRUIT", "DOCK", "TRANSPORT")


def test_guard_prevents_representative_obstacle_collision() -> None:
    world = build_world("static_obstacle", 9600, 8)
    guarded = simulate_method(world, "distributed_full")
    unguarded = simulate_method(world, "no_physical_guard")
    assert guarded.mission_success and not guarded.collision
    assert unguarded.collision and not unguarded.mission_success


def test_repair_resumes_the_same_payload_mission() -> None:
    world = build_world("failure_during_transport", 9600, 8)
    repaired = simulate_method(world, "distributed_full")
    disabled = simulate_method(world, "no_repair")
    assert repaired.failure_triggered and repaired.recovery_success
    assert repaired.mission_success
    assert "RECOVER" in repaired.phase_trace
    assert disabled.failure_triggered and not disabled.mission_success
    assert disabled.termination_reason == "repair_disabled"


def test_local_and_global_information_are_accounted_separately() -> None:
    world = build_world("degraded_network", 9600, 8)
    local = simulate_method(world, "distributed_full")
    perfect = simulate_method(world, "perfect_information")
    assert local.messages > 0 and local.bytes_sent > 0
    assert perfect.messages == 0 and perfect.bytes_sent == 0


def test_campaign_audit_checks_pairing_and_finiteness() -> None:
    world = build_world("open_nominal", 9600, 4)
    results = [simulate_method(world, method) for method in METHODS]
    audit = build_audit([world], results, METHODS)
    assert audit["status"] == "passed"
    assert all(audit["checks"].values())


def test_multiscenario_inference_clusters_repeated_instances() -> None:
    rows = []
    scenarios = (
        "open_nominal",
        "static_obstacle",
        "degraded_network",
        "failure_during_transport",
    )
    for seed in (9700, 9701):
        for scenario in scenarios:
            for method in METHODS:
                success = 1.0
                if method == "no_physical_guard" and scenario != "open_nominal":
                    success = 0.0
                if method == "no_repair" and scenario == "failure_during_transport":
                    success = 0.0
                rows.append({
                    "world_hash": f"{scenario}-{seed}",
                    "scenario": scenario,
                    "n_robots": 4,
                    "seed": seed,
                    "method": method,
                    "mission_success": success,
                    "mission_time_s": 10.0 + (method == "decoupled_local"),
                })
    hypotheses = evaluate_hypotheses(pd.DataFrame(rows)).set_index("id")
    assert hypotheses.loc["E2E-H2", "n_pairs"] == 6
    assert hypotheses.loc["E2E-H2", "n_independent_instances"] == 2

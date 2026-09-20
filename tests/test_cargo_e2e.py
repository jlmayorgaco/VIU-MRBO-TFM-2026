"""Invariants for the integrated Cargo campaign."""

from __future__ import annotations

import numpy as np
import pandas as pd

from viu_mrob_tfm.integrated.experiment import (
    METHODS,
    _cargo_spatial_score,
    _write_tables,
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


def test_normalized_cargo_score_preserves_archived_ranking() -> None:
    world = build_world("open_nominal", 9600, 8)
    distances = np.linalg.norm(world.robot_positions - world.load_initial_pose[:2], axis=1)
    normalized = np.asarray([
        _cargo_spatial_score(world, index, float(distances[index]))
        for index in range(world.n_robots)
    ])
    archived = distances - 0.08 * world.capacities_kg - 0.025 * world.force_limits_n
    np.testing.assert_allclose(normalized, archived, rtol=0.0, atol=1e-12)
    assert np.array_equal(np.argsort(normalized, kind="stable"), np.argsort(archived, kind="stable"))


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


def test_generated_document_macros_cover_reported_cargo_effects(tmp_path) -> None:
    runs = pd.DataFrame(
        [
            {
                "method": method,
                "scenario": scenario,
                "world_hash": f"{scenario}-0",
                "mission_success": float(method != "no_repair"),
                "messages": 10.0 if method == "distributed_full" else 0.0,
                "bytes_sent": 2000.0 if method == "distributed_full" else 0.0,
                "collision": float(method == "no_physical_guard"),
                "mechanical_certificate_initial": 1.0,
            }
            for method in METHODS
            for scenario in ("degraded_network", "failure_during_transport")
        ]
    )
    summary = pd.DataFrame(
        [
            {
                "method": method,
                "n": 2,
                "mission_success_mean": 1.0,
                "collision_mean": 0.0,
                "mission_time_s_mean": 1.0,
                "recovery_time_s_mean": 0.0,
                "messages_mean": 1.0,
            }
            for method in METHODS
        ]
    )
    hypotheses = pd.DataFrame(
        [
            {
                "id": hypothesis_id,
                "metric": metric,
                "n_pairs": 2,
                "effect_a_minus_b": effect,
                "ci95_low": effect - 0.1,
                "ci95_high": effect + 0.1,
                "p_holm": p_value,
            }
            for hypothesis_id, metric, effect, p_value in (
                ("E2E-H1", "mission_time_s", -0.2, 0.08),
                ("E2E-H2", "mission_success", 0.8, 1e-6),
                ("E2E-H3", "mission_success", 0.7, 2e-5),
            )
        ]
    )

    (tmp_path / "tables").mkdir()
    _write_tables(tmp_path, runs, summary, hypotheses)
    macros = (tmp_path / "tables" / "cargo_e2e_numbers.tex").read_text(
        encoding="utf-8"
    )

    assert "\\CargoEtwoEDegradedKilobytes" in macros
    assert "\\CargoEtwoETimingCI" in macros
    assert "\\CargoEtwoEGuardPHolm" in macros
    assert "\\CargoEtwoERepairEffect" in macros

"""Semantic and lifecycle tests for the corrected CPU-only SP5 protocol."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

from viu_mrob_tfm.sp5.payload_transport import (
    build_transport_world,
    filtered_acceleration_from_velocity,
    run_payload_transport_config,
    simulate_payload_transport,
)


def test_fixed_post_docking_contacts_follow_payload_without_pose_repair() -> None:
    world = build_transport_world("open_nominal", 573000, 4)
    result = simulate_payload_transport(world, "damped_hamiltonian_raw", horizon_s=2.0)
    expected = np.asarray(
        [pose[:2] + world.robot_offsets_body @ np.array([[np.cos(pose[2]), np.sin(pose[2])], [-np.sin(pose[2]), np.cos(pose[2])]]) for pose in result.load_pose]
    )
    assert np.allclose(result.robot_positions, expected)
    assert result.positions_repaired_after_integration is False


def test_raw_safe_exec_are_separate_and_mechanics_identity_holds() -> None:
    world = build_transport_world("mobile_crossing", 573001, 8)
    result = simulate_payload_transport(world, "damped_hamiltonian_cbf", horizon_s=3.0)
    assert result.raw_wrench.shape == result.safe_wrench.shape == result.exec_wrench.shape
    assert np.max(result.mechanics_residual, initial=0.0) <= 1e-8
    assert np.any(np.linalg.norm(result.raw_wrench - result.safe_wrench, axis=1) > 1e-9) or result.guard_intervention_norm <= 1e-9


def test_filtered_velocity_maps_to_dimensionally_consistent_planar_acceleration() -> None:
    acceleration = filtered_acceleration_from_velocity(
        current_velocity=np.array([1.0, -1.0, 0.3]),
        filtered_translational_velocity=np.array([1.2, -0.7]),
        nominal_acceleration=np.array([9.0, 8.0, 0.4]),
        dt_s=0.1,
    )
    assert np.allclose(acceleration, np.array([2.0, 3.0, 0.4]))
    bounded = filtered_acceleration_from_velocity(
        current_velocity=np.zeros(3),
        filtered_translational_velocity=np.array([3.0, 4.0]),
        nominal_acceleration=np.array([0.0, 0.0, 0.25]),
        dt_s=1.0,
        max_translational_accel_mps2=2.0,
    )
    assert np.isclose(np.linalg.norm(bounded[:2]), 2.0)
    assert bounded[2] == 0.25


def test_failures_are_not_converted_to_missing_rows() -> None:
    world = build_transport_world("static_corridor", 573001, 4)
    result = simulate_payload_transport(world, "pose_pd_raw", horizon_s=0.3)
    assert result.termination_reason in {"target_reached", "collision", "timeout", "initial_collision", "numerical_failure"}
    assert int(result.target_reached) + int(result.any_collision) + int(result.timeout) + int(result.numerical_failure) >= 1


def test_pilot_smoke_writes_expected_artifacts(tmp_path: Path) -> None:
    config = {
        "experiment_id": "SP5_PAYLOAD_TEST",
        "protocol_family": "payload_transport_v2",
        "mode": "pilot",
        "output_dir": str(tmp_path / "result"),
        "seeds": {"start": 573900, "count": 1},
        "scenarios": [{"id": "open_nominal"}],
        "robot_counts": [4],
        "methods": [{"id": "pose_pd_raw"}, {"id": "damped_hamiltonian_cbf"}],
        "simulation": {"dt_s": 0.15, "horizon_s": 1.0, "stable_steps": 2},
        "hypotheses": [],
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    manifest = run_payload_transport_config(path)
    assert manifest["runs"] == 2
    assert manifest["hardware"]["gpu_used"] is False
    assert (tmp_path / "result" / "tables" / "stage_ablation.csv").exists()
    assert (tmp_path / "result" / "theory_audit.json").exists()

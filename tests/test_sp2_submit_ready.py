from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from viu_mrob_tfm.sp2_canonical.benchmark import (
    _coalition_radius_m,
    _n3_statistics,
    _paired_endpoint_statistics,
    _paired_statistics,
    _run_n3,
)
from viu_mrob_tfm.sp2_canonical.communication import (
    ChannelConfig,
    SeededLocalChannel,
    leader_follower_update,
    virtual_structure_update,
)
from viu_mrob_tfm.sp2_canonical.controllers import make_controller
from viu_mrob_tfm.sp2_canonical.dynamics import (
    PlanarPayload,
    required_wrench_body,
    required_wrench_world,
)
from viu_mrob_tfm.sp2_canonical.governor import govern_acceleration
from viu_mrob_tfm.sp2_canonical.kinematics import DifferentialDrive
from viu_mrob_tfm.sp2_canonical.mechanics import certify_supported_wrench
from viu_mrob_tfm.sp2_canonical.support import SupportContact, solve_vertical_support


def _contacts() -> list[SupportContact]:
    return [
        SupportContact(f"r{i + 1}", tuple(offset), 0.65, 90.0, 28.0)
        for i, offset in enumerate(
            [(-0.45, -0.3), (0.45, -0.3), (0.45, 0.3), (-0.45, 0.3)]
        )
    ]


def _paired_rows_for_inference() -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for seed in range(30):
        for scenario in ("S0", "S1"):
            for mode in ("raw", "governed"):
                governed = mode == "governed"
                rows.append(
                    {
                        "method": "pd",
                        "scenario": scenario,
                        "seed": seed,
                        "mode": mode,
                        "success": float(governed),
                        "physically_admissible_success": float(governed),
                        "physical_violation": float(not governed),
                        "collision": float(governed and seed < 3),
                        "final_position_error_m": 0.1 - 0.02 * float(governed),
                        "realized_violation_fraction": 0.8 - 0.6 * float(governed),
                        "realized_violation_max_duration_s": 2.0 - float(governed),
                        "minimum_realized_kinematic_margin": -1.0 + float(governed),
                        "minimum_realized_mechanical_margin": 0.2 + 0.1 * float(governed),
                    }
                )
    return pd.DataFrame(rows)


def test_paired_statistics_resample_seed_blocks() -> None:
    statistics = _paired_statistics(_paired_rows_for_inference()).iloc[0]
    assert statistics["paired_worlds"] == 60
    assert statistics["independent_seed_blocks"] == 30
    assert statistics["scenarios_per_seed"] == 2
    assert statistics["success_risk_difference"] == 1.0
    assert statistics["success_difference_ci95_low"] == 1.0
    assert statistics["success_difference_ci95_high"] == 1.0


def test_paired_endpoint_statistics_preserve_controller_scenario_blocks() -> None:
    statistics = _paired_endpoint_statistics(_paired_rows_for_inference()).set_index(
        "endpoint"
    )
    assert statistics.loc["success", "paired_world_method_rows"] == 60
    assert statistics.loc["success", "independent_seed_blocks"] == 30
    assert statistics.loc["success", "difference_governed_minus_raw"] == 1.0
    assert statistics.loc["collision", "difference_governed_minus_raw"] == 0.1


def test_world_body_wrench_bridge_preserves_power_rotation() -> None:
    payload = PlanarPayload(20.0, 2.5, 1.0, 0.2)
    acceleration = np.asarray([0.3, -0.1, 0.2])
    twist = np.asarray([0.4, 0.2, -0.1])
    world = required_wrench_world(payload, acceleration, twist)
    body = required_wrench_body(payload, acceleration, twist, np.pi / 2.0)
    assert np.allclose(body[:2], np.asarray([world[1], -world[0]]))
    assert body[2] == world[2]


def test_support_equilibrium_includes_weight_and_tipping_moments() -> None:
    certificate = solve_vertical_support(_contacts(), 20.0)
    assert certificate.feasible
    assert np.isclose(np.sum(certificate.normal_forces_n), 20.0 * 9.81)
    assert certificate.residual_norm <= 1e-7
    assert certificate.normalized_equilibrium_residual.shape == (3,)
    assert np.isfinite(certificate.normalized_equilibrium_residual).all()


def test_supported_allocator_rejects_friction_false_feasible() -> None:
    contacts = [
        SupportContact(contact.robot_id, contact.offset_body_m, 0.05, 90.0, 28.0)
        for contact in _contacts()
    ]
    certificate = certify_supported_wrench(contacts, 20.0, np.asarray([25.0, 0.0, 0.0]))
    assert not certificate.feasible
    assert certificate.residual_norm > 0.0 or certificate.utilization > 1.0
    assert certificate.diagnostic_achieved_wrench is not None
    assert certificate.diagnostic_residual_norm > 0.0


def test_supported_allocator_reports_internal_force_and_limiting_contact() -> None:
    certificate = certify_supported_wrench(_contacts(), 20.0, np.asarray([12.0, 3.0, 2.0]))
    assert certificate.feasible
    assert certificate.residual_norm <= 1e-7
    assert certificate.internal_force_ratio >= 0.0
    assert certificate.limiting_robot_id.startswith("r")


def test_all_controller_families_return_finite_acceleration() -> None:
    for method in ("pd", "pid", "lqr", "lqi", "port_hamiltonian", "mpc_central"):
        controller = make_controller(method)
        acceleration = controller.command(
            np.zeros(3), np.zeros(3), np.asarray([1.0, -0.5, 0.2]), 0.1
        )
        assert acceleration.shape == (3,)
        assert np.isfinite(acceleration).all()
        assert controller.centralized is (method == "mpc_central")


def test_local_channel_obeys_range_and_is_seed_reproducible() -> None:
    config = ChannelConfig(2.0, delay_mean_s=0.1, delay_jitter_s=0.02, loss_probability=0.2)
    message = leader_follower_update(
        coalition_id="c1",
        membership_version=2,
        sequence=7,
        pose=[0.0, 0.0, 0.0],
        twist=[0.0, 0.0, 0.0],
        sender_id="r1",
        timestamp_s=1.0,
    )
    first = SeededLocalChannel(config, 5)
    second = SeededLocalChannel(config, 5)
    delivery_a = first.send(message, "r2", np.zeros(2), np.ones(2), 1.0)
    delivery_b = second.send(message, "r2", np.zeros(2), np.ones(2), 1.0)
    assert delivery_a.delivered_at_s == delivery_b.delivered_at_s
    out_of_range = first.send(message, "r3", np.zeros(2), np.asarray([3.0, 0.0]), 1.0)
    assert out_of_range.status == "out_of_range"
    first.receive_until(float("inf"))
    assert first.stats.attempted_bytes == first.stats.queued_bytes + first.stats.dropped_bytes
    assert first.stats.queued_bytes == first.stats.delivered_bytes


def test_virtual_structure_message_preserves_covariance_metadata() -> None:
    message = virtual_structure_update(
        coalition_id="c1",
        membership_version=2,
        sequence=7,
        robot_id="r2",
        pose_estimate=[0.1, -0.2, 0.05],
        twist_estimate=[0.0, 0.0, 0.0],
        covariance_diagonal=[4e-4, 4e-4, 1e-4],
    )
    assert message["covariance_diagonal"] == [4e-4, 4e-4, 1e-4]


def test_n3_pose_errors_keep_position_and_yaw_units_separate() -> None:
    config = {
        "dt_s": 0.1,
        "updates": 4,
        "seeds": [7],
        "networks": {"ideal": {"communication_radius_m": 2.0}},
    }
    frame = _run_n3(config)
    assert {"rmse_position_m", "rmse_yaw_rad"}.issubset(frame.columns)
    assert {
        "generated_bytes",
        "queued_bytes",
        "delivered_bytes",
        "dropped_bytes",
        "mean_age_s",
        "delivery_ratio",
    }.issubset(frame.columns)
    assert "rmse" not in frame.columns
    assert np.isfinite(frame[["rmse_position_m", "rmse_yaw_rad"]].to_numpy()).all()
    assert frame["generated_bytes"].eq(frame["queued_bytes"] + frame["dropped_bytes"]).all()
    assert frame["queued_bytes"].eq(frame["delivered_bytes"]).all()


def test_n3_all_channel_intervals_resample_seed_blocks() -> None:
    config = {
        "dt_s": 0.1,
        "updates": 4,
        "seeds": [7, 8],
        "networks": {
            "ideal": {"communication_radius_m": 2.0},
            "limited": {
                "communication_radius_m": 0.7,
                "bandwidth_bytes_s": 2500.0,
            },
        },
    }
    statistics = _n3_statistics(_run_n3(config)).set_index("network")
    assert statistics.loc["all_channels", "paired_runs"] == 4
    assert statistics.loc["all_channels", "independent_seed_blocks"] == 2


def test_reduced_coalition_footprint_contains_all_robot_discs() -> None:
    geometry = {
        "payload_half_extents_m": [0.45, 0.30],
        "robot_radius_m": 0.18,
        "safety_margin_m": 0.08,
    }
    radius = _coalition_radius_m(geometry)
    expected = np.hypot(0.45, 0.30) + 0.18
    assert np.isclose(radius, expected)


def test_terminal_criterion_uses_dimensionally_separate_thresholds() -> None:
    config = yaml.safe_load(
        Path("experiments/configs/sp2_submit_ready.yaml").read_text(encoding="utf-8")
    )
    terminal = config["dynamic"]["terminal"]
    assert set(terminal) == {
        "position_tolerance_m",
        "yaw_tolerance_rad",
        "linear_speed_tolerance_mps",
        "angular_speed_tolerance_rad_s",
        "dwell_time_s",
    }
    assert config["dynamic"]["governor_sensitivity_steps"] == [0.2, 0.1, 0.05]
    assert config["dynamic"]["simulation"]["information_max_age_s"] == 0.60
    assert config["dynamic"]["simulation"]["brake_gain"] == 1.80
    assert "degraded" in config["n3"]["networks"]
    assert "lossy" not in config["n3"]["networks"]


def test_governor_scales_an_excessive_command() -> None:
    drives = [DifferentialDrive(f"r{i + 1}", 0.06, 0.32, 10.0) for i in range(4)]
    offsets = np.asarray([contact.offset_body_m for contact in _contacts()])
    result = govern_acceleration(
        np.asarray([8.0, 0.0, 0.0]),
        np.asarray([0.2, 0.0, 0.0]),
        0.0,
        PlanarPayload(20.0, 2.5, 1.0, 0.2),
        drives,
        offsets,
        _contacts(),
    )
    assert result.status == "scaled"
    assert result.scale < 1.0
    assert result.kinematic.feasible
    assert result.mechanical.feasible


def test_stale_information_brakes_a_moving_payload_with_joint_guard() -> None:
    drives = [DifferentialDrive(f"r{i + 1}", 0.06, 0.32, 10.0) for i in range(4)]
    result = govern_acceleration(
        np.asarray([0.4, 0.0, 0.0]),
        np.asarray([0.2, 0.0, 0.0]),
        0.0,
        PlanarPayload(20.0, 2.5),
        drives,
        np.asarray([contact.offset_body_m for contact in _contacts()]),
        _contacts(),
        information_fresh=False,
        candidate_guard=lambda candidate: bool(candidate[0] <= 0.0),
    )
    assert result.status == "brake"
    assert result.scale == 0.0
    assert result.brake_scale > 0.0
    assert np.dot(result.executed_acceleration, np.asarray([0.2, 0.0, 0.0])) < 0.0
    assert result.kinematic.feasible
    assert result.mechanical.feasible
    assert result.auxiliary_guard_feasible


def test_each_nominal_scale_is_revalidated_against_the_auxiliary_guard() -> None:
    drives = [DifferentialDrive(f"r{i + 1}", 0.06, 0.32, 10.0) for i in range(4)]
    result = govern_acceleration(
        np.asarray([0.4, 0.0, 0.0]),
        np.zeros(3),
        0.0,
        PlanarPayload(20.0, 2.5),
        drives,
        np.asarray([contact.offset_body_m for contact in _contacts()]),
        _contacts(),
        scale_grid=np.asarray([1.0, 0.75, 0.5, 0.25, 0.0]),
        candidate_guard=lambda candidate: bool(candidate[0] <= 0.2 + 1e-12),
    )
    assert result.status == "scaled"
    assert result.scale == 0.5
    assert result.executed_acceleration[0] == 0.2
    assert result.auxiliary_guard_feasible


def test_stale_information_only_holds_an_already_stationary_payload() -> None:
    drives = [DifferentialDrive(f"r{i + 1}", 0.06, 0.32, 10.0) for i in range(4)]
    result = govern_acceleration(
        np.asarray([0.4, 0.0, 0.0]),
        np.zeros(3),
        0.0,
        PlanarPayload(20.0, 2.5),
        drives,
        np.asarray([contact.offset_body_m for contact in _contacts()]),
        _contacts(),
        information_fresh=False,
    )
    assert result.status == "hold"
    assert np.allclose(result.executed_acceleration, 0.0)


def test_missing_support_is_reported_as_uncontrolled_stop_required() -> None:
    drives = [DifferentialDrive(f"r{i + 1}", 0.06, 0.32, 10.0) for i in range(4)]
    unsupported_contacts = [
        SupportContact(contact.robot_id, contact.offset_body_m, 0.65, 1.0, 28.0)
        for contact in _contacts()
    ]
    result = govern_acceleration(
        np.asarray([0.4, 0.0, 0.0]),
        np.asarray([0.2, 0.0, 0.0]),
        0.0,
        PlanarPayload(20.0, 2.5),
        drives,
        np.asarray([contact.offset_body_m for contact in unsupported_contacts]),
        unsupported_contacts,
    )
    assert result.status == "uncontrolled_stop_required"
    assert result.scale == 0.0
    assert result.brake_scale == 0.0
    assert not result.mechanical.feasible


def test_nonzero_departure_acceleration_selects_a_heading() -> None:
    drives = [DifferentialDrive(f"r{i + 1}", 0.06, 0.32, 10.0) for i in range(4)]
    result = govern_acceleration(
        np.asarray([0.4, 0.1, 0.0]),
        np.zeros(3),
        0.0,
        PlanarPayload(20.0, 2.5),
        drives,
        np.asarray([contact.offset_body_m for contact in _contacts()]),
        _contacts(),
    )
    assert result.status == "accepted"
    assert all(robot.feasible for robot in result.kinematic.robots)
    assert all(robot.aligned_heading_rad is not None for robot in result.kinematic.robots)

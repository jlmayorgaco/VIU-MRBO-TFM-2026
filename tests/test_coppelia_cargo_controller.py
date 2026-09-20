from __future__ import annotations

import inspect
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from viu_mrob_tfm.coppelia_cargo import evaluate_guard, load_config
from viu_mrob_tfm.coppelia_cargo.controller import (
    CargoPoseController,
    Observation,
    allocate_contact_wrench,
)
from viu_mrob_tfm.coppelia_cargo.design import WorldSpec, build_worlds


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "experiments" / "configs" / "coppelia_cargo_smoke.yaml"


def _observation(
    world: WorldSpec,
    robot_count: int,
    *,
    normal_force_n: float = 100.0,
    measured_wrench_body: np.ndarray | None = None,
    contact_active: np.ndarray | None = None,
) -> Observation:
    active = np.arange(robot_count) < world.active_robot_count
    normal = np.zeros(robot_count)
    normal[active] = normal_force_n
    contacts = active if contact_active is None else contact_active
    robot_pose = np.zeros((robot_count, 3))
    robot_pose[:, 2] = world.initial_pose_m_rad[2]
    return Observation(
        time_s=0.0,
        payload_pose_m_rad=np.asarray(world.initial_pose_m_rad, dtype=float),
        payload_twist_m_s_rad_s=np.zeros(3),
        robot_pose_m_rad=robot_pose,
        wheel_speed_rad_s=np.zeros((robot_count, 2)),
        wheel_drive_force_n=np.zeros((robot_count, 2)),
        measured_wrench_body=(
            np.zeros(3)
            if measured_wrench_body is None
            else np.asarray(measured_wrench_body, dtype=float)
        ),
        normal_force_n=normal,
        contact_active=np.asarray(contacts, dtype=bool),
        active_robot_mask=active,
        relative_slip_m=np.zeros(robot_count),
        collision_count=0,
    )


def test_controller_configuration_declares_si_admittance() -> None:
    control = load_config(SMOKE).control
    assert control.controller_id == "cargo_pose_wrench_admittance_wheel_v2"
    assert control.contact_force_admittance_m_s_per_n > 0.0
    assert control.wrench_force_admittance_m_s_per_n > 0.0
    assert control.wrench_torque_admittance_rad_s_per_n_m > 0.0
    assert 0.0 < control.admittance_twist_limit_fraction <= 1.0


def test_observation_validates_force_shape_and_finiteness() -> None:
    config = load_config(SMOKE)
    world = build_worlds(config)[0]
    valid = _observation(world, config.robot.count)
    with pytest.raises(ValueError, match="wheel_drive_force_n"):
        replace(valid, wheel_drive_force_n=np.zeros((config.robot.count, 1)))
    bad_wrench = valid.measured_wrench_body.copy()
    bad_wrench[0] = np.nan
    with pytest.raises(FloatingPointError, match="measured_wrench_body"):
        replace(valid, measured_wrench_body=bad_wrench)


def test_reference_wrench_obeys_si_mass_and_damping_balance() -> None:
    config = load_config(SMOKE)
    source = build_worlds(config)[0]
    world = replace(
        source,
        actual_payload_mass_kg=20.0,
        initial_pose_m_rad=(0.0, 0.0, 0.0),
        target_pose_m_rad=(1.0, 0.0, 0.0),
    )
    observation = _observation(world, config.robot.count)
    command = CargoPoseController(config).command(
        world,
        observation,
        config.design.primary_dt_s,
    )
    acceleration_x = command.desired_acceleration_world_m_s2_rad_s2[0]
    desired_velocity_x = acceleration_x * config.design.primary_dt_s
    expected_force_n = (
        world.actual_payload_mass_kg * acceleration_x
        + config.payload.linear_damping_n_s_m * desired_velocity_x
    )
    assert np.isclose(command.reference_wrench_body[0], expected_force_n)
    assert np.isclose(command.reference_wrench_body[1], 0.0)


def test_bounded_allocation_reports_residual_and_respects_inactive_robot() -> None:
    config = load_config(SMOKE)
    world = build_worlds(config)[0]
    observation = _observation(
        world,
        config.robot.count,
        normal_force_n=1.0,
    )
    desired = np.asarray([100.0, -80.0, 40.0])
    allocation = allocate_contact_wrench(config, world, observation, desired)

    norms = np.linalg.norm(allocation.force_setpoint_body_n, axis=1)
    assert np.all(norms <= allocation.contact_force_limit_n + 1.0e-10)
    assert np.array_equal(allocation.force_setpoint_body_n[3], np.zeros(2))
    assert allocation.contact_force_limit_n[3] == 0.0
    assert allocation.residual_normalized > 0.0
    assert allocation.saturation_count > 0
    assert np.allclose(
        allocation.residual_body,
        allocation.achieved_wrench_body - desired,
    )

    command = CargoPoseController(config).command(
        world,
        observation,
        config.design.primary_dt_s,
    )
    assert np.array_equal(command.wheel_speed_rad_s[3], np.zeros(2))
    assert np.max(np.abs(command.wheel_speed_rad_s)) <= (
        config.robot.max_wheel_speed_rad_s + 1.0e-12
    )


def test_lost_contact_is_removed_from_allocation_and_wheel_command() -> None:
    config = load_config(SMOKE)
    world = build_worlds(config)[0]
    contacts = np.asarray([True, False, True, False])
    observation = _observation(
        world,
        config.robot.count,
        contact_active=contacts,
    )
    command = CargoPoseController(config).command(
        world,
        observation,
        config.design.primary_dt_s,
    )
    assert np.array_equal(command.contact_force_setpoint_body_n[1], np.zeros(2))
    assert np.array_equal(command.wheel_speed_rad_s[1], np.zeros(2))
    assert np.array_equal(command.wheel_speed_rad_s[3], np.zeros(2))


def test_wrench_feedback_has_declared_admittance_units() -> None:
    config = load_config(SMOKE)
    world = build_worlds(config)[0]
    controller = CargoPoseController(config)
    zero_measurement = _observation(world, config.robot.count)
    preliminary = controller.command(
        world,
        zero_measurement,
        config.design.primary_dt_s,
    )
    matched = replace(
        zero_measurement,
        measured_wrench_body=preliminary.allocated_wrench_body.copy(),
    )
    one_newton_short = replace(
        matched,
        measured_wrench_body=(
            preliminary.allocated_wrench_body - np.asarray([1.0, 0.0, 0.0])
        ),
    )
    matched_command = controller.command(
        world,
        matched,
        config.design.primary_dt_s,
    )
    short_command = controller.command(
        world,
        one_newton_short,
        config.design.primary_dt_s,
    )
    assert np.allclose(matched_command.admittance_twist_body_m_s_rad_s, 0.0)
    assert np.isclose(
        short_command.admittance_twist_body_m_s_rad_s[0],
        config.control.wrench_force_admittance_m_s_per_n,
    )
    assert np.allclose(
        short_command.contact_force_setpoint_body_n,
        matched_command.contact_force_setpoint_body_n,
    )


def test_guard_label_cannot_change_the_controller_law() -> None:
    config = load_config(SMOKE)
    world = build_worlds(config)[0]
    observation = _observation(world, config.robot.count)
    controller = CargoPoseController(config)
    assert "guard" not in inspect.signature(controller.command).parameters

    commands = []
    for guard in config.guards:
        evaluate_guard(config, world, guard)
        commands.append(
            controller.command(world, observation, config.design.primary_dt_s)
        )
    assert {command.controller_id for command in commands} == {
        config.control.controller_id
    }
    assert all(
        np.array_equal(commands[0].wheel_speed_rad_s, command.wheel_speed_rad_s)
        for command in commands[1:]
    )
    assert all(
        np.array_equal(
            commands[0].contact_force_setpoint_body_n,
            command.contact_force_setpoint_body_n,
        )
        for command in commands[1:]
    )

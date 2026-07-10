"""Tests for the closed-form AMR control law integrated from the control notes."""

from __future__ import annotations

import math

import numpy as np
import pytest

from viu_mrob_tfm.control import (
    CircularHazard,
    ExplicitControlGains,
    closed_form_hocbf_projection,
    hand_point,
    inverse_unicycle_dynamics,
    required_wrench_pd,
    saturate_force_torque,
    vgne_force_share,
)


def test_hand_point_matches_unicycle_lookahead_kinematics() -> None:
    h, h_dot = hand_point(
        position_xy=np.array([1.0, 2.0]),
        theta=math.pi / 2.0,
        linear_speed=0.8,
        angular_speed=0.5,
        lookahead_m=0.2,
    )

    np.testing.assert_allclose(h, np.array([1.0, 2.2]), atol=1e-12)
    np.testing.assert_allclose(h_dot, np.array([-0.1, 0.8]), atol=1e-12)


def test_required_wrench_reproduces_pdf_guided_example() -> None:
    wrench, accel = required_wrench_pd(
        mass_total_kg=157.0,
        inertia_total_kgm2=76.16,
        pose=np.array([2.0, 1.5, math.radians(10.0)]),
        twist=np.array([0.80, 0.50, 0.05]),
        target_pose=np.array([2.10, 1.55, math.radians(12.0)]),
        target_twist=np.array([0.85, 0.53, 0.06]),
        target_acceleration=np.array([0.30, 0.19, 0.02]),
        gains=ExplicitControlGains(load_position_bandwidth=1.0, load_orientation_bandwidth=1.0),
    )

    np.testing.assert_allclose(accel[:2], np.array([0.50, 0.30]), atol=1e-12)
    np.testing.assert_allclose(wrench[:2], np.array([78.5, 47.1]), atol=1e-12)
    assert wrench[2] == pytest.approx(5.7049, rel=2e-4)


def test_vgne_force_share_closes_force_and_pure_torque_when_offsets_are_centered() -> None:
    offsets = [
        np.array([1.0, 0.0]),
        np.array([-1.0, 0.0]),
        np.array([0.0, 1.0]),
        np.array([0.0, -1.0]),
    ]
    wrench = np.array([0.0, 0.0, 4.0])
    shares = np.vstack([vgne_force_share(wrench, offset, eta_i=1.0, h_sum=4.0, s_sum=4.0) for offset in offsets])
    total_force = shares.sum(axis=0)
    total_torque = sum(float(offset[0] * force[1] - offset[1] * force[0]) for offset, force in zip(offsets, shares))

    np.testing.assert_allclose(total_force, np.zeros(2), atol=1e-12)
    assert total_torque == pytest.approx(4.0, abs=1e-12)


def test_hocbf_projection_reduces_inward_acceleration() -> None:
    nominal = np.array([-2.0, 0.0])
    safe = closed_form_hocbf_projection(
        nominal,
        hand_xy=np.array([1.0, 0.0]),
        hand_velocity_xy=np.zeros(2),
        hazards=[CircularHazard(center_xy=np.zeros(2), velocity_xy=np.zeros(2), radius_m=0.8)],
        safety_distance_m=0.0,
        gains=ExplicitControlGains(safety_k1=2.8, safety_k2=2.8),
    )

    assert safe[0] > nominal[0]
    assert np.isfinite(safe).all()


def test_inverse_unicycle_and_uniform_saturation_are_finite_and_direction_preserving() -> None:
    force, torque = inverse_unicycle_dynamics(
        np.array([1.2, -0.4]),
        theta=0.0,
        linear_speed=0.6,
        angular_speed=0.2,
        mass_kg=20.0,
        inertia_kgm2=1.0,
        linear_friction=3.0,
        angular_friction=0.2,
        lookahead_m=0.15,
    )
    saturated_force, saturated_torque, sigma = saturate_force_torque(force, torque, force_limit_n=10.0, torque_limit_nm=2.0)

    assert np.isfinite([force, torque, saturated_force, saturated_torque, sigma]).all()
    assert 0.0 < sigma <= 1.0
    assert saturated_force / force == pytest.approx(saturated_torque / torque)

"""Invariants for the sampled local-navigation comparators."""

from __future__ import annotations

import numpy as np

from viu_mrob_tfm.sp5.local_navigation import BarrierConstraint, predictive_navigation_step


def test_predictive_proxy_is_bounded_finite_and_preserves_diagnostic_simplex() -> None:
    step = predictive_navigation_step(
        position=[0.0, 0.0],
        goal=[2.0, 0.2],
        current_velocity=[0.0, 0.0],
        preference=[1 / 3, 1 / 3, 1 / 3],
        constraints=[BarrierConstraint(np.array([-1.0, 0.0]), 0.8, "front")],
        dt_s=0.05,
        max_speed_mps=1.0,
        max_accel_mps2=2.0,
        goal_gain=1.2,
        barrier_gamma=1.5,
        projection_sweeps=12,
        horizon_s=1.0,
        heading_samples=11,
        clearance_weight=3.0,
        effort_weight=0.03,
        wait_cost=0.8,
    )
    assert np.isfinite(step.position).all()
    assert np.isfinite(step.exec_velocity).all()
    assert np.isclose(step.preference.sum(), 1.0)
    assert np.all(step.preference >= 0.0)
    assert np.linalg.norm(step.exec_velocity) <= 1.0 + 1e-12
    assert np.linalg.norm(step.exec_velocity) <= 2.0 * 0.05 + 1e-12
    assert step.safe_residual <= 1e-9


def test_predictive_proxy_rejects_nonpositive_horizon() -> None:
    try:
        predictive_navigation_step(
            position=[0.0, 0.0],
            goal=[1.0, 0.0],
            current_velocity=[0.0, 0.0],
            preference=[1 / 3, 1 / 3, 1 / 3],
            constraints=[],
            dt_s=0.05,
            max_speed_mps=1.0,
            max_accel_mps2=2.0,
            goal_gain=1.0,
            barrier_gamma=1.0,
            projection_sweeps=4,
            horizon_s=0.0,
            heading_samples=5,
            clearance_weight=1.0,
            effort_weight=0.0,
            wait_cost=0.0,
        )
    except ValueError:
        return
    raise AssertionError("zero predictive horizon must be rejected")

"""Deterministic Gate 0 tests for the canonical MegaGame validation plan."""

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "validation_v1"))

from gate0 import (  # noqa: E402
    BeliefRecord,
    BeliefStore,
    body_velocity,
    caging_friction_feasible,
    difference_utility,
    hocbf_terms,
    run_math_checks,
    smith_euler,
    smith_rhs,
    wheel_speeds,
    wrench_map,
    wrench_residual,
)


def test_gate0_math_physical_bundle_passes() -> None:
    result = run_math_checks()
    assert result["status"] == "passed"
    assert result["wrench_relative_residual"] < 1e-2


def test_smith_preserves_simplex_under_digital_update() -> None:
    rng = np.random.default_rng(20260920)
    for _ in range(200):
        x = rng.dirichlet(np.ones(5))
        payoff = rng.normal(size=5)
        rhs = smith_rhs(x, payoff, gain=0.45)
        updated = smith_euler(x, payoff, dt=0.02, gain=0.45)
        assert abs(float(rhs.sum())) < 1e-12
        assert np.all(updated >= -1e-12)
        assert np.isclose(updated.sum(), 1.0, atol=1e-12)


def test_difference_utility_matches_social_variation() -> None:
    phi = lambda s: s[0] ** 2 + 3.0 * s[1] ** 2 + s[0] * s[1]
    baseline = (0.0, 0.0)
    old, new = (0.2, -0.3), (0.8, -0.3)
    utility_change = difference_utility(phi, new, baseline, 0) - difference_utility(phi, old, baseline, 0)
    assert np.isclose(utility_change, -(phi(new) - phi(old)))


def test_wrench_and_caging_constraints() -> None:
    contacts = np.array([[-0.8, 0.0], [0.8, 0.0], [0.0, 0.8]])
    target = np.array([1.0, 0.4, 0.15])
    force_vector, *_ = np.linalg.lstsq(wrench_map(contacts), target, rcond=None)
    residual = wrench_residual(contacts, force_vector.reshape(-1, 2), target)
    assert np.linalg.norm(residual) < 1e-10
    assert caging_friction_feasible([1.0, 0.8], [0.2, -0.1], [0.5, 0.3])
    assert not caging_friction_feasible([1.0, -0.1], [0.2, 0.0], [0.5, 0.3])


def test_differential_drive_round_trip_and_hocbf() -> None:
    left, right = wheel_speeds(0.6, -0.4, 0.1, 0.24)
    assert np.allclose(body_velocity(left, right, 0.1, 0.24), [0.6, -0.4])
    h, hdot, hddot, barrier = hocbf_terms([2.0, 0.0], [0.0, 0.0], [0.0, 0.0], 1.0, 3.0, 3.8)
    assert h > 0 and hdot == 0 and hddot == 0 and barrier >= 0


def test_gossip_deduplicates_and_keeps_latest_sequence() -> None:
    store = BeliefStore()
    latest = BeliefRecord(3, "intention", 14, (0.4, 0.6), 1.0, 0, 1.0)
    assert store.receive(latest, now=1.0)
    assert not store.receive(latest, now=1.1)
    assert not store.receive(BeliefRecord(3, "intention", 12, (0.0, 1.0), 1.0, 1, 1.0), now=1.1)
    assert store.receive(BeliefRecord(3, "intention", 15, (0.3, 0.7), 1.2, 2, 1.0), now=1.2)
    assert store.records[(3, "intention")].seq == 15
    assert store.accepted_updates == 2

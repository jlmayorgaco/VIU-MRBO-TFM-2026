"""Closed-form predictions used by the SP9 gap study."""

from __future__ import annotations

import math


def rho_loop_prediction(k_p: float) -> float:
    """Return the closed-loop rate rho_L = sqrt(k_p)."""

    if k_p < 0:
        raise ValueError("k_p must be non-negative.")
    return math.sqrt(k_p)


def consensus_time_prediction(c_gain: float, lambda2: float) -> float:
    """Return the approximate consensus time 1 / (c * lambda2)."""

    denominator = c_gain * lambda2
    if denominator <= 0:
        return math.inf
    return 1.0 / denominator


def n_min_prediction(mass_total: float, acceleration_max: float, disturbance: float, force_max: float) -> int:
    """Return ceil(M_T * (a_max + d_bar) / F_max)."""

    if force_max <= 0:
        raise ValueError("force_max must be positive.")
    return int(math.ceil(max(0.0, mass_total) * max(0.0, acceleration_max + disturbance) / force_max))


def cbf_clearance_prediction(safety_distance: float) -> float:
    """Return the minimum clearance predicted by an ideal CBF invariant set."""

    if safety_distance < 0:
        raise ValueError("safety_distance must be non-negative.")
    return safety_distance

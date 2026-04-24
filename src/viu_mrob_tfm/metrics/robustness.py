"""Robustness-oriented placeholder metrics."""

from __future__ import annotations


def robustness_score(
    baseline_error: float,
    disturbed_error: float,
) -> float:
    """Return a simple normalized degradation score."""

    denominator = baseline_error if baseline_error != 0.0 else 1.0
    return float(1.0 - ((disturbed_error - baseline_error) / denominator))

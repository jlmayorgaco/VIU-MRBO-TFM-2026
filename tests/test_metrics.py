"""Metric smoke tests."""

import numpy as np

from viu_mrob_tfm.metrics import (
    control_effort,
    formation_error,
    tracking_error_series,
    trajectory_tracking_error,
)


def test_metric_functions_return_numeric_outputs() -> None:
    actual = np.array([[0.0, 0.0], [1.0, 1.0]])
    reference = np.array([[0.0, 0.0], [1.5, 1.5]])
    control = np.array([[0.1, 0.0], [0.2, 0.1]])

    series = tracking_error_series(actual, reference)
    mean_error = trajectory_tracking_error(actual, reference)
    spacing_error = formation_error(actual, reference)
    effort = control_effort(control)

    assert series.shape == (2,)
    assert isinstance(mean_error, float)
    assert isinstance(spacing_error, float)
    assert isinstance(effort, float)

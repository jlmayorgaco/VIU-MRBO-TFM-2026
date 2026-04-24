"""Default configuration factories used across experiments and tests."""

from __future__ import annotations

from pathlib import Path

from viu_mrob_tfm.config.schema import (
    ControllerConfig,
    ExperimentConfig,
    GraphConfig,
    LoadConfig,
    SimulationConfig,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = REPOSITORY_ROOT / "results"


def default_experiment_config() -> ExperimentConfig:
    """Return a conservative default experiment specification."""

    return ExperimentConfig(
        name="exp-default-placeholder",
        description="Baseline placeholder experiment for early repository wiring.",
        controller=ControllerConfig(type="nominal"),
        simulation=SimulationConfig(),
        load=LoadConfig(),
        graph=GraphConfig(
            adjacency=[
                [0.0, 1.0, 1.0],
                [1.0, 0.0, 1.0],
                [1.0, 1.0, 0.0],
            ]
        ),
        metrics=[
            "tracking_error",
            "formation_error",
            "control_effort",
        ],
    )

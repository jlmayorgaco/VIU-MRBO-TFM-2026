"""Runner used by scripts and future automation hooks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from viu_mrob_tfm.config.schema import ExperimentConfig
from viu_mrob_tfm.controllers.adaptive_consensus import AdaptiveConsensusController
from viu_mrob_tfm.controllers.nominal_consensus import NominalConsensusController
from viu_mrob_tfm.estimators.inertial_uncertainty import InertialUncertaintyEstimator
from viu_mrob_tfm.simulations.scenario import SimulationScenario
from viu_mrob_tfm.simulations.simulator import Simulator
from viu_mrob_tfm.utils.io import ensure_directory, load_yaml, save_json


@dataclass(slots=True)
class ExperimentRunner:
    """Thin orchestration layer for loading a config and saving results."""

    results_root: Path = Path("results/raw")

    def run(self, config_path: str | Path) -> dict[str, Any]:
        """Run a configured experiment and persist a JSON summary."""

        path = Path(config_path)
        config = ExperimentConfig.from_dict(load_yaml(path))
        scenario = SimulationScenario.from_config(config)
        controller_type = config.controller.type.lower()

        if controller_type == "adaptive":
            estimator = InertialUncertaintyEstimator()
            controller = AdaptiveConsensusController(
                graph=scenario.graph,
                estimator=estimator,
                adaptation_gain=config.controller.parameters.get("adaptation_gain", 0.2),
            )
        else:
            estimator = None
            controller = NominalConsensusController(
                graph=scenario.graph,
                consensus_gain=config.controller.parameters.get("consensus_gain", 1.0),
                tracking_gain=config.controller.parameters.get("tracking_gain", 0.5),
            )
        setattr(controller, "treatment", controller_type)
        setattr(controller, "parameters", dict(config.controller.parameters))

        simulator = Simulator(scenario=scenario, controller=controller, estimator=estimator)
        results = simulator.run()

        output_dir = ensure_directory(self.results_root / config.name)
        metrics = _compute_summary_metrics(results)
        arrays = {key: value for key, value in results.items() if isinstance(value, np.ndarray)}
        np.savez_compressed(output_dir / "results.npz", **arrays)
        summary = {
            "experiment": config.name,
            "description": config.description,
            "controller": controller.name,
            "treatment": results.get("treatment", controller_type),
            "steps": int(len(results["time"])),
            "output_dir": str(output_dir),
            "metrics": metrics,
        }
        save_json(output_dir / "summary.json", summary)
        return summary


def _compute_summary_metrics(results: dict[str, Any]) -> dict[str, Any]:
    time = np.asarray(results["time"], dtype=float)
    duration = float(time[-1] - time[0]) if time.size > 1 else 0.0
    duration_min = max(duration / 60.0, 1e-9)
    completion_times = np.asarray(results.get("task_completion_times", []), dtype=float)
    coalition_times = np.asarray(results.get("task_coalition_times", []), dtype=float)
    completed = np.isfinite(completion_times)
    ever_feasible = np.isfinite(coalition_times)
    trajectory = np.asarray(results.get("trajectory", []), dtype=float)
    controls = np.asarray(results.get("controls", []), dtype=float)
    assignments = np.asarray(results.get("assignments", []), dtype=int)
    task_feasible = np.asarray(results.get("task_feasible", []), dtype=bool)

    total_distance = 0.0
    if trajectory.ndim == 3 and trajectory.shape[0] > 1:
        total_distance = float(np.sum(np.linalg.norm(np.diff(trajectory, axis=0), axis=2)))

    effort = 0.0
    if controls.ndim >= 2:
        effort = float(np.sum(np.linalg.norm(controls, axis=-1)))

    assignment_change_rate = 0.0
    if assignments.ndim == 2 and assignments.shape[0] > 1:
        assignment_change_rate = float(np.mean(assignments[1:] != assignments[:-1]))

    mean_coalition_time = None
    if np.any(ever_feasible):
        mean_coalition_time = float(np.nanmean(coalition_times[ever_feasible]))

    mean_completion_time = None
    if np.any(completed):
        mean_completion_time = float(np.nanmean(completion_times[completed]))

    return {
        "completed_tasks": int(np.sum(completed)),
        "task_count": int(completion_times.size),
        "completion_rate": float(np.mean(completed)) if completion_times.size else 0.0,
        "throughput_tasks_per_min": float(np.sum(completed) / duration_min),
        "ever_feasible_tasks": int(np.sum(ever_feasible)),
        "ever_feasible_rate": float(np.mean(ever_feasible)) if coalition_times.size else 0.0,
        "time_feasible_rate": float(np.mean(task_feasible)) if task_feasible.size else 0.0,
        "mean_coalition_time_s": mean_coalition_time,
        "mean_completion_time_s": mean_completion_time,
        "feasibility_rate": float(np.mean(task_feasible)) if task_feasible.size else 0.0,
        "assignment_change_rate": assignment_change_rate,
        "total_distance_m": total_distance,
        "control_effort": effort,
    }

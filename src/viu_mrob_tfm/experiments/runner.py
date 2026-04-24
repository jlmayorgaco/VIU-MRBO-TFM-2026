"""Runner used by scripts and future automation hooks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

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

        simulator = Simulator(scenario=scenario, controller=controller, estimator=estimator)
        results = simulator.run()

        output_dir = ensure_directory(self.results_root / config.name)
        summary = {
            "experiment": config.name,
            "description": config.description,
            "controller": controller.name,
            "steps": int(len(results["time"])),
            "output_dir": str(output_dir),
        }
        save_json(output_dir / "summary.json", summary)
        return summary

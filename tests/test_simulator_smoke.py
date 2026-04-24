"""Simulator smoke test."""

from viu_mrob_tfm.config.defaults import default_experiment_config
from viu_mrob_tfm.controllers.nominal_consensus import NominalConsensusController
from viu_mrob_tfm.simulations import SimulationScenario, Simulator


def test_simulator_can_be_instantiated() -> None:
    config = default_experiment_config()
    scenario = SimulationScenario.from_config(config)
    controller = NominalConsensusController(graph=scenario.graph)
    simulator = Simulator(scenario=scenario, controller=controller)

    results = simulator.run()

    assert simulator.scenario.name == config.name
    assert "time" in results
    assert "trajectory" in results

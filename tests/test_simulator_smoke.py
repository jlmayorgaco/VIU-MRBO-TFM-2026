"""Simulator smoke tests."""

from pathlib import Path

import numpy as np

from viu_mrob_tfm.config.defaults import default_experiment_config
from viu_mrob_tfm.controllers.nominal_consensus import NominalConsensusController
from viu_mrob_tfm.domain import AMR, AMRState, CommunicationGraph, LoadState, TransportedLoad
from viu_mrob_tfm.experiments.runner import ExperimentRunner
from viu_mrob_tfm.simulations import (
    FailureEvent,
    ObstacleSpec,
    SimulationScenario,
    Simulator,
    TaskSpec,
)


def test_simulator_can_be_instantiated() -> None:
    config = default_experiment_config()
    scenario = SimulationScenario.from_config(config)
    controller = NominalConsensusController(graph=scenario.graph)
    simulator = Simulator(scenario=scenario, controller=controller)

    results = simulator.run()

    assert simulator.scenario.name == config.name
    assert "time" in results
    assert "trajectory" in results


def test_all_treatment_policies_run_on_default_scenario() -> None:
    config = default_experiment_config()
    config.simulation.duration = 18.0
    treatments = [
        "t1_greedy",
        "t2_dac_greedy",
        "t3_replicator",
        "t4_smith",
        "t5_centralized",
        "t6_single_clock",
    ]

    for treatment in treatments:
        scenario = SimulationScenario.from_config(config)
        controller = NominalConsensusController(graph=scenario.graph)
        controller.treatment = treatment
        results = Simulator(scenario=scenario, controller=controller).run()

        assert results["treatment"] == treatment
        assert results["trajectory"].shape[1] == config.simulation.amr_count
        assert results["assignments"].shape == (
            len(results["time"]),
            config.simulation.amr_count,
        )
        if treatment == "t6_single_clock":
            assert "prices" in results
            assert float(np.max(results["prices"])) > 0.0
            assert float(np.max(results["prices"])) <= 1.0


def test_kinematic_loop_forms_coalition_and_delivers_load() -> None:
    config = default_experiment_config()
    config.simulation.duration = 20.0
    scenario = SimulationScenario.from_config(config)
    controller = NominalConsensusController(graph=scenario.graph)
    simulator = Simulator(scenario=scenario, controller=controller)

    results = simulator.run()

    assert results["task_modes"][-1, 0] == 2
    assert np.isfinite(results["task_completion_times"][0])
    np.testing.assert_allclose(
        results["load_trajectory"][-1],
        scenario.tasks[0].destination,
        atol=scenario.detection_radius,
    )


def test_obstacle_reactive_layer_keeps_clearance_and_completes() -> None:
    config = default_experiment_config()
    config.simulation.duration = 25.0
    scenario = SimulationScenario.from_config(config)
    obstacle = ObstacleSpec(center=np.array([2.7, 0.0]), radius=0.35, influence_radius=1.4)
    scenario.obstacles.append(obstacle)
    controller = NominalConsensusController(graph=scenario.graph)

    results = Simulator(scenario=scenario, controller=controller).run()
    distances = np.linalg.norm(results["trajectory"] - obstacle.center, axis=2)

    assert results["task_modes"][-1, 0] == 2
    assert float(np.min(distances)) > obstacle.radius


def test_failure_event_triggers_recruitment_and_nearby_help() -> None:
    graph = CommunicationGraph(np.ones((4, 4), dtype=float) - np.eye(4, dtype=float))
    amrs = [
        AMR(f"amr-{idx + 1}", AMRState(position=np.array(position), heading=0.0))
        for idx, position in enumerate(
            [
                [-2.0, -0.8],
                [-2.0, 0.0],
                [-2.0, 0.8],
                [-2.0, 3.0],
            ]
        )
    ]
    load = TransportedLoad(state=LoadState(position=np.array([1.5, 0.0])))
    tasks = [
        TaskSpec(
            identifier="heavy",
            pickup=np.array([1.5, 0.0]),
            destination=np.array([4.5, 0.0]),
            min_coalition_size=3,
            reward=1.8,
        ),
        TaskSpec(
            identifier="light",
            pickup=np.array([1.5, 3.0]),
            destination=np.array([4.5, 3.0]),
            min_coalition_size=1,
            reward=0.8,
        ),
    ]
    scenario = SimulationScenario(
        name="failure-reorganization",
        amrs=amrs,
        transported_load=load,
        graph=graph,
        duration=25.0,
        time_step=0.1,
        tasks=tasks,
        failure_events=[FailureEvent(time=6.0, agent_index=0)],
    )

    results = Simulator(
        scenario=scenario,
        controller=NominalConsensusController(graph=scenario.graph),
    ).run()

    assert not results["active"][-1, 0]
    assert np.all(results["task_modes"][-1] == 2)
    assert np.all(np.isfinite(results["task_completion_times"]))
    assert bool(np.any(results["task_feasible"][70:, 0]))


def test_experiment_runner_saves_metrics_and_npz() -> None:
    workspace_tmp = Path("results/raw/_pytest_runner_smoke")
    workspace_tmp.mkdir(parents=True, exist_ok=True)
    config_path = workspace_tmp / "config.yaml"
    config_path.write_text(
        """
name: runner-smoke
description: Runner smoke with YAML scenario fields.
controller:
  type: t4_smith
  parameters:
    beta: 2.0
    revision_rate: 0.8
simulation:
  duration: 12.0
  time_step: 0.1
  amr_count: 3
  dimensions: 2
  random_seed: 2026
  initial_positions:
    - [-2.0, -0.8]
    - [-2.0, 0.0]
    - [-2.0, 0.8]
load:
  nominal_mass: 25.0
  nominal_inertia: 3.0
  mass_uncertainty_ratio: 0.0
  center_of_mass_shift: [0.0, 0.0]
graph:
  adjacency:
    - [0.0, 1.0, 1.0]
    - [1.0, 0.0, 1.0]
    - [1.0, 1.0, 0.0]
tasks:
  - identifier: load-1
    pickup: [1.5, 0.0]
    destination: [4.5, 0.0]
    min_coalition_size: 2
    reward: 1.0
metrics:
  - completion_rate
""",
        encoding="utf-8",
    )
    runner = ExperimentRunner(results_root=workspace_tmp / "results")

    summary = runner.run(config_path)

    output_dir = workspace_tmp / "results" / "runner-smoke"
    assert summary["treatment"] == "t4_smith"
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "results.npz").exists()
    assert summary["metrics"]["completed_tasks"] == 1

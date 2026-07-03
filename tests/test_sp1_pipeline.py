"""SP1 recruitment pipeline tests."""

from __future__ import annotations

import json

import numpy as np
import pytest
import yaml

from viu_mrob_tfm.allocation import DecisionContext, timed_allocate
from viu_mrob_tfm.sp1.methods import (
    CentralizedCoalitionOracleAllocator,
    SP1_METHOD_LABELS,
    make_sp1_allocator,
)
from viu_mrob_tfm.sp1.metrics import evaluate_assignment
from viu_mrob_tfm.sp1.runner import run_sp1_config
from viu_mrob_tfm.sp1.scenario import (
    SP1RecruitmentScenario,
    SP1RecruitmentScenarioParams,
    iter_sp1_worlds,
    scenario_params_for_generator,
)


SP1_GENERATORS = ["setup", "under_demand", "balanced_demand", "over_demand", "monte_carlo"]
SP1_METHODS = list(SP1_METHOD_LABELS)


def test_sp1_setup_generator_matches_requested_demand() -> None:
    params = scenario_params_for_generator("setup")[0]
    world = SP1RecruitmentScenario(params).build(seed=123)

    assert len(world.robots) == 4
    assert len(world.loads) == 1
    assert world.loads[0].min_coalition_size == 2
    assert all(robot.identifier.startswith("amr-") for robot in world.robots)


@pytest.mark.parametrize("generator", SP1_GENERATORS)
def test_sp1_each_scenario_generator_produces_valid_worlds(generator: str) -> None:
    worlds = list(iter_sp1_worlds([generator], seeds=[123]))

    assert worlds
    for scenario_generator, _variant_id, _seed, params, world in worlds:
        assert scenario_generator == generator
        assert len(world.robots) == params.n_robots
        assert len(world.loads) == params.n_loads
        assert all(robot.spec.capacity.payload_kg > 0.0 for robot in world.robots)
        assert all(load.mass_kg > 0.0 for load in world.loads)
        assert all(load.min_coalition_size >= 1 for load in world.loads)
        demand_ratio = sum(load.min_coalition_size for load in world.loads) / len(world.robots)
        if generator == "under_demand":
            assert demand_ratio < 1.0
        elif generator == "balanced_demand":
            assert demand_ratio == pytest.approx(1.0)
        elif generator == "over_demand":
            assert demand_ratio > 1.0


@pytest.mark.parametrize("method_id", SP1_METHODS)
def test_sp1_each_method_returns_valid_assignment(method_id: str) -> None:
    params = SP1RecruitmentScenarioParams(n_robots=5, n_loads=2, demand_ratio=1.0)
    world = SP1RecruitmentScenario(params).build(seed=11)
    context = DecisionContext(world=world, metadata={"communication_radius": params.communication_radius})

    assignment = make_sp1_allocator(method_id).allocate(context)

    assert assignment.labels.shape == (5,)
    assert assignment.labels.min() >= 0
    assert assignment.labels.max() <= len(world.loads)


def test_sp1_debug_config_writes_outputs(tmp_path) -> None:
    config = {
        "experiment_id": "SP1_TEST_smoke",
        "mode": "monte_carlo",
        "output_dir": str(tmp_path / "sp1"),
        "scenarios": [{"id": "SP1_recruitment", "param_generator": "setup"}],
        "methods": [{"id": "greedy_nearest"}, {"id": "centralized_coalition_milp"}],
        "seeds": {"start": 2000, "count": 2},
        "artifacts": {"save_video": False},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest = run_sp1_config(config_path)

    assert manifest["experiment_id"] == "SP1_TEST_smoke"
    assert (tmp_path / "sp1" / "tables" / "runs.csv").exists()
    assert (tmp_path / "sp1" / "tables" / "summary.csv").exists()
    assert (tmp_path / "sp1" / "report.md").exists()


def test_sp1_marl_compatible_training_uses_70_30_split_and_validates_on_new_data(tmp_path) -> None:
    checkpoint_dir = tmp_path / "checkpoint"
    config = {
        "training_id": "SP1_TEST_mappo_training",
        "mode": "train_mappo",
        "scenarios": [{"id": "SP1_recruitment", "param_generator": "setup"}],
        "train_seeds": {"start": 0, "count": 7},
        "validation_seeds": {"start": 1000, "count": 3},
        "algorithm": {
            "params": {
                "total_episodes": 32,
                "rollout_horizon": 8,
                "ppo_epochs": 3,
                "hidden_dim": 16,
                "learning_rate": 0.003,
                "random_seed": 44,
            }
        },
        "output": {"checkpoint_dir": str(checkpoint_dir)},
    }
    config_path = tmp_path / "train.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest = run_sp1_config(config_path)
    model_path = checkpoint_dir / "model.json"
    weights_path = checkpoint_dir / "model.pt"
    history_path = checkpoint_dir / "training_history.csv"
    validation_path = checkpoint_dir / "validation_metrics.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    history = history_path.read_text(encoding="utf-8")

    assert manifest["train_seed_count"] == 7
    assert manifest["validation_seed_count"] == 3
    assert model["model_version"] == "sp1-mappo-v4"
    assert weights_path.exists()
    assert "policy_loss" in history
    assert "value_loss" in history
    assert validation["validation_runs"] == 3
    assert validation["demand_satisfaction_ratio_mean"] > 0.0

    trained = make_sp1_allocator("mappo_recruitment", {"checkpoint": model_path})
    trained_score = _mean_validation_demand_satisfaction(trained, seeds=[2000, 2001, 2002])

    assert trained_score > 0.0


def test_sp1_model_based_tuning_uses_holdout_validation(tmp_path) -> None:
    artifact = tmp_path / "best_params.yaml"
    config = {
        "experiment_id": "SP1_TEST_tune",
        "mode": "tune_model_based",
        "output_dir": str(tmp_path / "tuning"),
        "scenarios": [{"id": "SP1_recruitment", "param_generator": "setup"}],
        "methods": [{"id": "replicator_cardinality"}],
        "seeds": {"start": 0, "count": 7},
        "validation_seeds": {"start": 1000, "count": 3},
        "tuning": {
            "output_artifact": str(artifact),
            "method_param_grid": {
                "replicator_cardinality": {
                    "distance_weight": [0.22],
                    "deficit_weight": [1.0],
                    "idle_score": [0.0, 999.0],
                }
            },
        },
    }
    config_path = tmp_path / "tune.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest = run_sp1_config(config_path)
    tuned = yaml.safe_load(artifact.read_text(encoding="utf-8"))
    best_params = tuned["best_params"]["replicator_cardinality"]["params"]
    validation_scores = (tmp_path / "tuning" / "validation_scores.csv").read_text(encoding="utf-8")

    assert manifest["seed_count"] == 7
    assert manifest["validation_seed_count"] == 3
    assert best_params["idle_score"] == 0.0
    assert "validation_score" in validation_scores

    holdout_seeds = [2000, 2001, 2002]
    best_score = _mean_candidate_penalty("replicator_cardinality", best_params, holdout_seeds)
    bad_score = _mean_candidate_penalty(
        "replicator_cardinality",
        {"distance_weight": 0.22, "deficit_weight": 1.0, "idle_score": 999.0},
        holdout_seeds,
    )
    assert best_score < bad_score


def _mean_validation_demand_satisfaction(allocator, seeds: list[int]) -> float:
    values = []
    for _generator, _variant_id, _seed, params, world in iter_sp1_worlds(["monte_carlo"], seeds=seeds):
        context = DecisionContext(world=world, metadata={"communication_radius": params.communication_radius})
        oracle_assignment, _ = timed_allocate(CentralizedCoalitionOracleAllocator(), context)
        assignment, runtime_ms = timed_allocate(allocator, context)
        metrics = evaluate_assignment(
            world,
            assignment,
            runtime_ms=runtime_ms,
            oracle_assignment=oracle_assignment,
            communication_radius=params.communication_radius,
        )
        values.append(metrics.demand_satisfaction_ratio)
    return float(np.mean(values))


def _mean_candidate_penalty(method_id: str, params: dict[str, float], seeds: list[int]) -> float:
    penalties = []
    for _generator, _variant_id, _seed, scenario_params, world in iter_sp1_worlds(["setup"], seeds=seeds):
        context = DecisionContext(world=world, metadata={"communication_radius": scenario_params.communication_radius})
        oracle_assignment, _ = timed_allocate(CentralizedCoalitionOracleAllocator(), context)
        assignment, runtime_ms = timed_allocate(make_sp1_allocator(method_id, params), context)
        metrics = evaluate_assignment(
            world,
            assignment,
            runtime_ms=runtime_ms,
            oracle_assignment=oracle_assignment,
            communication_radius=scenario_params.communication_radius,
        )
        penalties.append(
            (1.0 - metrics.coalition_success_rate)
            + 0.15 * metrics.robots_underassigned
            + 0.08 * metrics.robots_overassigned
            + metrics.optimality_gap_vs_oracle
            + 0.0002 * metrics.communication_messages
        )
    return float(np.mean(penalties))

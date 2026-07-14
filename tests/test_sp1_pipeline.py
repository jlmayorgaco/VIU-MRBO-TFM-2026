"""SP1 recruitment pipeline tests."""

from __future__ import annotations

import json
from itertools import product
from pathlib import Path

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
from viu_mrob_tfm.sp1 import runner as sp1_runner
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


def test_sp1_oracle_uses_binary_milp_and_leaves_surplus_robots_idle() -> None:
    params = SP1RecruitmentScenarioParams(
        n_robots=4,
        n_loads=1,
        demand_ratio=0.5,
        min_cardinality_choices=(2,),
        position_noise_std=0.0,
    )
    world = SP1RecruitmentScenario(params).build(seed=19)
    oracle = CentralizedCoalitionOracleAllocator()
    assignment = oracle.allocate(DecisionContext(world=world))
    metrics = evaluate_assignment(world, assignment, runtime_ms=0.0, oracle_assignment=assignment, centralized=True)

    assert oracle.last_solve_status == "optimal"
    assert np.sum(assignment.labels > 0) == 2
    assert metrics.idle_robots == 2
    assert metrics.fully_served_load_fraction == 1.0


def test_sp1_partial_coalition_is_not_counted_as_served() -> None:
    params = SP1RecruitmentScenarioParams(
        n_robots=4,
        n_loads=1,
        demand_ratio=0.5,
        min_cardinality_choices=(2,),
        position_noise_std=0.0,
    )
    world = SP1RecruitmentScenario(params).build(seed=23)
    partial = np.array([1, 0, 0, 0], dtype=int)
    from viu_mrob_tfm.allocation import Assignment

    metrics = evaluate_assignment(world, Assignment(labels=partial), runtime_ms=0.0)
    assert metrics.coalition_success_rate == 0.0
    assert metrics.fully_served_load_fraction == 0.0
    assert metrics.robots_in_incomplete_coalitions == 1
    assert metrics.unmet_quorum == 1


def test_sp1_milp_matches_bruteforce_on_enumerable_instance() -> None:
    params = SP1RecruitmentScenarioParams(
        n_robots=4,
        n_loads=2,
        demand_ratio=1.0,
        min_cardinality_choices=(1, 2),
        heterogeneous_robots=True,
    )
    world = SP1RecruitmentScenario(params).build(seed=31)
    oracle = CentralizedCoalitionOracleAllocator()
    assignment = oracle.allocate(DecisionContext(world=world))

    def objective(labels: np.ndarray) -> float:
        value = 0.0
        for load_idx, load in enumerate(world.loads):
            members = np.flatnonzero(labels == load_idx + 1)
            if members.size == 0:
                continue
            payload = sum(world.robots[int(idx)].spec.capacity.payload_kg for idx in members)
            if members.size < load.min_coalition_size or payload + 1e-9 < load.min_capacity_kg:
                return -np.inf
            value += float(load.reward) - oracle.overassignment_weight * (members.size - load.min_coalition_size)
        for robot_idx, label in enumerate(labels):
            if label > 0:
                value -= oracle.distance_weight * float(
                    np.linalg.norm(world.robots[robot_idx].position - world.loads[int(label) - 1].pickup)
                )
        return value

    brute_best = max(objective(np.asarray(labels, dtype=int)) for labels in product(range(3), repeat=4))
    assert oracle.last_solve_status == "optimal"
    assert objective(assignment.labels) == pytest.approx(brute_best, abs=1e-8)


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
    assert (tmp_path / "sp1" / "tables" / "performance_ranking.csv").exists()
    assert (tmp_path / "sp1" / "figures" / "sp1_performance_matrix_by_method.png").exists()
    assert (tmp_path / "sp1" / "figures" / "sp1_taxonomy_scope_family_ownership.png").exists()
    assert (tmp_path / "sp1" / "figures" / "sp1_communication_radius_degradation.png").exists()
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
    assert model["model_version"] == "sp1-mappo-v5"
    assert model["rollout_action_mode"] == "sampled_policy"
    assert model["actor_trainable_parameters"] > 0
    assert model["training_trainable_parameters"] >= model["actor_trainable_parameters"]
    assert weights_path.exists()
    assert "policy_loss" in history
    assert "value_loss" in history
    assert validation["validation_runs"] == 3
    assert validation["demand_satisfaction_ratio_mean"] > 0.0
    assert "optimality_gap_vs_oracle_mean" in validation
    assert "energy_proxy_wh_mean" in validation

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
    assert tuned["best_params"]["replicator_cardinality"]["selection_split"] == "validation"
    assert best_params["idle_score"] == 0.0
    assert "selection_split" in validation_scores
    assert "validation_score" in validation_scores

    holdout_seeds = [2000, 2001, 2002]
    best_score = _mean_candidate_penalty("replicator_cardinality", best_params, holdout_seeds)
    bad_score = _mean_candidate_penalty(
        "replicator_cardinality",
        {"distance_weight": 0.22, "deficit_weight": 1.0, "idle_score": 999.0},
        holdout_seeds,
    )
    assert best_score < bad_score


def test_sp1_monte_carlo_writes_scenario_videos_and_theory_artifacts(tmp_path, monkeypatch) -> None:
    def fake_snapshot(_world, _assignment, path, _title):
        path.write_text("snapshot", encoding="utf-8")

    def fake_video(_world, _assignment, path, _title, **_kwargs):
        path.write_text("video", encoding="utf-8")
        return True

    monkeypatch.setattr(sp1_runner, "save_recruitment_snapshot", fake_snapshot)
    monkeypatch.setattr(sp1_runner, "save_recruitment_video", fake_video)
    config = {
        "experiment_id": "SP1_TEST_video_hypotheses",
        "mode": "monte_carlo",
        "output_dir": str(tmp_path / "sp1"),
        "scenarios": [
            {"id": "SP1_recruitment", "param_generator": "setup"},
            {"id": "SP1_recruitment", "param_generator": "balanced_demand"},
        ],
        "methods": [{"id": "centralized_coalition_milp"}, {"id": "greedy_nearest"}],
        "seeds": {"start": 2000, "count": 2},
        "hypotheses": [
            {
                "id": "H_TEST_methods_differ",
                "class": "PairedSuperiorityHypothesis",
                "metric": "optimality_gap_vs_oracle",
                "treatment": "centralized_coalition_milp",
                "control": "greedy_nearest",
                "alternative": "less",
                "paired_by": ["scenario_generator", "scenario_variant_id", "seed"],
            }
        ],
        "artifacts": {
            "save_video": True,
            "video": {
                "save_per_method": True,
                "save_median_run": True,
                "selection_metric": "demand_satisfaction_ratio",
                "duration_s": 2,
                "final_hold_s": 0.5,
            },
        },
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest = run_sp1_config(config_path)

    assert {item["scenario_generator"] for item in manifest["scenario_videos"]} == {"balanced_demand", "setup"}
    assert {item["method"] for item in manifest["scenario_videos"]} == {"centralized_coalition_milp", "greedy_nearest"}
    assert all(item["method_family"] in {"classic", "model_based_oracle"} for item in manifest["scenario_videos"])
    assert all(item["method_scope"] in {"centralized", "decentralized"} for item in manifest["scenario_videos"])
    assert any("reference_model-based-oracle_centralized" in Path(item["video"]).stem for item in manifest["scenario_videos"])
    assert any("baseline_classic_decentralized" in Path(item["video"]).stem for item in manifest["scenario_videos"])
    assert all((tmp_path / "sp1" / "videos" / Path(item["video"]).name).exists() for item in manifest["scenario_videos"])
    assert (tmp_path / "sp1" / "tables" / "theory_checks.csv").exists()
    assert (tmp_path / "sp1" / "tables" / "hypothesis_results.csv").exists()
    hypothesis_text = (tmp_path / "sp1" / "tables" / "hypothesis_results.csv").read_text(encoding="utf-8")
    assert "p_value_holm" in hypothesis_text
    assert "reject_holm" in hypothesis_text
    assert (tmp_path / "sp1" / "figures" / "sp1_ours_vs_baselines_vs_reference.png").exists()
    assert (tmp_path / "sp1" / "figures" / "sp1_reference_gap_proposed_methods.png").exists()
    assert (tmp_path / "sp1" / "figures" / "sp1_best_method_by_scenario.png").exists()
    assert (tmp_path / "sp1" / "figures" / "sp1_quality_resource_pareto.png").exists()
    assert (tmp_path / "sp1" / "figures" / "sp1_physical_cost_tradeoff.png").exists()
    runs_text = (tmp_path / "sp1" / "tables" / "runs.csv").read_text(encoding="utf-8")
    assert "travel_distance_m" in runs_text
    assert "energy_proxy_wh" in runs_text
    assert "method_trainable_parameters" in runs_text
    assert "method_training_type" in runs_text
    summary_text = (tmp_path / "sp1" / "tables" / "summary.csv").read_text(encoding="utf-8")
    assert "method_family" in summary_text
    assert "method_scope" in summary_text
    assert "method_ownership" in summary_text
    assert "p_value_holm" not in summary_text.splitlines()[0]
    audit = json.loads((tmp_path / "sp1" / "theory_audit.json").read_text(encoding="utf-8"))
    assert audit["failed_checks"] == 0


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

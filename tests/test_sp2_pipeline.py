"""SP2 capacity-aware pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from viu_mrob_tfm.allocation import DecisionContext, timed_allocate
from viu_mrob_tfm.sp2 import runner as sp2_runner
from viu_mrob_tfm.sp2.methods import (
    CentralizedCapacityMILPAllocator,
    SP2_METHOD_LABELS,
    effective_capacity_matrix,
    make_sp2_allocator,
)
from viu_mrob_tfm.sp2.metrics import evaluate_assignment, load_diagnostics
from viu_mrob_tfm.sp2.runner import run_sp2_config
from viu_mrob_tfm.sp2.scenario import (
    SP2CapacityScenario,
    SP2CapacityScenarioParams,
    iter_sp2_worlds,
    scenario_params_for_generator,
)


SP2_GENERATORS = ["setup", "light_mixed", "balanced_capacity", "heavy_capacity", "battery_constrained", "monte_carlo"]
SP2_METHODS = [method for method in SP2_METHOD_LABELS if method not in {"oracle_reference", "capacity_oracle_reference"}]


def test_sp2_setup_generator_builds_capacity_problem() -> None:
    params = scenario_params_for_generator("setup")[0]
    world = SP2CapacityScenario(params).build(seed=123)

    assert len(world.robots) == 5
    assert len(world.loads) == 2
    assert all(robot.identifier.startswith("amr-") for robot in world.robots)
    assert all(robot.spec.capacity.payload_kg > 0.0 for robot in world.robots)
    assert all(load.mass_kg == pytest.approx(load.min_capacity_kg) for load in world.loads)
    assert sum(load.mass_kg for load in world.loads) == pytest.approx(params.capacity_ratio * sum(robot.spec.capacity.payload_kg for robot in world.robots))


@pytest.mark.parametrize("generator", SP2_GENERATORS)
def test_sp2_each_scenario_generator_produces_valid_worlds(generator: str) -> None:
    worlds = list(iter_sp2_worlds([generator], seeds=[123]))

    assert worlds
    for scenario_generator, _variant_id, _seed, params, world in worlds:
        assert scenario_generator == generator
        assert len(world.robots) == params.n_robots
        assert len(world.loads) == params.n_loads
        assert all(robot.spec.capacity.payload_kg > 0.0 for robot in world.robots)
        assert all(0.0 <= robot.battery_fraction <= 1.0 for robot in world.robots)
        assert all(load.mass_kg > 0.0 for load in world.loads)
        assert all(load.min_coalition_size >= 1 for load in world.loads)


@pytest.mark.parametrize("method_id", SP2_METHODS)
def test_sp2_each_method_returns_valid_assignment(method_id: str) -> None:
    params = SP2CapacityScenarioParams(n_robots=6, n_loads=3, capacity_ratio=0.95, battery_variation=True)
    world = SP2CapacityScenario(params).build(seed=11)
    context = DecisionContext(world=world, metadata={"communication_radius": params.communication_radius, "distance_decay_m": params.distance_decay_m})

    assignment = make_sp2_allocator(method_id).allocate(context)

    assert assignment.labels.shape == (6,)
    assert assignment.labels.min() >= 0
    assert assignment.labels.max() <= len(world.loads)


def test_sp2_metrics_include_capacity_shortage_waste_and_oracle_gap() -> None:
    params = SP2CapacityScenarioParams(n_robots=5, n_loads=2, capacity_ratio=0.9, battery_variation=False)
    world = SP2CapacityScenario(params).build(seed=44)
    context = DecisionContext(world=world, metadata={"communication_radius": params.communication_radius, "distance_decay_m": params.distance_decay_m})
    oracle_assignment, _oracle_runtime = timed_allocate(CentralizedCapacityMILPAllocator(), context)
    capacity_oracle_assignment, _capacity_runtime = timed_allocate(make_sp2_allocator("capacity_oracle_reference"), context)
    assignment, runtime_ms = timed_allocate(make_sp2_allocator("greedy_capacity_nearest"), context)

    metrics = evaluate_assignment(
        world,
        assignment,
        runtime_ms=runtime_ms,
        oracle_assignment=oracle_assignment,
        capacity_oracle_assignment=capacity_oracle_assignment,
        communication_radius=params.communication_radius,
        distance_decay_m=params.distance_decay_m,
    )
    diagnostics = load_diagnostics(world, assignment, communication_radius=params.communication_radius, distance_decay_m=params.distance_decay_m)

    assert 0.0 <= metrics.capacity_satisfaction_ratio <= 1.0
    assert metrics.under_capacity_kg >= 0.0
    assert metrics.over_capacity_kg >= 0.0
    assert metrics.energy_proxy_wh >= 0.0
    assert metrics.optimality_gap_vs_oracle >= 0.0
    assert metrics.capacity_gap_vs_capacity_oracle >= 0.0
    assert metrics.incomplete_capacity_kg >= 0.0
    assert 0.0 <= metrics.incomplete_capacity_ratio <= 1.0
    assert 0.0 <= metrics.served_capacity_alignment <= 1.0
    assert metrics.effective_feasibility_ratio >= metrics.capacity_satisfaction_ratio - 1e-9
    assert np.isfinite(metrics.signed_score_delta_vs_oracle)
    assert 0.0 <= metrics.communication_coverage_ratio <= 1.0
    assert len(diagnostics) == len(world.loads)
    assert {"required_capacity_kg", "assigned_effective_capacity_kg", "assigned_visible_robots", "status"} <= set(diagnostics[0])
    assert effective_capacity_matrix(context).shape == (len(world.robots), len(world.loads))


def test_sp2_plain_and_marginal_payoff_variants_are_auditable() -> None:
    params = SP2CapacityScenarioParams(n_robots=7, n_loads=3, capacity_ratio=1.05, battery_variation=True)
    world = SP2CapacityScenario(params).build(seed=51)
    context = DecisionContext(world=world, metadata={"communication_radius": params.communication_radius, "distance_decay_m": params.distance_decay_m})

    for method_id in ["replicator_capacity_plain", "replicator_capacity_marginal", "smith_capacity_plain", "smith_capacity_marginal"]:
        assignment = make_sp2_allocator(method_id).allocate(context)

        assert assignment.labels.shape == (len(world.robots),)
        assert assignment.labels.min() >= 0
        assert assignment.labels.max() <= len(world.loads)

    plain = sp2_runner.sp2_potential_alignment("smith_capacity_plain")
    marginal = sp2_runner.sp2_potential_alignment("smith_capacity_marginal")

    assert plain["payoff_uses_marginal_capacity"] is False
    assert plain["potential_structure"] == "not_guaranteed_unless_eik_factorizes"
    assert marginal["payoff_uses_marginal_capacity"] is True
    assert marginal["potential_structure"] == "exact"

    repaired_marginal = sp2_runner.sp2_potential_alignment("smith_capacity_marginal_repair")
    repaired_heuristic = sp2_runner.sp2_potential_alignment("pid_capacity_repair")

    assert repaired_marginal["payoff_uses_marginal_capacity"] is True
    assert repaired_marginal["potential_structure"] == "marginal_payoff_plus_monotone_finite_local_repair"
    assert repaired_heuristic["payoff_uses_marginal_capacity"] is False
    assert repaired_heuristic["potential_structure"] == "heuristic_payoff_plus_monotone_finite_local_repair"


def test_sp2_data_driven_training_uses_holdout_validation_and_test(tmp_path) -> None:
    checkpoint_dir = tmp_path / "checkpoint"
    config = {
        "training_id": "SP2_TEST_capacity_data_driven",
        "mode": "train_imitation",
        "training": {
            "model_type": "both",
            "output_dir": str(checkpoint_dir),
            "linear_artifact": str(checkpoint_dir / "model.json"),
            "neural_artifact": str(checkpoint_dir / "neural_model.json"),
            "neural_hidden_dim": 6,
            "neural_epochs": 12,
            "neural_learning_rate": 0.02,
            "random_seed": 44,
        },
        "scenarios": [{"id": "SP2_capacity", "param_generator": "setup"}],
        "train_seeds": {"start": 0, "count": 7},
        "validation_seeds": {"start": 1000, "count": 3},
        "test_seeds": {"start": 2000, "count": 2},
        "quality_gates": {
            "default": {
                "validation": {
                    "capacity_satisfaction_ratio_mean_min": 0.1,
                    "optimality_gap_vs_oracle_mean_max": 1.0,
                }
            }
        },
    }
    config_path = tmp_path / "train.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest = run_sp2_config(config_path)
    linear_model = json.loads((checkpoint_dir / "model.json").read_text(encoding="utf-8"))
    neural_model = json.loads((checkpoint_dir / "neural_model.json").read_text(encoding="utf-8"))
    validation = json.loads((checkpoint_dir / "validation_metrics.json").read_text(encoding="utf-8"))
    neural_validation = json.loads((checkpoint_dir / "neural_capacity_scorer_validation_metrics.json").read_text(encoding="utf-8"))

    assert manifest["train_seed_count"] == 7
    assert manifest["validation_seed_count"] == 3
    assert manifest["test_seed_count"] == 2
    assert set(manifest["checkpoints"]) == {"imitation_capacity", "neural_capacity_scorer"}
    assert linear_model["model_version"] == "sp2-imitation-capacity-linear-v2"
    assert neural_model["model_version"] == "sp2-neural-capacity-imitation-v2"
    assert neural_model["trainable_parameters"] > linear_model["trainable_parameters"]
    assert validation["validation_runs"] == 3
    assert neural_validation["validation_runs"] == 3
    assert "optimality_gap_vs_oracle_mean" in validation
    assert "capacity_gap_vs_capacity_oracle_mean" in validation
    assert "capacity_satisfaction_ratio_mean" in neural_validation
    assert (checkpoint_dir / "quality_gates.json").exists()
    assert (checkpoint_dir / "test_runs.csv").exists()
    assert (checkpoint_dir / "neural_capacity_scorer_test_runs.csv").exists()


def test_sp2_monte_carlo_writes_videos_plots_and_theory_artifacts(tmp_path, monkeypatch) -> None:
    def fake_snapshot(_world, _assignment, path, _title, **_kwargs):
        Path(path).write_text("snapshot", encoding="utf-8")

    def fake_video(_world, _assignment, path, _title, **_kwargs):
        Path(path).write_text("video", encoding="utf-8")
        return True

    monkeypatch.setattr(sp2_runner, "save_capacity_snapshot", fake_snapshot)
    monkeypatch.setattr(sp2_runner, "save_capacity_video", fake_video)
    config = {
        "experiment_id": "SP2_TEST_video_hypotheses",
        "mode": "monte_carlo",
        "output_dir": str(tmp_path / "sp2"),
        "scenarios": [
            {"id": "SP2_capacity", "param_generator": "setup"},
            {"id": "SP2_capacity", "param_generator": "battery_constrained"},
        ],
        "methods": [{"id": "centralized_capacity_milp"}, {"id": "greedy_capacity_nearest"}],
        "seeds": {"start": 3100, "count": 2},
        "hypotheses": [
            {
                "id": "H_TEST_capacity_gap",
                "metric": "optimality_gap_vs_oracle",
                "method_a": "centralized_capacity_milp",
                "method_b": "greedy_capacity_nearest",
                "direction": "less",
            }
        ],
        "artifacts": {"save_video": True, "video": {"max_per_scenario": 2, "selection_metric": "capacity_satisfaction_ratio", "duration_s": 2, "final_hold_s": 0.5}},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest = run_sp2_config(config_path)

    assert {item["scenario_generator"] for item in manifest["scenario_videos"]} == {"battery_constrained", "setup"}
    assert {item["method"] for item in manifest["scenario_videos"]} == {"centralized_capacity_milp", "greedy_capacity_nearest"}
    assert any("reference_model-based-oracle_centralized" in Path(item["video"]).stem for item in manifest["scenario_videos"])
    assert any("baseline_classic_decentralized" in Path(item["video"]).stem for item in manifest["scenario_videos"])
    assert all((tmp_path / "sp2" / "videos" / Path(item["video"]).name).exists() for item in manifest["scenario_videos"])
    assert (tmp_path / "sp2" / "tables" / "runs.csv").exists()
    assert (tmp_path / "sp2" / "tables" / "load_status.csv").exists()
    assert (tmp_path / "sp2" / "tables" / "performance_ranking.csv").exists()
    assert (tmp_path / "sp2" / "tables" / "theory_checks.csv").exists()
    assert (tmp_path / "sp2" / "tables" / "hypothesis_results.csv").exists()
    assert (tmp_path / "sp2" / "figures" / "sp2_capacity_satisfaction_by_method.png").exists()
    assert (tmp_path / "sp2" / "figures" / "sp2_performance_matrix_by_method.png").exists()
    assert (tmp_path / "sp2" / "figures" / "sp2_quality_resource_pareto.png").exists()
    assert (tmp_path / "sp2" / "figures" / "sp2_capacity_coverage_vs_completion.png").exists()
    assert (tmp_path / "sp2" / "figures" / "sp2_communication_radius_degradation.png").exists()
    runs_text = (tmp_path / "sp2" / "tables" / "runs.csv").read_text(encoding="utf-8")
    assert "capacity_satisfaction_ratio" in runs_text
    assert "capacity_gap_vs_capacity_oracle" in runs_text
    assert "signed_score_delta_vs_oracle" in runs_text
    assert "under_capacity_kg" in runs_text
    assert "incomplete_capacity_ratio" in runs_text
    assert "served_capacity_alignment" in runs_text
    assert "method_trainable_parameters" in runs_text
    audit = json.loads((tmp_path / "sp2" / "theory_audit.json").read_text(encoding="utf-8"))
    assert audit["failed_checks"] == 0
    assert audit["potential_alignment"]["effective_capacity_pair_dependent"] is True
    assert audit["potential_alignment"]["theorem"] == "Teorema 2"


def test_sp2_model_based_tuning_uses_holdout_validation(tmp_path) -> None:
    artifact = tmp_path / "best_params.yaml"
    config = {
        "experiment_id": "SP2_TEST_tune",
        "mode": "tune_model_based",
        "output_dir": str(tmp_path / "tuning"),
        "scenarios": [{"id": "SP2_capacity", "param_generator": "setup"}],
        "methods": [{"id": "smith_capacity"}],
        "seeds": {"start": 0, "count": 3},
        "validation_seeds": {"start": 1000, "count": 2},
        "tuning": {
            "output_artifact": str(artifact),
            "method_param_grid": {
                "smith_capacity": {
                    "default": [
                        {"distance_weight": 0.18, "deficit_weight": 1.45, "reward_weight": 1.0, "capacity_weight": 1.2, "completion_weight": 0.0, "exponent": 1.15},
                        {"distance_weight": 0.08, "deficit_weight": 1.55, "reward_weight": 1.35, "capacity_weight": 1.45, "completion_weight": 2.0, "exponent": 1.0},
                    ]
                }
            },
        },
    }
    config_path = tmp_path / "tune.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest = run_sp2_config(config_path)
    tuned = yaml.safe_load(artifact.read_text(encoding="utf-8"))
    validation_scores = (tmp_path / "tuning" / "validation_scores.csv").read_text(encoding="utf-8")

    assert manifest["seed_count"] == 3
    assert manifest["validation_seed_count"] == 2
    assert "smith_capacity" in tuned["best_params"]
    assert tuned["best_params"]["smith_capacity"]["selection_split"] == "validation"
    assert "selection_split" in validation_scores
    assert "validation_score" in validation_scores

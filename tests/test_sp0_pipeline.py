"""SP0 homogeneous one-to-one assignment pipeline tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import yaml

from viu_mrob_tfm.sp0.methods import assignment_valid, run_sp0_method
from viu_mrob_tfm.sp0.runner import run_sp0_config
from viu_mrob_tfm.sp0.scenario import make_sp0_world


def test_sp0_world_has_valid_oracle_and_simplex_initialization() -> None:
    world = make_sp0_world(n_robots=6, n_loads=9, seed=123, geometry_id="G-UNI", mean_degree_target=4)

    assert world.cost.shape == (6, 9)
    assert world.initial_x.shape == (6, 10)
    assert np.allclose(np.sum(world.initial_x, axis=1), 1.0)
    assert assignment_valid(world.oracle_labels, world.n_loads)
    assert int(np.sum(world.oracle_labels > 0)) == world.s_star
    assert world.oracle_j <= world.s_star
    assert world.world_hash


def test_sp0_population_method_returns_valid_qr_assignment() -> None:
    world = make_sp0_world(n_robots=8, n_loads=8, seed=321, geometry_id="G-X", mean_degree_target="all")
    result = run_sp0_method(
        world,
        {
            "id": "SMI",
            "fitness_id": "ASYM",
            "rounding_id": "QR2",
            "h": 0.05,
            "max_steps": 40,
            "stable_window_steps": 3,
        },
    )

    assert result.continuous_x is not None
    assert np.allclose(np.sum(result.continuous_x, axis=1), 1.0)
    assert assignment_valid(result.labels, world.n_loads)


def test_sp0_debug_config_writes_outputs() -> None:
    output_dir = Path("output/test_sp0_debug")
    config = {
        "sp_id": "SP0-v1.0",
        "experiment_id": "SP0_TEST_smoke",
        "mode": "debug",
        "output_dir": str(output_dir),
        "seeds": {"start": 10, "count": 1},
        "worlds": [
            {
                "block": "debug",
                "geometries": ["G-UNI"],
                "N": [5],
                "load_ratios": [1.0, 1.5],
                "mean_degrees": ["all"],
            }
        ],
        "methods": [
            {"id": "HUN"},
            {"id": "GRD"},
            {"id": "DA"},
            {"id": "REP", "fitness_id": "LIN", "rounding_id": "QR1", "max_steps": 20, "stable_window_steps": 2},
        ],
        "make_figures": True,
    }
    config_path = Path("output/test_sp0_debug_config.yaml")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")

    manifest = run_sp0_config(config_path)

    assert manifest["experiment_id"] == "SP0_TEST_smoke"
    assert manifest["runs"] == 8
    assert (output_dir / "tables" / "runs.csv").exists()
    assert (output_dir / "tables" / "summary.csv").exists()
    assert (output_dir / "tables" / "theory_checks.csv").exists()
    assert (output_dir / "figures" / "sp0_method_quality.png").exists()
    assert (output_dir / "report.md").exists()


def test_sp0_b0_reduced_gate_passes() -> None:
    output_dir = Path("output/test_sp0_b0")
    config = {
        "sp_id": "SP0-v1.0",
        "experiment_id": "SP0_TEST_B0",
        "mode": "b0",
        "output_dir": str(output_dir),
        "b0_runs": 12,
    }
    config_path = Path("output/test_sp0_b0_config.yaml")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")

    manifest = run_sp0_config(config_path)

    assert manifest["runs"] == 12
    assert manifest["passed"] is True
    assert (output_dir / "tables" / "b0_checks.csv").exists()
    assert (output_dir / "theory_audit.json").exists()


def test_sp0_protocol_manifest_records_open_freeze_decisions() -> None:
    output_dir = Path("output/test_sp0_protocol")
    config = {
        "sp_id": "SP0-v1.0",
        "experiment_id": "SP0_TEST_PROTOCOL",
        "mode": "protocol",
        "output_dir": str(output_dir),
        "frozen": False,
        "expected_full_campaign_evaluations": 15436,
        "campaign_counts": {"B0": 300, "B2": 2400, "B3": 1536, "B4": 5760, "B5": 4000, "B6": 960, "B7": 480},
        "implementation_decisions": {
            "exp4_population_finalists": 5,
            "data_driven_champion_rule": "validation_between_IPPO_GNN_and_MAPPO_GNN",
        },
    }
    config_path = Path("output/test_sp0_protocol_config.yaml")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")

    manifest = run_sp0_config(config_path)

    assert manifest["expected_full_campaign_evaluations"] == 15436
    assert manifest["implementation_decisions"]["exp4_population_finalists"] == 5
    assert manifest["implementation_decisions"]["data_driven_champion_rule"] == "validation_between_IPPO_GNN_and_MAPPO_GNN"


def test_non_oracle_methods_do_not_access_oracle() -> None:
    from viu_mrob_tfm.sp0.audit import OracleBlockedWorld

    world = make_sp0_world(n_robots=5, n_loads=5, seed=4242, geometry_id="G-X", mean_degree_target="all")
    blocked = OracleBlockedWorld(world, [])
    specs = [
        {"id": "GRD"},
        {"id": "DA"},
        {"id": "REP", "fitness_id": "LIN", "rounding_id": "QR1", "max_steps": 8},
        {"id": "SMI", "fitness_id": "ASYM", "rounding_id": "QRA", "max_steps": 8},
        {"id": "HYB", "fitness_id": "ASYM", "rounding_id": "QR2", "max_steps": 8},
    ]
    for spec in specs:
        result = run_sp0_method(blocked, spec)
        assert assignment_valid(result.labels, world.n_loads)



def test_sp0_campaign_planned_counts_are_preregistered() -> None:
    from viu_mrob_tfm.sp0.campaign import planned_counts

    assert planned_counts() == {
        "B0": 300,
        "B2": 2400,
        "B3": 1536,
        "B4": 5760,
        "B5": 4000,
        "B6": 960,
        "B7": 480,
        "TOTAL": 15436,
    }


def test_sp0_data_driven_champion_validation_rejects_incomplete_artifacts() -> None:
    from viu_mrob_tfm.sp0.campaign import validate_data_driven_champion

    errors = validate_data_driven_champion({"champion_id": "MAPPO-GNN", "final_seeds": [{"train_seed": 1}]})

    assert errors
    assert any("exactly 3" in error or "fewer than" in error for error in errors)


def test_sp0_data_driven_proxy_execution_is_forbidden() -> None:
    from viu_mrob_tfm.sp0.campaign import run_data_driven_checkpoint

    world = make_sp0_world(n_robots=3, n_loads=3, seed=5151, geometry_id="G-UNI", mean_degree_target="all")

    try:
        run_data_driven_checkpoint(world, {"id": "MAPPO-GNN"})
    except RuntimeError as exc:
        assert "real checkpoint" in str(exc)
    else:
        raise AssertionError("proxy data-driven execution was not blocked")

def test_sp0_data_driven_run_sp0_method_requires_checkpoint() -> None:
    world = make_sp0_world(n_robots=3, n_loads=3, seed=6161, geometry_id="G-UNI", mean_degree_target="all")

    try:
        run_sp0_method(world, {"id": "IPPO-GNN"})
    except RuntimeError as exc:
        assert "real checkpoint" in str(exc)
    else:
        raise AssertionError("IPPO-GNN ran without a real checkpoint")


def test_sp0_data_driven_checkpoint_executor_is_oracle_free() -> None:
    import torch
    from viu_mrob_tfm.sp0.audit import OracleBlockedWorld
    from viu_mrob_tfm.sp0.data_driven import SP0GNNActorCritic, build_policy_batch, run_checkpoint_policy

    world = make_sp0_world(n_robots=4, n_loads=4, seed=6262, geometry_id="G-X", mean_degree_target="all")
    access_log: list[str] = []
    blocked = OracleBlockedWorld(world, access_log)
    model = SP0GNNActorCritic(hidden_dim=16, critic_global=False)
    checkpoint_dir = Path("results/sp0/test_artifacts/sp0_dd_checkpoint_executor")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = checkpoint_dir / "checkpoint.pt"
    torch.save(
        {
            "algorithm": "IPPO-GNN",
            "hidden_dim": 16,
            "train_seed": 15001,
            "training_steps": 5_000_000,
            "training_converged": False,
            "model_state_dict": model.state_dict(),
        },
        checkpoint,
    )

    _ = build_policy_batch(blocked)
    result = run_checkpoint_policy(blocked, {"id": "IPPO-GNN", "checkpoint_path": str(checkpoint), "training_steps": 5_000_000, "train_seed": 15001})

    assert access_log == []
    assert assignment_valid(result.labels, world.n_loads)
    assert result.training_steps == 5_000_000
    assert result.method_family == "data_driven"

def test_sp0_world_public_view_excludes_oracle_and_is_read_only() -> None:
    from viu_mrob_tfm.sp0.scenario import WorldPublicView, public_world_view

    world = make_sp0_world(n_robots=4, n_loads=5, seed=6363, geometry_id="G-UNI", mean_degree_target=3)
    public = public_world_view(world)

    assert isinstance(public, WorldPublicView)
    assert not hasattr(public, "oracle_labels")
    assert not hasattr(public, "oracle_social_cost")
    assert not hasattr(public, "oracle_j")
    assert public.world_hash == world.world_hash
    assert public.cost.flags.writeable is False
    try:
        public.cost[0, 0] = 0.0
    except ValueError:
        pass
    else:
        raise AssertionError("public world arrays must be read-only")


def test_sp0_campaign_dispatches_only_hun_with_oracle_view(monkeypatch) -> None:
    import viu_mrob_tfm.sp0.campaign as campaign
    from viu_mrob_tfm.sp0.scenario import SP0World, WorldPublicView

    world = make_sp0_world(n_robots=4, n_loads=4, seed=6464, geometry_id="G-X", mean_degree_target="all")
    seen: dict[str, object] = {}
    real_run = campaign.run_sp0_method

    def capture(method_world, spec):
        seen[str(spec["id"])] = method_world
        return real_run(method_world, spec)

    monkeypatch.setattr(campaign, "run_sp0_method", capture)
    common = ("test", "B0", "config", "git", "2026-01-01T00:00:00+00:00")
    campaign.run_row(world, {"id": "GRD"}, *common)
    campaign.run_row(world, {"id": "HUN"}, *common)

    assert isinstance(seen["GRD"], WorldPublicView)
    assert isinstance(seen["HUN"], SP0World)


def test_sp0_b1_cache_separates_and_hashes_public_oracle_namespaces() -> None:
    from viu_mrob_tfm.sp0.campaign import run_b1_world_cache, validate_b1_cache

    root = Path("output/test_sp0_b1_cache")
    status = run_b1_world_cache({"sp_id": "SP0-v1.1"}, root, resume=False)
    catalog = root / "worlds" / "world_catalog.parquet"
    manifest = root / "worlds" / "cache_manifest.json"

    assert status["worlds"] == 60
    assert status["cache_validated"] is True
    assert validate_b1_cache(catalog, manifest, expected_worlds=60) == []
    assert (root / "worlds" / "public").is_dir()
    assert (root / "worlds" / "oracle").is_dir()
    public_path = next((root / "worlds" / "public").glob("*.npz"))
    with np.load(public_path, allow_pickle=False) as data:
        assert not {"oracle_assignment", "oracle_cost", "oracle_j"}.intersection(data.files)

def test_sp0_raw_reports_continuous_metrics_without_discrete_success() -> None:
    from viu_mrob_tfm.sp0.metrics import evaluate_sp0_result

    world = make_sp0_world(n_robots=6, n_loads=6, seed=6565, geometry_id="G-UNI", mean_degree_target="all")
    result = run_sp0_method(
        world,
        {"id": "SMI", "fitness_id": "ASYM", "rounding_id": "RAW", "max_steps": 10},
    )
    metrics = evaluate_sp0_result(world, result)

    assert result.closure_applied is False
    assert np.all(result.labels == -1)
    assert metrics.matching_valid is None
    assert metrics.maximum_cardinality is None
    assert metrics.final_success is None
    assert metrics.success is None
    assert np.isfinite(metrics.continuous_objective)
    assert np.isfinite(metrics.continuous_normalized_regret)
    assert metrics.normalized_regret == metrics.continuous_normalized_regret

def test_sp0_gnn_actor_is_local_on_disconnected_graph() -> None:
    import torch
    from dataclasses import replace
    from viu_mrob_tfm.sp0.data_driven import SP0GNNActorCritic, build_policy_batch
    from viu_mrob_tfm.sp0.scenario import public_world_view

    torch.manual_seed(7)
    world = make_sp0_world(n_robots=4, n_loads=4, seed=6666, geometry_id="G-UNI", mean_degree_target=0)
    public = public_world_view(world)
    modified_cost = np.asarray(public.cost).copy()
    modified_cost[1:, :] = np.flip(modified_cost[1:, :], axis=1)
    modified = replace(public, cost=modified_cost)
    model = SP0GNNActorCritic(hidden_dim=16, critic_global=True, gnn_layers=2)
    model.eval()
    with torch.no_grad():
        logits_a = model.actor_logits(build_policy_batch(public))
        logits_b = model.actor_logits(build_policy_batch(modified))

    assert np.all(public.adjacency == 0)
    assert torch.allclose(logits_a[0], logits_b[0], atol=1.0e-7)


def test_sp0_mappo_inference_does_not_execute_global_critic(monkeypatch) -> None:
    from viu_mrob_tfm.sp0.data_driven import SP0GNNActorCritic, deterministic_policy_rollout
    from viu_mrob_tfm.sp0.scenario import public_world_view

    world = make_sp0_world(n_robots=4, n_loads=5, seed=6767, geometry_id="G-UNI", mean_degree_target=2)
    model = SP0GNNActorCritic(hidden_dim=16, critic_global=True, gnn_layers=2)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("centralized critic executed during inference")

    monkeypatch.setattr(model.global_value, "forward", forbidden)
    raw, labels, iterations, _closure_s = deterministic_policy_rollout(
        model,
        public_world_view(world),
        horizon=2,
    )

    assert raw.shape == (4,)
    assert assignment_valid(labels, 5)
    assert iterations >= 1


def test_sp0_data_driven_reward_has_no_oracle_access() -> None:
    from viu_mrob_tfm.sp0.audit import OracleBlockedWorld
    from viu_mrob_tfm.sp0.data_driven import assignment_reward

    world = make_sp0_world(n_robots=4, n_loads=4, seed=6868, geometry_id="G-X", mean_degree_target="all")
    access_log: list[str] = []
    public = OracleBlockedWorld(world, access_log)
    reward = assignment_reward(public, np.array([1, 1, 0, 2]), np.zeros(4, dtype=int), terminal=True)

    assert np.isfinite(reward)
    assert access_log == []


def test_sp0_data_driven_masks_support_variable_N_K() -> None:
    from viu_mrob_tfm.sp0.data_driven import SP0GNNActorCritic, build_policy_batch
    from viu_mrob_tfm.sp0.scenario import public_world_view

    model = SP0GNNActorCritic(hidden_dim=16, critic_global=False, gnn_layers=3)
    for n, k in [(8, 12), (24, 24), (48, 48), (64, 43)]:
        world = make_sp0_world(n_robots=n, n_loads=k, seed=6900 + n + k, geometry_id="G-UNI", mean_degree_target=4)
        batch = build_policy_batch(public_world_view(world))
        logits, values = model(batch)
        assert logits.shape == (n, k + 1)
        assert values.shape == (n,)
        assert batch.action_mask.shape == (n, k + 1)
        assert bool(batch.action_mask.all())


def test_sp0_ppo_training_counts_exact_steps_and_writes_real_checkpoint() -> None:
    from viu_mrob_tfm.sp0.data_driven import train_one_seed

    output_dir = Path("output/test_sp0_ppo_training")
    metadata = train_one_seed(
        algorithm="IPPO-GNN",
        output_dir=output_dir,
        train_seed=6971,
        total_steps=128,
        hidden_dim=16,
        learning_rate=3.0e-4,
        device="cpu",
        eval_interval=42,
        gnn_layers=2,
        ppo_clip=0.2,
        entropy_coefficient=0.01,
        discount_factor=0.99,
        ppo_epochs=1,
        rollout_environment_steps=16,
        episode_horizon=2,
    )

    assert metadata["training_steps"] == 128
    assert metadata["training_step_unit"] == "joint_environment_transition"
    assert metadata["optimizer_updates"] > 0
    assert metadata["checkpoint_hash"]
    assert Path(metadata["checkpoint_path"]).exists()
    assert len(metadata["history"]) >= 3
    progress = Path(metadata["progress_checkpoint_path"])
    assert progress.exists()
    Path(metadata["checkpoint_path"]).unlink()
    resumed = train_one_seed(
        algorithm="IPPO-GNN",
        output_dir=output_dir,
        train_seed=6971,
        total_steps=128,
        hidden_dim=16,
        learning_rate=3.0e-4,
        device="cpu",
        eval_interval=42,
        gnn_layers=2,
        ppo_clip=0.2,
        entropy_coefficient=0.01,
        discount_factor=0.99,
        ppo_epochs=1,
        rollout_environment_steps=16,
        episode_horizon=2,
    )
    assert resumed["resumed_from_step"] == 128
    assert Path(resumed["checkpoint_path"]).exists()

def test_sp0_epsilon_auction_is_valid_for_rectangular_regimes() -> None:
    for n, k in [(4, 7), (6, 6), (8, 5)]:
        world = make_sp0_world(n_robots=n, n_loads=k, seed=7100 + n + k, geometry_id="G-TIE", mean_degree_target="all")
        result = run_sp0_method(world, {"id": "DA", "auction_epsilon": 1.0e-3})

        assert result.method_id == "EPS-AUCTION"
        assert assignment_valid(result.labels, k)
        assert int(np.sum(result.labels > 0)) == min(n, k)
        assert result.final_success is True


def test_sp0_local_baselines_do_not_hide_disconnected_conflicts() -> None:
    world = make_sp0_world(
        n_robots=3,
        n_loads=3,
        seed=7201,
        geometry_id="G-UNI",
        mean_degree_target="all",
    )
    disconnected = replace(
        world,
        cost=np.asarray(
            [
                [0.01, 0.80, 0.90],
                [0.02, 0.81, 0.91],
                [0.03, 0.82, 0.92],
            ],
            dtype=float,
        ),
        adjacency=np.zeros((3, 3), dtype=np.int8),
        mean_degree=0.0,
        min_degree=0,
        lambda2=0.0,
        num_components=3,
        diameter=float("inf"),
    )

    greedy = run_sp0_method(disconnected, {"id": "GRD", "architecture": "distributed_local"})
    auction = run_sp0_method(disconnected, {"id": "DA", "architecture": "distributed_local"})

    assert assignment_valid(greedy.labels, disconnected.n_loads) is False
    assert assignment_valid(auction.labels, disconnected.n_loads) is False
    assert len(set(greedy.labels.tolist())) == 1
    assert len(set(auction.labels.tolist())) == 1


def test_sp0_global_baselines_remain_valid_on_same_cost_matrix() -> None:
    world = make_sp0_world(
        n_robots=3,
        n_loads=3,
        seed=7202,
        geometry_id="G-UNI",
        mean_degree_target="all",
    )
    same_preference = replace(
        world,
        cost=np.asarray(
            [
                [0.01, 0.80, 0.90],
                [0.02, 0.81, 0.91],
                [0.03, 0.82, 0.92],
            ],
            dtype=float,
        ),
    )

    for method_id in ("GRD", "DA"):
        result = run_sp0_method(same_preference, {"id": method_id, "architecture": "distributed_global"})
        assert assignment_valid(result.labels, same_preference.n_loads) is True
        assert result.maximum_cardinality is True
        assert result.final_success is True

def test_sp0_parquet_preserves_nullable_boolean_types() -> None:
    import pandas as pd

    from viu_mrob_tfm.sp0.campaign import write_parquet

    target = Path("output/test_sp0_nullable.parquet")
    write_parquet(
        target,
        [
            {"final_success": True, "continuous_timeout": False, "value": 1.0},
            {"final_success": False, "continuous_timeout": True, "value": 2.0},
            {"final_success": None, "continuous_timeout": None, "value": None},
        ],
    )
    restored = pd.read_parquet(target)

    assert restored["final_success"].dropna().map(type).eq(bool).all()
    assert restored["continuous_timeout"].dropna().map(type).eq(bool).all()
    assert restored["value"].dropna().map(type).isin([float, int]).all()

def test_sp0_cpu_preflight_blocks_without_reducing_budget() -> None:
    import json

    from viu_mrob_tfm.sp0.audit import hardware_info
    from viu_mrob_tfm.sp0.data_driven import (
        POLICY_VERSION,
        cpu_hardware_block_status,
        expected_training_environment_steps,
    )

    config = {
        "data_driven_training": {
            "algorithms": ["IPPO-GNN", "MAPPO-GNN"],
            "DD_1": {
                "configurations_per_algorithm": 6,
                "train_seeds_per_configuration": 1,
                "environment_steps": 250_000,
            },
            "DD_2": {
                "retained_configurations_per_algorithm": 2,
                "train_seeds_per_configuration": 2,
                "environment_steps": 1_000_000,
            },
            "final": {
                "independent_train_seeds": 3,
                "environment_steps_per_seed": 5_000_000,
            },
            "hardware_preflight": {
                "benchmark_environment_steps": 10_000,
                "maximum_estimated_training_wall_hours": 24,
            },
        }
    }
    root = Path("output/test_sp0_cpu_preflight")
    benchmark_path = root / "training/hardware_benchmark.json"
    benchmark_path.parent.mkdir(parents=True, exist_ok=True)
    benchmark_path.write_text(
        json.dumps(
            {
                "policy_version": POLICY_VERSION,
                "training_step_unit": "joint_environment_transition",
                "benchmark_steps": 10_000,
                "ppo_epochs": 4,
                "rollout_environment_steps": 128,
                "episode_horizon": 4,
                "measured_environment_steps_per_s": 63.0,
                "expected_full_training_environment_steps": 26_000_000,
                "estimated_training_wall_hours_lower_bound": 26_000_000 / 63.0 / 3600.0,
                "hardware": hardware_info(),
                "benchmark_checkpoint_sha256": "test-only-hash",
            }
        ),
        encoding="utf-8",
    )

    assert expected_training_environment_steps(config) == 26_000_000
    blocked = cpu_hardware_block_status(config, root, allow_long_cpu_training=False)
    assert blocked is not None
    assert blocked["status"] == "HARDWARE_BLOCKED"
    assert blocked["budget_reduced"] is False
    assert blocked["confirmatory_seeds_opened"] is False
    assert cpu_hardware_block_status(config, root, allow_long_cpu_training=True) is None


def test_sp0_cpu_protocol_training_budget_formula_is_preregistered() -> None:
    from viu_mrob_tfm.sp0.data_driven import expected_training_environment_steps

    config = yaml.safe_load(
        Path("configs/experiments/sp0/SP0_PROTOCOL_v1_2_CPU.yaml").read_text(encoding="utf-8")
    )

    assert expected_training_environment_steps(config) == 1_120_000
    assert config["data_driven_training"]["expected_total_environment_steps"] == 1_120_000
    assert config["data_driven_training"]["ppo_epochs"] == 1
    assert config["data_driven_training"]["rollout_environment_steps"] == 512
    assert config["revision"]["created_before_confirmatory_seed_opening"] is True

def test_sp0_parallel_task_execution_preserves_order_and_results() -> None:
    import os

    from viu_mrob_tfm.sp0.campaign import execute_run_tasks

    worlds = [
        make_sp0_world(
            n_robots=4,
            n_loads=4,
            seed=7300 + index,
            geometry_id="G-UNI",
            mean_degree_target="all",
        )
        for index in range(6)
    ]
    tasks = [
        (
            world,
            {"id": "GRD"},
            "SP0_parallel_test",
            "DRY_TEST",
            "config-test",
            "git-test",
            "2026-07-11T00:00:00+00:00",
            {"task_index": index},
        )
        for index, world in enumerate(worlds)
    ]
    previous = os.environ.get("SP0_WORKERS")
    try:
        os.environ["SP0_WORKERS"] = "1"
        sequential = execute_run_tasks(tasks)
        os.environ["SP0_WORKERS"] = "4"
        parallel = execute_run_tasks(tasks)
    finally:
        if previous is None:
            os.environ.pop("SP0_WORKERS", None)
        else:
            os.environ["SP0_WORKERS"] = previous

    assert [row["task_index"] for row in parallel] == list(range(6))
    for left, right in zip(sequential, parallel):
        assert left["world_hash"] == right["world_hash"]
        assert left["method_variant"] == right["method_variant"]
        assert left["matching_valid"] == right["matching_valid"]
        assert left["final_success"] == right["final_success"]
        assert left["social_cost"] == right["social_cost"]
        assert left["normalized_regret"] == right["normalized_regret"]

def test_sp0_resumable_tasks_reuse_checkpoint_without_reexecution(monkeypatch) -> None:
    import viu_mrob_tfm.sp0.campaign as campaign

    worlds = [
        make_sp0_world(
            n_robots=3,
            n_loads=3,
            seed=7400 + index,
            geometry_id="G-UNI",
            mean_degree_target="all",
        )
        for index in range(3)
    ]
    tasks = [
        (
            world,
            {"id": "GRD"},
            "SP0_resume_test",
            "DRY_TEST",
            "config-resume-v1",
            "git-test",
            "2026-07-11T00:00:00+00:00",
            {"task_index": index},
        )
        for index, world in enumerate(worlds)
    ]
    checkpoint = Path("output/test_sp0_resume/checkpoint.parquet")
    first = campaign.execute_run_tasks_resumable(tasks, checkpoint, resume=False)

    def forbidden(_task):
        raise AssertionError("completed task was executed again")

    monkeypatch.setattr(campaign, "_execute_run_task", forbidden)
    second = campaign.execute_run_tasks_resumable(tasks, checkpoint, resume=True)

    assert len(first) == len(second) == 3
    assert [row["task_index"] for row in second] == [0, 1, 2]
    assert len({row["task_token"] for row in second}) == 3
    assert [row["world_hash"] for row in first] == [row["world_hash"] for row in second]

def test_sp0_confirmatory_seed_registry_requires_immutable_opening_event() -> None:
    import json

    import pytest
    import yaml

    from viu_mrob_tfm.sp0.audit import validate_confirmatory_seed_opening

    from viu_mrob_tfm.sp0.campaign import (
        default_seed_registry,
        load_frozen_seed_registry,
        record_confirmatory_seed_opening,
        sha256_file,
    )

    root = Path("output/test_sp0_seed_opening")
    protocol = root / "protocol"
    b3 = root / "b3"
    training = root / "training"
    protocol.mkdir(parents=True, exist_ok=True)
    b3.mkdir(parents=True, exist_ok=True)
    training.mkdir(parents=True, exist_ok=True)
    event_path = protocol / "confirmatory_seed_opening.json"
    event_path.unlink(missing_ok=True)
    event_path.with_suffix(".sha256").unlink(missing_ok=True)
    seed_path = protocol / "seed_registry_v1_1.yaml"
    seed_path.write_text(yaml.safe_dump(default_seed_registry(), sort_keys=True), encoding="utf-8")
    frozen_path = protocol / "frozen_manifest_v1_1.json"
    frozen_path.write_text(
        json.dumps(
            {
                "frozen": True,
                "status": "frozen_ready_for_execution",
                "artifact_names": {"seeds": seed_path.name},
                "frozen_at_utc": "2026-07-11T00:00:00+00:00",
                "seed_registry_sha256": sha256_file(seed_path),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    champions = b3 / "champions.yaml"
    champions.write_text("REP: {config_id: REP_00}\n", encoding="utf-8")
    dd_champion = training / "champion.yaml"
    dd_champion.write_text("champion_id: MAPPO-GNN\n", encoding="utf-8")
    model_selection = b3 / "model_selection_champions.yaml"
    model_selection.write_text("B5_top5_local_population: []\n", encoding="utf-8")

    preconfirmatory = load_frozen_seed_registry(root)
    assert "screening_seeds" in preconfirmatory
    assert "validation_seeds" in preconfirmatory
    assert "test_seeds_1_40" not in preconfirmatory
    assert "generalization_seeds" not in preconfirmatory
    with pytest.raises(RuntimeError, match="sealed"):
        load_frozen_seed_registry(root, allow_confirmatory=True)

    event = record_confirmatory_seed_opening(
        root,
        {"champion_sha256": sha256_file(dd_champion)},
        {"selection_sha256": sha256_file(model_selection)},
    )
    opened = load_frozen_seed_registry(root, allow_confirmatory=True)
    assert opened["test_seeds_1_40"] == list(range(13000, 13040))
    assert event["event_sha256"] == sha256_file(event_path)
    assert validate_confirmatory_seed_opening(root) == []
    repeated = record_confirmatory_seed_opening(
        root,
        {"champion_sha256": sha256_file(dd_champion)},
        {"selection_sha256": sha256_file(model_selection)},
    )
    assert repeated["opened_at_utc"] == event["opened_at_utc"]
    with pytest.raises(RuntimeError, match="mismatch"):
        record_confirmatory_seed_opening(
            root,
            {"champion_sha256": "different-dd-hash"},
            {"selection_sha256": sha256_file(model_selection)},
        )

def test_sp0_time_to_epsilon_uses_first_useful_trajectory_state() -> None:
    from viu_mrob_tfm.sp0.metrics import evaluate_sp0_result

    world = make_sp0_world(
        n_robots=4,
        n_loads=4,
        seed=7501,
        geometry_id="G-UNI",
        mean_degree_target="all",
    )
    base = run_sp0_method(world, {"id": "HUN"})
    result = replace(
        base,
        iterations=4,
        messages=100,
        bytes_sent=3200,
        closure_messages=10,
        simulation_end_time_s=0.4,
        trajectory={
            "time_s": np.asarray([0.1, 0.2], dtype=float),
            "argmax_labels": np.stack(
                [np.zeros(world.n_robots, dtype=int), world.oracle_labels],
                axis=0,
            ),
        },
    )
    metrics = evaluate_sp0_result(world, result)

    assert metrics.time_to_epsilon_observed is True
    assert metrics.time_to_epsilon_solution == 0.2
    assert metrics.time_to_epsilon_duration_s == 0.2
    assert metrics.messages_to_epsilon_solution == 45.0
    assert metrics.bytes_to_epsilon_solution == 1440.0


def test_sp0_time_to_epsilon_preserves_censoring_for_invalid_local_result() -> None:
    from viu_mrob_tfm.sp0.metrics import evaluate_sp0_result

    world = make_sp0_world(
        n_robots=3,
        n_loads=3,
        seed=7502,
        geometry_id="G-UNI",
        mean_degree_target=0,
    )
    result = run_sp0_method(world, {"id": "GRD", "architecture": "distributed_local"})
    metrics = evaluate_sp0_result(world, result)

    if not assignment_valid(result.labels, world.n_loads):
        assert metrics.time_to_epsilon_observed is False
        assert np.isnan(metrics.time_to_epsilon_solution)
        assert np.isnan(metrics.messages_to_epsilon_solution)
        assert metrics.time_to_epsilon_duration_s > 0.0

def test_sp0_training_frame_does_not_mix_dry_run_with_official_metadata() -> None:
    import json

    from viu_mrob_tfm.sp0.postprocess import training_frame

    root = Path("output/test_sp0_training_frame")
    official = root / "training" / "IPPO_GNN" / "DD1" / "run"
    dry = root / "training" / "dry_run" / "IPPO_GNN" / "DD1" / "run"
    official.mkdir(parents=True, exist_ok=True)
    dry.mkdir(parents=True, exist_ok=True)
    payload = lambda algorithm, seed, nr: {
        "algorithm": algorithm,
        "train_seed": seed,
        "history": [{"training_steps": 10, "validation": {"mean_NR": nr, "success": 1.0}}],
    }
    (official / "metadata.json").write_text(json.dumps(payload("IPPO-GNN", 1, 0.1)), encoding="utf-8")
    (dry / "metadata.json").write_text(json.dumps(payload("MAPPO-GNN", 2, 0.9)), encoding="utf-8")

    frame = training_frame(root)

    assert frame["algorithm"].tolist() == ["IPPO-GNN"]
    assert frame["artifact_scope"].tolist() == ["official"]


def test_sp0_trajectory_overlay_metrics_penalize_duplicate_assignments() -> None:
    from viu_mrob_tfm.sp0.postprocess import trajectory_assignment_metrics, trajectory_messages_at_frame

    trajectory = {
        "cost_matrix": np.asarray([[0.1, 0.8], [0.2, 0.3]]),
        "s_star": np.asarray(2),
        "oracle_j_posthoc": np.asarray(0.4),
        "messages_total": np.asarray(30),
        "closure_messages": np.asarray(10),
        "iterations": np.asarray(2),
        "render_final_appended": np.asarray(1),
    }
    coverage, regret = trajectory_assignment_metrics(trajectory, np.asarray([1, 1]))

    assert coverage == 0.5
    assert regret > 0.0
    assert trajectory_messages_at_frame(trajectory, 0, 3) == 10
    assert trajectory_messages_at_frame(trajectory, 2, 3) == 30

def test_sp0_closure_regret_deltas_have_explicit_baselines() -> None:
    from viu_mrob_tfm.sp0.metrics import evaluate_sp0_result

    world = make_sp0_world(n_robots=6, n_loads=6, seed=7601, geometry_id="G-X", mean_degree_target="all")
    result = run_sp0_method(
        world,
        {"id": "HYB", "fitness_id": "ASYM", "rounding_id": "QR2", "max_steps": 20},
    )
    metrics = evaluate_sp0_result(world, result)

    assert metrics.closure_vs_preclosure_regret_delta == metrics.closure_regret_delta
    assert np.isclose(
        metrics.closure_vs_preclosure_regret_delta,
        metrics.normalized_regret - metrics.preclosure_normalized_regret,
    )
    assert np.isclose(
        metrics.final_vs_continuous_regret_delta,
        metrics.normalized_regret - metrics.continuous_normalized_regret,
    )

def test_sp0_legacy_training_metrics_are_migrated_without_changing_values() -> None:
    from viu_mrob_tfm.sp0.data_driven import upgrade_validation_metric_names

    history = [{"validation": {"mean_NR": 0.02, "mean_closure_NR_delta": -1.5}}]

    assert upgrade_validation_metric_names(history) is True
    validation = history[0]["validation"]
    assert validation["mean_closure_vs_raw_decode_NR_delta"] == -1.5
    assert np.isclose(validation["mean_raw_decode_NR"], 1.52)
    assert upgrade_validation_metric_names(history) is False


def test_sp0_batched_policy_matches_individual_forward_passes() -> None:
    import torch

    from viu_mrob_tfm.sp0.data_driven import (
        SP0GNNActorCritic,
        build_policy_batch,
        stack_policy_batches,
    )
    from viu_mrob_tfm.sp0.scenario import public_world_view

    worlds = [
        public_world_view(make_sp0_world(
            n_robots=8,
            n_loads=8,
            seed=seed,
            geometry_id="G-UNI",
            mean_degree_target=4,
        ))
        for seed in [7701, 7702]
    ]
    batches = [build_policy_batch(world) for world in worlds]
    stacked = stack_policy_batches(batches)

    for critic_global in [False, True]:
        torch.manual_seed(17)
        model = SP0GNNActorCritic(hidden_dim=16, critic_global=critic_global, gnn_layers=2)
        model.eval()
        with torch.no_grad():
            individual = [model(batch) for batch in batches]
            batched_logits, batched_values = model(stacked)

        assert torch.allclose(batched_logits, torch.stack([item[0] for item in individual]), atol=1e-6)
        assert torch.allclose(batched_values, torch.stack([item[1] for item in individual]), atol=1e-6)


def test_non_oracle_method_has_no_oracle_field() -> None:
    from viu_mrob_tfm.sp0.scenario import public_world_view

    public = public_world_view(
        make_sp0_world(n_robots=4, n_loads=4, seed=91001, geometry_id="G-X", mean_degree_target="all")
    )
    for field in ("oracle_labels", "oracle_social_cost", "oracle_j", "oracle_assignment", "oracle_cost"):
        assert not hasattr(public, field)


def test_non_oracle_method_does_not_call_hungarian() -> None:
    from viu_mrob_tfm.sp0.audit import run_oracle_leakage_checks

    _checks, rows = run_oracle_leakage_checks("config-test", "git-test", "2026-07-11T00:00:00+00:00")
    assert {row["method"] for row in rows} == {
        "GRD", "DA", "REP", "SMI", "BNN", "LOG", "PROJ", "IBR", "GPC", "HYB", "IPPO-GNN", "MAPPO-GNN"
    }
    assert all(row["hungarian_calls"] == 0 for row in rows)
    assert all(row["passed"] for row in rows)


def test_disable_oracle_does_not_change_non_oracle_output() -> None:
    from viu_mrob_tfm.sp0.audit import run_oracle_leakage_checks

    _checks, rows = run_oracle_leakage_checks("config-test", "git-test", "2026-07-11T00:00:00+00:00")
    assert all(row["disable_oracle_same_output"] for row in rows)


def test_no_oracle_in_observation() -> None:
    from viu_mrob_tfm.sp0.audit import OracleBlockedWorld
    from viu_mrob_tfm.sp0.data_driven import build_policy_batch

    world = make_sp0_world(n_robots=5, n_loads=7, seed=91002, geometry_id="G-UNI", mean_degree_target=3)
    access_log: list[str] = []
    batch = build_policy_batch(OracleBlockedWorld(world, access_log))
    assert batch.action_mask.shape == (5, 8)
    assert access_log == []


def test_deterministic_evaluation_reproducible() -> None:
    import torch
    from viu_mrob_tfm.sp0.data_driven import SP0GNNActorCritic, deterministic_policy_rollout
    from viu_mrob_tfm.sp0.scenario import public_world_view

    torch.manual_seed(91003)
    world = public_world_view(
        make_sp0_world(n_robots=8, n_loads=8, seed=91003, geometry_id="G-X", mean_degree_target=4)
    )
    model = SP0GNNActorCritic(hidden_dim=16, critic_global=False, gnn_layers=2)
    first = deterministic_policy_rollout(model, world, horizon=4)
    second = deterministic_policy_rollout(model, world, horizon=4)
    assert np.array_equal(first[0], second[0])
    assert np.array_equal(first[1], second[1])
    assert first[2] == second[2]


def test_sp0_v1_1_budget_guard_rejects_reduced_cpu_protocol() -> None:
    from viu_mrob_tfm.sp0.data_driven import validate_sp0_v1_1_training_budget

    canonical = yaml.safe_load(
        Path("configs/experiments/sp0/SP0_PROTOCOL_v1_1.yaml").read_text(encoding="utf-8")
    )
    reduced = yaml.safe_load(
        Path("configs/experiments/sp0/SP0_PROTOCOL_v1_2_CPU.yaml").read_text(encoding="utf-8")
    )
    assert validate_sp0_v1_1_training_budget(canonical) == []
    errors = validate_sp0_v1_1_training_budget(reduced)
    assert errors
    assert any("final_environment_steps_per_seed=200000" in error for error in errors)


def test_sp0_metrics_export_seconds_only() -> None:
    from viu_mrob_tfm.sp0.metrics import evaluate_sp0_result

    world = make_sp0_world(n_robots=4, n_loads=4, seed=91004, geometry_id="G-UNI", mean_degree_target="all")
    exported = evaluate_sp0_result(world, run_sp0_method(world, {"id": "GRD"})).to_dict()
    assert "runtime_wall_s" in exported
    assert "runtime_cpu_s" in exported
    assert "runtime_wall" not in exported
    assert "runtime_cpu" not in exported
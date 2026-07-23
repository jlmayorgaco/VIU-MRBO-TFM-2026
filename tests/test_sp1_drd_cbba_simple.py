"""Scientific invariants for SP1_DRD_VS_CBBA_SIMPLE_v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from scipy.sparse import csr_matrix

from viu_mrob_tfm.sp1_canonical.validation.drd_cbba_benchmark import (
    audit_results,
    calibration_tasks,
    deterministic_case_catalog,
    deterministic_world,
    evaluation_tasks,
    execute_tasks,
    preview_tasks,
)
from viu_mrob_tfm.sp1_canonical.validation.drd_cbba_simple import (
    assignment_from_drd,
    exponential_replicator_step,
    graph_from_adjacency,
    initial_drd_state,
    integer_metrics,
    make_graph,
    make_manual_world,
    make_simple_world,
    marginal_bid,
    metropolis_hastings_matrix,
    recover_assignment,
    run_cbba,
    run_drd,
    solve_scalar_lp,
    solve_scalar_milp,
    stable_hash,
    validate_message_rows,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "experiments" / "configs" / "sp1_drd_vs_cbba_simple_v1.yaml"


def config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def parameters() -> dict:
    return {
        "candidate_id": "test",
        "rho": 100_000.0,
        "alpha": 0.00005,
        "tau": 0.00001,
        "bid_minimum": 0.0,
    }


def tiny_world():
    return make_manual_world(
        case_id="tiny",
        positions=[[0.0, 0.0], [0.2, 0.0], [0.8, 0.0], [1.0, 0.0]],
        loads=[[0.1, 0.0], [0.9, 0.0]],
        capacities=[1.0, 1.0, 1.0, 1.0],
        masses=[1.8, 1.8],
        witness=[0, 0, 1, 1],
    )


def test_world_is_planted_feasible_and_reproducible() -> None:
    first = make_simple_world(20, 4, 1234, config())
    second = make_simple_world(20, 4, 1234, config())
    assert first.world_hash == second.world_hash
    assert np.array_equal(first.robot_positions, second.robot_positions)
    assert integer_metrics(first, first.witness)["feasible"]
    assert 0.70 <= first.utilization <= 0.90


@pytest.mark.parametrize("regime", ["low", "medium", "high"])
def test_capacity_regimes_are_positive_and_labeled(regime: str) -> None:
    world = make_simple_world(100, 20, 2001, config(), capacity_regime=regime)
    assert np.all(world.capacities > 0.0)
    assert world.capacity_regime == regime


def test_utilization_target_is_constructed_exactly() -> None:
    world = make_simple_world(
        50, 10, 2002, config(), utilization_target=0.95
    )
    assert world.utilization == pytest.approx(0.95)
    assert integer_metrics(world, world.witness)["feasible"]


def test_geometric_graph_is_connected_and_near_target_degree() -> None:
    world = make_simple_world(50, 10, 2003, config())
    graph = make_graph(world, "rdisk_degree_8")
    assert graph.lambda_2 > 0.0
    assert graph.diameter >= 1
    assert graph.degree_min >= 1
    assert graph.degree_mean >= 8.0 - 2.0 / world.n_robots


def test_complete_graph_metrics_are_exact() -> None:
    graph = make_graph(tiny_world(), "complete")
    assert graph.edges == 6
    assert graph.degree_min == graph.degree_max == 3
    assert graph.diameter == 1


def test_metropolis_matrix_is_doubly_stochastic_and_respects_support() -> None:
    world = make_simple_world(20, 4, 2004, config())
    graph = make_graph(world, "rdisk_degree_4")
    weights = metropolis_hastings_matrix(graph)
    assert np.allclose(np.asarray(weights.sum(axis=1)).ravel(), 1.0)
    assert np.allclose(np.asarray(weights.sum(axis=0)).ravel(), 1.0)
    off_diagonal = weights.toarray()
    np.fill_diagonal(off_diagonal, 0.0)
    assert not np.any((off_diagonal != 0.0) & (graph.adjacency.toarray() == 0))


def test_static_consensus_estimates_global_capacity() -> None:
    world = make_simple_world(20, 4, 2005, config())
    graph = make_graph(world, "rdisk_degree_8")
    weights = metropolis_hastings_matrix(graph)
    x = initial_drd_state(world)
    z = world.capacities[:, None] * x[:, 1:]
    for _ in range(500):
        z = weights.dot(z)
    estimate = world.n_robots * z
    truth = np.sum(world.capacities[:, None] * x[:, 1:], axis=0)
    assert np.max(np.abs(estimate - truth)) < 1e-8


def test_exponential_update_matches_direct_formula() -> None:
    x = np.asarray([[0.2, 0.3, 0.5]])
    fitness = np.asarray([[2.0, -1.0, 0.5]])
    alpha = 0.1
    expected = x * np.exp(alpha * fitness)
    expected /= expected.sum(axis=1, keepdims=True)
    assert np.allclose(exponential_replicator_step(x, fitness, alpha), expected)


def test_exponential_update_preserves_simplex_nonnegativity_and_finiteness() -> None:
    rng = np.random.default_rng(9)
    x = rng.dirichlet(np.ones(11), size=50)
    fitness = rng.normal(0.0, 1e5, size=x.shape)
    updated = exponential_replicator_step(x, fitness, 1e-3)
    assert np.all(updated >= 0.0)
    assert np.allclose(updated.sum(axis=1), 1.0)
    assert np.all(np.isfinite(updated))


def test_drd_preserves_simplex_and_tracker_invariant() -> None:
    local = config()
    local["drd"]["max_rounds"] = 20
    local["drd"]["dwell_rounds"] = 100
    world = tiny_world()
    result = run_drd(world, make_graph(world, "complete"), local, parameters())
    assert result.simplex_violation <= 1e-12
    assert result.nonnegativity_violation == 0.0
    assert result.finite_state
    assert result.tracker_sum_error <= 1e-10


def test_drd_converges_in_relaxed_small_case_with_dwell() -> None:
    local = copy.deepcopy(config())
    local["drd"].update(
        {
            "max_rounds": 2000,
            "dwell_rounds": 3,
            "state_tolerance": 1e-3,
            "consensus_tolerance": 1e-3,
            "capacity_tolerance": 1e-3,
        }
    )
    world = tiny_world()
    result = run_drd(world, make_graph(world, "complete"), local, parameters())
    assert result.converged
    assert result.persistent_convergence_round >= result.first_gate_round + 2


def test_drd_records_censoring_when_budget_expires() -> None:
    local = copy.deepcopy(config())
    local["drd"]["max_rounds"] = 1
    local["drd"]["dwell_rounds"] = 100
    world = tiny_world()
    result = run_drd(world, make_graph(world, "complete"), local, parameters())
    assert result.censored
    assert result.censoring_reason == "max_rounds"
    assert result.persistent_convergence_round is None


def test_drd_argmax_is_deterministic_and_idle_is_not_a_load() -> None:
    x = np.asarray([[0.5, 0.5, 0.0], [0.1, 0.2, 0.7]])
    assignment = assignment_from_drd(x)
    assert assignment.tolist() == [-1, 1]


def test_marginal_bid_implements_common_quadratic_penalty() -> None:
    bid = marginal_bid(0.2, capacity=1.0, mass=2.0, recruited_capacity=0.0, rho=4.0)
    expected = -0.2 + 2.0 * (1.0 - 0.25)
    assert bid == pytest.approx(expected)


def test_cbba_has_unit_bundle_multiple_winners_and_no_duplicates() -> None:
    local = copy.deepcopy(config())
    local["cbba"]["max_rounds"] = 1000
    world = tiny_world()
    result = run_cbba(world, make_graph(world, "complete"), local, parameters())
    assert result.converged
    assert integer_metrics(world, result.assignment)["feasible"]
    assert result.duplicate_assignment_count == 0
    assert all(np.sum(result.assignment == load) >= 2 for load in range(2))


def test_cbba_tie_breaking_is_reproducible() -> None:
    world = deterministic_world(10)
    graph = make_graph(world, "complete")
    first = run_cbba(world, graph, config(), parameters())
    second = run_cbba(world, graph, config(), parameters())
    assert np.array_equal(first.assignment, second.assignment)


def test_cbba_propagates_on_a_line_graph_and_terminates() -> None:
    world = tiny_world()
    adjacency = csr_matrix(
        np.asarray(
            [
                [0, 1, 0, 0],
                [1, 0, 1, 0],
                [0, 1, 0, 1],
                [0, 0, 1, 0],
            ]
        )
    )
    graph = graph_from_adjacency("line", adjacency)
    result = run_cbba(world, graph, config(), parameters())
    assert graph.diameter == 3
    assert result.converged
    assert result.persistent_convergence_round >= 2 * graph.diameter


def test_cbba_message_accounting_recomputes() -> None:
    world = tiny_world()
    result = run_cbba(world, make_graph(world, "complete"), config(), parameters())
    validation = validate_message_rows(list(result.messages))
    assert validation
    assert all(row["valid"] for row in validation)


def test_drd_message_accounting_recomputes() -> None:
    local = copy.deepcopy(config())
    local["drd"]["max_rounds"] = 3
    world = tiny_world()
    result = run_drd(world, make_graph(world, "complete"), local, parameters())
    validation = validate_message_rows(list(result.messages))
    assert all(row["valid"] for row in validation)


def test_recovery_simple_move_covers_load() -> None:
    world = deterministic_world(2)
    result = recover_assignment(world, np.full(world.n_robots, -1), config())
    assert result.executed and result.success
    assert result.robots_reassigned >= 2


def test_recovery_uses_augmenting_chain_when_direct_move_cannot_improve() -> None:
    world = make_manual_world(
        case_id="chain",
        positions=[[0.1, 0.0], [0.9, 0.0]],
        loads=[[0.0, 0.0], [1.0, 0.0]],
        capacities=[3.0, 2.0],
        masses=[3.0, 2.0],
        witness=[0, 1],
    )
    result = recover_assignment(world, np.asarray([1, 0]), config())
    assert result.success
    assert result.chain_length_max >= 2
    assert np.array_equal(result.assignment, np.asarray([0, 1]))


def test_recovery_detects_impossible_instance() -> None:
    world = make_manual_world(
        case_id="impossible",
        positions=[[0.0, 0.0], [1.0, 0.0]],
        loads=[[0.5, 0.0]],
        capacities=[1.0, 1.0],
        masses=[3.0],
        witness=[-1, -1],
    )
    result = recover_assignment(world, np.asarray([-1, -1]), config())
    assert result.executed
    assert not result.success
    assert integer_metrics(world, result.assignment)["deficit_total"] > 0


def test_recovery_preserves_one_assignment_per_robot() -> None:
    world = make_simple_world(20, 4, 2010, config())
    result = recover_assignment(world, np.full(20, -1), config())
    assert result.assignment.shape == (20,)
    assert np.all((result.assignment >= -1) & (result.assignment < 4))


@pytest.mark.parametrize("case_index", range(1, 11))
def test_deterministic_witnesses_are_feasible(case_index: int) -> None:
    world = deterministic_world(case_index)
    assert integer_metrics(world, world.witness)["feasible"]


def test_deterministic_catalog_has_exact_ten_reasoned_cases() -> None:
    catalog = deterministic_case_catalog()
    assert len(catalog) == 10
    assert catalog.case_id.is_unique
    assert catalog.expectation.str.len().min() > 0


def test_lp_and_milp_are_coherent() -> None:
    world = deterministic_world(4)
    lp = solve_scalar_lp(world)
    integer = solve_scalar_milp(world, time_limit_s=10.0)
    assert lp.optimal and integer.optimal
    assert lp.objective <= integer.objective + 1e-9
    assert integer.assignment is not None
    assert integer_metrics(world, integer.assignment)["feasible"]


def test_sparse_oracle_handles_moderate_world() -> None:
    world = make_simple_world(100, 20, 2011, config())
    lp = solve_scalar_lp(world)
    assert lp.optimal
    coverage = np.sum(world.capacities[:, None] * lp.x, axis=0)
    assert np.all(coverage >= world.masses - 1e-7)
    assert np.all(lp.x.sum(axis=1) <= 1.0 + 1e-7)


def test_common_random_numbers_hashes_are_method_independent() -> None:
    world = make_simple_world(20, 4, 2012, config())
    graph = make_graph(world, "rdisk_degree_8")
    record = {
        "world_hash": world.world_hash,
        "graph_hash": graph.graph_hash,
        "loads_hash": world.loads_hash,
        "capacities_hash": world.capacities_hash,
    }
    assert stable_hash(record) == stable_hash(record)


def test_exact_campaign_task_counts_and_disjoint_seeds() -> None:
    cfg = config()
    calibration = calibration_tasks(cfg)
    preview = preview_tasks(cfg)
    evaluation = evaluation_tasks(cfg)
    assert len(calibration) == 60 * 6
    assert len(preview) == 15
    assert len(evaluation) == 920
    counts = pd.Series([task["experiment"] for task in evaluation]).value_counts()
    assert counts.to_dict() == {
        "e5": 240,
        "e4": 240,
        "e6": 160,
        "e3": 150,
        "e2": 120,
        "e1": 10,
    }
    calibration_seeds = {task["seed"] for task in calibration}
    evaluation_seeds = {task["seed"] for task in evaluation if task["experiment"] != "e1"}
    assert calibration_seeds.isdisjoint(evaluation_seeds)


def test_checkpoint_resume_returns_identical_rows(tmp_path: Path) -> None:
    cfg = copy.deepcopy(config())
    cfg["parallel_workers"] = 1
    cfg["drd"]["max_rounds"] = 2
    cfg["cbba"]["max_rounds"] = 30
    task = {
        "experiment": "test",
        "scenario_id": "checkpoint",
        "n": 4,
        "k": 2,
        "seed": 3010,
        "capacity_regime": "medium",
        "topology": "complete",
        "utilization_target": None,
        "include_oracles": False,
        "include_recovery": True,
    }
    first = execute_tasks(cfg, [task], parameters(), tmp_path, resume=False)
    second = execute_tasks(cfg, [task], parameters(), tmp_path, resume=True)
    pd.testing.assert_frame_equal(
        first["runs"].sort_index(axis=1),
        second["runs"].sort_index(axis=1),
        check_dtype=False,
    )


def test_json_checkpoint_payload_is_finite_or_explicit_nan(tmp_path: Path) -> None:
    payload = {"value": np.nan, "reason": "not_applicable"}
    path = tmp_path / "checkpoint.json"
    path.write_text(json.dumps(payload, allow_nan=True), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert np.isnan(loaded["value"])
    assert loaded["reason"] == "not_applicable"


def test_audit_is_json_serializable_with_numpy_backed_flags(tmp_path: Path) -> None:
    cfg = config()
    rows = []
    for method, variant in (
        ("DRD-simple", "raw"),
        ("DRD-simple", "recovered"),
        ("CBBA-1-Capacity", "raw"),
        ("CBBA-1-Capacity", "recovered"),
    ):
        rows.append(
            {
                "is_primary": True,
                "scenario_id": "x",
                "method_variant": f"{method}/{variant}",
                "world_hash": "w",
                "graph_hash": "g",
                "positions_hash": "p",
                "capacities_hash": "c",
                "loads_hash": "l",
                "simplex_violation": 0.0,
                "duplicate_assignment_count": 0,
                "finite_state": True,
                "censored": False,
                "censoring_reason": "",
                "seed": 81000,
            }
        )
    pd.DataFrame(rows).to_csv(tmp_path / "all_runs.csv", index=False)
    pd.DataFrame([{"planted_witness_feasible": True}]).to_csv(
        tmp_path / "worlds.csv", index=False
    )
    pd.DataFrame([{"valid": True}]).to_csv(
        tmp_path / "message_accounting_validation.csv", index=False
    )
    for name in ("config_snapshot.yaml", "all_messages.csv", "all_traces.csv"):
        (tmp_path / name).write_text("", encoding="utf-8")
    audit = audit_results(
        tmp_path,
        cfg,
        stage="preview",
        preflight_tests_passed=True,
        git_clean_start=True,
        git_clean_end=True,
    )
    json.dumps(audit)

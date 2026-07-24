from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from viu_mrob_tfm.sp1_canonical.validation.quota_game_benchmark import (
    build_full_tasks,
    build_preview_tasks,
    run_scalar_task,
    task_id,
)
from viu_mrob_tfm.sp1_canonical.validation.quota_game_cases import (
    deterministic_case_catalog,
    evaluate_service_assignment,
    make_chain_world,
    make_service_world,
    run_grape_s,
)
from viu_mrob_tfm.sp1_canonical.validation.quota_game_core import (
    PRIMARY_METHODS,
    _revision_update,
    bernstein_rounding_bound,
    categorical_round,
    certificate_diagnostics,
    continuous_metrics,
    evaluate_assignment,
    make_quota_graph,
    make_quota_world,
    nonregularized_dual_lower_bound,
    quota_aware_seed,
    raw_assignment_from_rho,
    recover_assignment,
    run_continuous_method,
    run_primary_method,
    solve_hungarian_slots,
    solve_quota_lp,
    solve_quota_milp,
    stable_hash,
)


CONFIG_PATH = Path(
    "experiments/configs/sp1_tfm_final_quota_game_benchmark_v1.yaml"
)


@pytest.fixture(scope="module")
def config() -> dict:
    value = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    value["budgets"]["evaluation_round_guard"] = {
        "calibration": 4,
        "preview": 4,
        "full": 4,
    }
    value["budgets"]["dwell_rounds"] = 3
    return value


@pytest.fixture(scope="module")
def world_graph(config: dict):
    world = make_quota_world(
        12,
        3,
        991,
        config,
        capacity_regime="medium",
        utilization=0.7,
        quota_band="medium",
        compatibility_regime="full",
    )
    return world, make_quota_graph(world, "rdisk_degree_4", config)


def test_task_counts_match_predeclared_design(config: dict) -> None:
    preview = build_preview_tasks(config)
    full = build_full_tasks(config)
    counts = {}
    for task in full:
        counts[task["experiment"]] = counts.get(task["experiment"], 0) + 1
    assert len(preview) == 15
    assert counts == {
        "E1": 150,
        "E2": 120,
        "E3": 150,
        "E4": 810,
        "E5": 240,
        "E6": 60,
        "E7": 300,
        "E8": 30,
        "E9": 260,
        "E10": 80,
    }
    assert len({task_id(task) for task in full}) == len(full)


def test_world_pairing_and_hash_are_deterministic(config: dict) -> None:
    arguments = dict(
        n=20,
        k=4,
        seed=992,
        config=config,
        capacity_regime="high",
        utilization=0.8,
        quota_band="narrow",
        compatibility_regime="critical_sparse",
    )
    first = make_quota_world(**arguments)
    second = make_quota_world(**arguments)
    assert first.world_hash == second.world_hash
    assert np.array_equal(first.capacities, second.capacities)
    assert evaluate_assignment(first, first.witness_assignment)["feasible"]


@pytest.mark.parametrize(
    "protocol",
    ["replicator", "logit", "smith", "bnn", "projection", "best_response"],
)
def test_revision_protocols_preserve_masked_simplex(protocol: str) -> None:
    rho = np.asarray([[0.3, 0.2, 0.5], [0.0, 0.6, 0.4]])
    utilities = np.asarray([[1.0, 2.0, 0.0], [3.0, 1.0, 0.0]])
    valid = np.asarray([[True, True, True], [False, True, True]])
    result = _revision_update(
        protocol,
        rho,
        utilities,
        valid,
        eta=0.1,
        temperature=0.2,
    )
    assert np.allclose(result.sum(axis=1), 1.0)
    assert np.all(result >= 0.0)
    assert result[1, 0] == 0.0


def test_closed_logit_response() -> None:
    rho = np.asarray([[0.5, 0.5]])
    utilities = np.asarray([[1.0, 0.0]])
    valid = np.ones_like(rho, dtype=bool)
    result = _revision_update(
        "logit",
        rho,
        utilities,
        valid,
        eta=1.0,
        temperature=1.0,
    )
    expected = np.exp([1.0, 0.0])
    expected /= expected.sum()
    assert np.allclose(result[0], expected)


def test_lp_milp_hungarian_and_dual_controls(config: dict) -> None:
    case = deterministic_case_catalog()[0]["world"]
    lp = solve_quota_lp(case)
    integer = solve_quota_milp(case)
    slots = np.repeat(np.arange(case.n_loads), case.lower_quotas.astype(int))
    assignment, objective = solve_hungarian_slots(case.distances_m, slots)
    dual = nonregularized_dual_lower_bound(
        case,
        np.zeros(case.n_loads),
        np.zeros(case.n_loads),
    )
    assert lp.optimal and integer.optimal
    assert evaluate_assignment(case, assignment)["feasible"]
    assert objective == pytest.approx(integer.objective_m)
    assert dual <= lp.objective_m + 1.0e-9


@pytest.mark.parametrize("length", [1, 2, 3, 6, 12])
def test_augmenting_recovery_exact_chain(length: int, config: dict) -> None:
    world, initial = make_chain_world(length)
    result = recover_assignment(world, initial, config["recovery"])
    assert result.success
    assert result.maximum_chain_length == length
    assert result.robots_reassigned == length
    assert evaluate_assignment(world, result.assignment)["feasible"]
    if length > 1:
        short = recover_assignment(
            world,
            initial,
            config["recovery"],
            max_chain_length_override=length - 1,
        )
        assert not short.success


def test_atomic_exclusivity_cbba_grape_and_pair(world_graph, config: dict) -> None:
    world, graph = world_graph
    parameters = config["calibration"]["candidates"]["balanced"]
    for method in ("Capacity-CBBA", "Weighted-GRAPE", "Weighted-Pair-GRAPE"):
        result = run_primary_method(
            world,
            graph,
            method,
            config,
            parameters,
            stage="preview",
            seed=993,
        )
        assert result.assignment.shape == (world.n_robots,)
        assert evaluate_assignment(world, result.assignment)["exclusive"]
        assert np.all((result.assignment >= 0) & (result.assignment <= world.n_loads))


def test_continuous_invariants_prices_and_censoring(world_graph, config: dict) -> None:
    world, graph = world_graph
    result = run_continuous_method(
        world,
        graph,
        "QPG-Logit-AR",
        config,
        config["calibration"]["candidates"]["balanced"],
        stage="preview",
    )
    metrics = continuous_metrics(world, result.rho)
    assert metrics["finite"]
    assert metrics["simplex_violation"] <= 1.0e-10
    assert metrics["mask_violation"] <= 1.0e-10
    assert np.all(result.lambda_minus >= 0.0)
    assert np.all(result.lambda_plus >= 0.0)
    assert result.censoring_reason in {"evaluation_round_guard", "none"}


def test_common_closure_and_certificate(world_graph, config: dict) -> None:
    world, graph = world_graph
    result = run_continuous_method(
        world,
        graph,
        "QPG-Logit-AR",
        config,
        config["calibration"]["candidates"]["balanced"],
        stage="preview",
    )
    raw = raw_assignment_from_rho(world, result.rho)
    seed = quota_aware_seed(world, result.rho)
    recovered = recover_assignment(world, seed, config["recovery"])
    lp = solve_quota_lp(world)
    integer = solve_quota_milp(world)
    diagnostics = certificate_diagnostics(
        world,
        result.rho,
        recovered.assignment,
        result.lambda_minus,
        result.lambda_plus,
        tau=config["potential"]["entropy_tau"],
        lp_reference=lp,
        milp_reference=integer,
    )
    assert evaluate_assignment(world, raw)["exclusive"]
    assert evaluate_assignment(world, seed)["exclusive"]
    assert diagnostics["certificate_valid"]


def test_bernstein_bound_and_categorical_exclusivity(world_graph) -> None:
    world, _ = world_graph
    rho = np.zeros((world.n_robots, world.n_loads + 1))
    rho[np.arange(world.n_robots), world.witness_assignment] = 1.0
    bound = bernstein_rounding_bound(world, rho)
    rng = np.random.default_rng(994)
    for _ in range(20):
        assignment = categorical_round(world, rho, rng)
        assert evaluate_assignment(world, assignment)["exclusive"]
        assert evaluate_assignment(world, assignment)["feasible"]
    assert bound["union_failure_bound"] == pytest.approx(0.0)


def test_message_accounting_and_scalar_shard(world_graph, config: dict) -> None:
    task = {
        "kind": "scalar",
        "experiment": "TEST",
        "n": 12,
        "k": 3,
        "seed": 995,
        "capacity_regime": "medium",
        "utilization": 0.7,
        "quota_band": "medium",
        "compatibility": "full",
        "topology": "rdisk_degree_4",
        "methods": ["QPG-Logit-AR"],
        "suffix": "",
    }
    payload = run_scalar_task(
        task,
        config,
        config["calibration"]["candidates"]["balanced"],
        stage="preview",
    )
    raw = next(
        row
        for row in payload["runs"]
        if row["method"] == "QPG-Logit-AR" and row["closure"] == "raw"
    )
    assert sum(row["packets"] for row in payload["messages"]) == raw["packets_total"]
    assert sum(row["bytes"] for row in payload["messages"]) == raw["payload_bytes_total"]
    encoded = json.dumps(payload, default=lambda value: value.tolist())
    assert json.loads(encoded)["worlds"][0]["world_hash"]


def test_discrete_service_domain_is_separate(config: dict) -> None:
    world = make_service_world(
        n=30,
        service_types=5,
        services_per_robot=1,
        task_fraction=0.1,
        seed=996,
        config=config,
    )
    result = run_grape_s(world, pairwise=False, seed=996, max_rounds=20)
    metrics = evaluate_service_assignment(world, result.tasks, result.services)
    assert result.method == "GRAPE-S"
    assert isinstance(metrics["feasible"], bool)
    assert "discrete-service" in result.deviation


def test_hash_changes_with_payload() -> None:
    assert stable_hash({"a": 1}) == stable_hash({"a": 1})
    assert stable_hash({"a": 1}) != stable_hash({"a": 2})

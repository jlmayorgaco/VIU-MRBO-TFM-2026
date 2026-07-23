"""Focused invariants and reproducibility tests for SP1 dynamics V3."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from viu_mrob_tfm.sp1_canonical.validation.benchmark_v3_core import (
    deterministic_case_catalog,
    run_fractional_scenario,
    scenario_graph,
    target_degree_rdisk,
)
from viu_mrob_tfm.sp1_canonical.validation.dynamics import make_graph, run_population_dynamics
from viu_mrob_tfm.sp1_canonical.validation.dynamics_benchmark_v3 import (
    _report,
    _write_hashes,
    audit_checks,
    calibration_tasks,
    execute_tasks,
    expected_primary_count,
    full_tasks,
    preview_tasks,
)
from viu_mrob_tfm.sp1_canonical.validation.dynamics_v2 import estimate_instance_preconditioner
from viu_mrob_tfm.sp1_canonical.validation.dynamics_v3 import (
    FRACTIONAL_METHODS,
    DynamicsBudgets,
    OperationCounts,
    _revision_step,
    initial_fractional_state,
    recompute_message_accounting,
    run_best_response_pure,
    run_fractional_dynamics,
)
from viu_mrob_tfm.sp1_canonical.validation.model import build_costs, generate_resource_world, manual_world


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "experiments" / "configs" / "sp1_dynamics_benchmark_v3.yaml"


def config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def selected_first(configuration: dict) -> dict[str, dict]:
    return {method: dict(configuration["calibration"]["candidates"][method][0]) for method in FRACTIONAL_METHODS}


def small_problem(seed: int = 11):
    world = generate_resource_world(20, 4, seed)
    costs, _, _ = build_costs(world, {"distance": 0.45, "time": 0.25, "energy": 0.30}, reserve_energy=5.0)
    return world, costs, make_graph(world, "complete")


def common_kwargs():
    return {
        "budgets": DynamicsBudgets(5, 10.0, 10**12, 10**7),
        "operational_tolerances": {"primal": 0.0, "consensus": 0.0, "fixed_point": 0.0},
        "refinement_tolerances": {"primal": 0.0, "consensus": 0.0, "fixed_point": 0.0},
        "attempt_refinement": False,
    }


def test_e70_catalog_contains_exact_ten_predeclared_cases() -> None:
    cases = deterministic_case_catalog()
    assert len(cases) == 10
    assert cases.case_id.is_unique
    assert set(cases.case) == {
        "symmetric_homogeneous",
        "empty_strategy_becomes_optimal",
        "rare_capacity_robot",
        "battery_incompatible_load",
        "two_loads_one_critical_robot",
        "payoff_tie",
        "complete_graph",
        "connected_rdisk",
        "masked_strategies",
        "synchronous_br_oscillation",
    }


def test_replicator_matches_v2_bit_for_bit() -> None:
    world, costs, graph = small_problem(12)
    preconditioner = estimate_instance_preconditioner(world, graph, distributed=True, eta=0.22, step_min=0.005, step_max=0.10)
    v2 = run_population_dynamics(
        world,
        costs,
        graph,
        distributed=True,
        integrator="mirror_prox",
        step=preconditioner.step,
        max_iterations=5,
        primal_tolerance=0.0,
        consensus_tolerance=0.0,
        stationarity_tolerance=0.0,
        convergence_residual_mode="relative",
        entropy_tau=0.003,
        consensus_gain=1.0,
        use_integral_consensus=True,
        history_stride=25,
    )
    v3 = run_fractional_dynamics(
        world,
        costs,
        graph,
        "Replicator-D-preconditioned",
        distributed=True,
        parameters={"eta": 0.22, "step_min": 0.005, "step_max": 0.10},
        entropy_tau=0.003,
        **common_kwargs(),
    )
    assert np.array_equal(v2.x, v3.x)
    assert np.array_equal(v2.dual, v3.dual)


@pytest.mark.parametrize("method", FRACTIONAL_METHODS)
def test_all_fractional_methods_preserve_simplex_masks_and_finiteness(method: str) -> None:
    world, costs, graph = small_problem(13)
    parameters = {"eta": 0.12, "damping": 0.35, "T_0": 0.15, "T_min": 0.005, "gamma": 0.995, "eta_br": 0.25}
    result = run_fractional_dynamics(world, costs, graph, method, distributed=True, parameters=parameters, **common_kwargs())
    assert result.invariant_violations["simplex_violation"] <= 1e-12
    assert result.invariant_violations["mask_violation"] == 0.0
    assert result.invariant_violations["nonnegativity_violation"] == 0.0
    assert result.invariant_violations["finite"]


@pytest.mark.parametrize("method", ["Smith-D-preconditioned", "BNN-D-preconditioned", "Logit-D-annealed", "BestResponse-D"])
def test_nonreplicator_can_reactivate_admissible_zero_mass(method: str) -> None:
    world = manual_world()
    costs, _, _ = build_costs(world, {"distance": 0.45, "time": 0.25, "energy": 0.30}, reserve_energy=5.0)
    graph = make_graph(world, "complete")
    initial = np.zeros((world.n_robots, world.n_loads + 1))
    initial[:, -1] = 1.0
    dual = np.full((world.n_loads, world.requirements.shape[1]), 20.0)
    result = run_fractional_dynamics(
        world,
        costs,
        graph,
        method,
        distributed=False,
        parameters={"eta": 0.12, "damping": 1.0, "T_0": 0.15, "T_min": 0.005, "gamma": 0.995, "eta_br": 0.5},
        initial_x=initial,
        initial_dual=dual,
        **common_kwargs(),
    )
    assert np.any(result.x > 0.0)
    assert result.reactivation_round is not None


def test_smith_records_quadratic_payoff_comparisons() -> None:
    world, costs, graph = small_problem(14)
    result = run_fractional_dynamics(
        world,
        costs,
        graph,
        "Smith-D-preconditioned",
        distributed=True,
        parameters={"eta": 0.12, "damping": 0.35},
        **common_kwargs(),
    )
    assert result.counts["pairwise_payoff_comparisons"] > world.n_robots * world.n_loads


def test_logit_anneals_without_crossing_minimum_temperature() -> None:
    world, costs, graph = small_problem(15)
    result = run_fractional_dynamics(
        world,
        costs,
        graph,
        "Logit-D-annealed",
        distributed=True,
        parameters={"eta": 0.12, "damping": 0.5, "T_0": 0.1, "T_min": 0.02, "gamma": 0.5},
        **common_kwargs(),
    )
    assert 0.02 <= result.terminal_temperature <= 0.1
    assert result.counts["softmax_calls"] > 0


def test_best_response_tie_breaks_to_lowest_valid_index() -> None:
    x = np.asarray([[0.25, 0.25, 0.5]])
    fitness = np.asarray([[1.0, 1.0, 0.0]])
    counts = OperationCounts()
    result = _revision_step(
        "best_response",
        x,
        fitness,
        np.asarray([[True, True]]),
        step=0.1,
        parameters={"eta_br": 0.5},
        round_index=0,
        counts=counts,
    )
    assert result[0, 0] > result[0, 1]
    assert np.isclose(result.sum(), 1.0)


def test_message_accounting_recomputes_packets_scalars_and_bytes() -> None:
    expected = recompute_message_accounting(
        logical_rounds=7,
        graph_edges=11,
        n_loads=4,
        n_resources=3,
        consensus_exchanges_per_round=2,
        distributed=True,
    )
    assert expected == {"packets_total": 308, "scalar_transmissions_total": 7392, "payload_bytes_total": 59136}


def test_battery_mask_never_receives_mass() -> None:
    world = manual_world()
    costs, _, _ = build_costs(world, {"distance": 0.45, "time": 0.25, "energy": 0.30}, reserve_energy=5.0)
    assert np.any(~np.isfinite(costs))
    state = initial_fractional_state(costs)
    assert np.all(state[:, :-1][~np.isfinite(costs)] == 0.0)


def test_pure_best_response_is_seed_reproducible() -> None:
    world, costs, graph = small_problem(16)
    budgets = DynamicsBudgets(2, 10.0, 10**12, 10**7)
    first = run_best_response_pure(world, costs, graph, parameters={"eta": 0.12}, budgets=budgets, consensus_tolerance=1e-4, seed=99)
    second = run_best_response_pure(world, costs, graph, parameters={"eta": 0.12}, budgets=budgets, consensus_tolerance=1e-4, seed=99)
    assert np.array_equal(first.assignment, second.assignment)
    assert np.array_equal(first.dual, second.dual)


def test_world_graph_cost_and_initial_state_are_paired_across_methods() -> None:
    configuration = config()
    task = {"experiment": "preview", "n": 20, "k": 4, "seed": 901, "topology": "complete", "scenario_id": "paired", "attempt_refinement": False}
    result = run_fractional_scenario(
        configuration,
        selected_first(configuration),
        task,
        DynamicsBudgets(1, 20.0, 10**12, 10**7),
        include_references=False,
        include_pure=False,
        include_recovery=True,
    )
    frame = pd.DataFrame(result["runs"])
    assert frame.world_hash.nunique() == frame.cost_hash.nunique() == frame.graph_hash.nunique() == 1
    assert frame.initial_state_hash.nunique() == frame.initial_dual_hash.nunique() == 1


def test_recovery_is_skipped_after_nonconvergence() -> None:
    configuration = config()
    task = {"experiment": "preview", "n": 20, "k": 4, "seed": 902, "topology": "complete", "scenario_id": "skip", "attempt_refinement": False}
    result = run_fractional_scenario(
        configuration,
        selected_first(configuration),
        task,
        DynamicsBudgets(1, 20.0, 10**12, 10**7),
        include_references=False,
        include_pure=False,
        include_recovery=True,
    )
    frame = pd.DataFrame(result["runs"])
    assert (~frame.operational_converged.astype(bool)).all()
    assert (~frame.recovery_executed.astype(bool)).all()
    assert frame.recovery_skipped_nonconverged.astype(bool).all()


def test_connected_rdisk_targets_degree_without_regeneration() -> None:
    world = generate_resource_world(20, 4, 903)
    graph, _ = target_degree_rdisk(world, 4)
    again, _ = target_degree_rdisk(world, 4)
    assert graph.connected and graph.lambda2 > 0.0
    assert np.array_equal(graph.adjacency, again.adjacency)


def test_exact_predeclared_run_counts() -> None:
    configuration = config()
    standard, events = full_tasks(configuration)
    assert len(calibration_tasks(configuration)) == 180
    assert len(preview_tasks(configuration)) == 30
    assert len(standard) == 600 and len(events) == 60
    assert expected_primary_count(configuration, "calibrate") == 900
    assert expected_primary_count(configuration, "preview") == 150
    assert expected_primary_count(configuration, "full") == 4200


def test_max_rounds_is_recorded_as_censoring() -> None:
    world, costs, graph = small_problem(17)
    result = run_fractional_dynamics(
        world,
        costs,
        graph,
        "BNN-D-preconditioned",
        distributed=True,
        parameters={"eta": 0.12, "damping": 0.35},
        **common_kwargs(),
    )
    assert result.censored
    assert result.censoring_reason == "max_rounds"
    assert not result.operational_converged


def test_checkpoint_resume_returns_identical_rows(tmp_path: Path) -> None:
    configuration = config()
    configuration["parallel_workers"] = 1
    task = {"kind": "preview", "experiment": "preview", "n": 20, "k": 4, "seed": 904, "topology": "complete", "scenario_id": "resume", "attempt_refinement": False}
    budget = {"max_logical_rounds": 1, "max_wall_time_s": 20.0, "max_scalar_transmissions": 10**12, "max_payoff_evaluations": 10**7}
    first = execute_tasks(configuration, [task], selected_first(configuration), budget, tmp_path, resume=False)
    second = execute_tasks(configuration, [task], selected_first(configuration), budget, tmp_path, resume=True)
    pd.testing.assert_frame_equal(
        first["runs"].sort_index(axis=1),
        second["runs"].sort_index(axis=1),
        check_dtype=False,
    )


def test_checksum_file_roundtrips(tmp_path: Path) -> None:
    (tmp_path / "artifact.txt").write_text("auditable", encoding="utf-8")
    records, valid = _write_hashes(tmp_path)
    assert valid and len(records) == 1
    digest, relative = (tmp_path / "checksums.sha256").read_text(encoding="utf-8").strip().split("  ")
    assert relative == "artifact.txt"
    assert digest == records[0]["sha256"]


def test_report_does_not_claim_recovery_without_valid_event_origin() -> None:
    runs = pd.DataFrame(
        [
            {
                "is_primary": True,
                "experiment": "e75",
                "scenario_id": f"event-{index}",
                "method": method,
                "operational_converged": False,
                "integer_feasibility": 0.0,
                "valid_event_origin": False,
                "recovery_executed": False,
                "topology": "rdisk",
            }
            for index, method in enumerate(FRACTIONAL_METHODS)
        ]
    )
    report = _report(
        config(),
        runs,
        pd.DataFrame(),
        pd.DataFrame([{"censoring_reason": "max_rounds"}]),
        pd.DataFrame(),
        None,
        1.0,
    )
    assert "0 orígenes dinámicos válidos" in report
    assert "0 recuperaciones ejecutadas" in report
    assert "no aporta evidencia" in report


def test_audit_exposes_clean_start_and_end_fields() -> None:
    configuration = config()
    runs = pd.DataFrame(
        [
            {
                "is_primary": True,
                "scenario_id": "x",
                "method": method,
                "world_hash": "w",
                "cost_hash": "c",
                "initial_state_hash": "i",
                "graph_hash": "g",
                "simplex_violation": 0.0,
                "mask_violation": 0.0,
                "finite_state": True,
                "recovery_executed": False,
                "operational_converged": False,
                "censoring_reason": "max_rounds",
                "seed": 81000,
            }
            for method in FRACTIONAL_METHODS
        ]
    )
    validation = pd.DataFrame([{"valid": True}])
    checks = audit_checks(runs, validation, configuration, stage="preview", tests_passed=True, git_clean_start=True, git_clean_end=True, hashes_valid=True)
    assert checks["git_clean_start"] and checks["git_clean_end"]
    assert "all_artifact_hashes_valid" in checks

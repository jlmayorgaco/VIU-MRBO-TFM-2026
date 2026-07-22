from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from viu_mrob_tfm.sp1_canonical.validation.auction import distributed_deficit_auction
from viu_mrob_tfm.sp1_canonical.validation.conference import (
    _e0_cases,
    _not_comparable_reason,
    _preflight_test_command,
    run_conference_config,
)
from viu_mrob_tfm.sp1_canonical.validation.dynamics import make_graph
from viu_mrob_tfm.sp1_canonical.validation.model import build_costs, generate_resource_world
from viu_mrob_tfm.sp1_canonical.validation.rounding import argmax_round, repair_assignment
from viu_mrob_tfm.sp1_canonical.validation.solvers import evaluate_relaxed, solve_lp, solve_milp


WEIGHTS = {"distance": 0.45, "time": 0.25, "energy": 0.30}


def test_conference_preflight_is_scoped_to_sp1_tests() -> None:
    command = _preflight_test_command({})
    assert command[-5:] == [
        "tests/test_sp1_canonical.py",
        "tests/test_sp1_validation.py",
        "tests/test_sp1_conference.py",
        "tests/test_sp1_e6_visualization.py",
        "tests/test_sp1_result_package.py",
    ]
    assert all("test_sp3" not in target and "test_sp4" not in target and "test_sp5" not in target for target in command)


def test_constructed_e0_cases_have_the_declared_integer_optimum() -> None:
    for _, world, expected in _e0_cases():
        costs, _, _ = build_costs(world, WEIGHTS)
        oracle = solve_milp(world, costs)
        declared = repair_assignment(world, expected, costs, prune=False, local_exchange=False, compress=False)
        assert oracle.status == 0
        assert declared.feasible
        assert np.isclose(declared.objective, oracle.objective, atol=1e-8)


def test_distributed_deficit_auction_is_reproducible_and_counts_messages() -> None:
    world = generate_resource_world(12, 3, 8801)
    costs, _, _ = build_costs(world, WEIGHTS)
    graph = make_graph(world, "ring")
    first = distributed_deficit_auction(world, costs, graph)
    second = distributed_deficit_auction(world, costs, graph)
    assert np.array_equal(first.integer.assignment, second.integer.assignment)
    assert first.messages == second.messages
    assert first.messages > 0 and first.scalars_sent == 3 * first.messages


def test_rounding_margin_and_repair_phase_switches_are_explicit() -> None:
    x = np.asarray([[0.51, 0.0], [0.49, 0.0]])
    assert argmax_round(x, margin=0.0).tolist() == [0, -1]
    assert argmax_round(x, margin=0.05).tolist() == [-1, -1]
    world = generate_resource_world(12, 2, 8802)
    costs, _, _ = build_costs(world, WEIGHTS)
    dense = np.zeros(world.n_robots, dtype=int)
    repair_only = repair_assignment(world, dense, costs, prune=False, local_exchange=False, compress=False)
    full = repair_assignment(world, dense, costs, prune=True, local_exchange=True, compress=True)
    assert repair_only.feasible == full.feasible
    if full.feasible:
        assert full.objective <= repair_only.objective + 1e-9


def test_negative_gap_is_rejected_for_infeasible_state() -> None:
    world = generate_resource_world(8, 2, 8803)
    costs, _, _ = build_costs(world, WEIGHTS)
    lp = solve_lp(world, costs)
    x = np.zeros_like(lp.x)
    metrics = evaluate_relaxed(world, x, costs)
    reason = _not_comparable_reason(
        reference_status=0,
        x=x,
        primal_normalized=1.0,
        simplex_violation=metrics["simplex_violation"],
        tolerance=1e-6,
    )
    assert reason == "primal_infeasible"


def test_tiny_conference_campaign_writes_required_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "conference"
    config = {
        "experiment_id": "SP1_CONFERENCE_TEST",
        "protocol_family": "sp1_conference_validation_frozen_v1",
        "output_dir": output_dir.as_posix(),
        "fail_on_audit": False,
        "run_preflight_tests": False,
        "parallel_workers": 2,
        "reserve_energy": 5.0,
        "oracle_time_limit_s": 5.0,
        "cost_weights": WEIGHTS,
        "dynamics": {
            "integrator": "mirror_prox", "step": 0.03, "max_iterations": 2,
            "convergence_residual_mode": "relative", "primal_tolerance": 1e-3,
            "consensus_tolerance": 1e-4, "stationarity_tolerance": 1e-3,
            "comparison_feasibility_tolerance": 1e-6, "entropy_tau": 0.003,
            "consensus_gain": 1.0, "use_integral_consensus": True, "history_stride": 1,
        },
        "statistics": {"bootstrap_resamples": 20, "analysis_seed": 970000},
        "e0": {
            "history_stride": 20,
            "acceptance": {"regularized_error": 1e-4, "primal_relative": 1e-4, "rep_d_rep_c_state_error": 1e-4},
            "dynamics": {"step": 0.1, "max_iterations": 20, "convergence_residual_mode": "absolute", "primal_tolerance": 1e-6, "consensus_tolerance": 1e-6, "stationarity_tolerance": 1e-5},
        },
        "e1": {"configurations": [[6, 2]], "seeds": [8810], "trace_stride": 1, "terminal_history_stride": 3, "dynamics": {"max_iterations": 2}},
        "e2": {"n_robots": 6, "n_loads": 2, "seeds": [8820], "topologies": ["complete", "ring"], "rdisk_levels": 2, "trace_stride": 1, "negative_control_max_iterations": 2, "dynamics": {"max_iterations": 2}},
        "e3": {"n_robots": 6, "n_loads": 2, "seeds": [8830], "integrators": ["euler_pure", "projected_euler", "exponential_replicator", "mirror_prox"], "step_factors": [0.25, 0.5, 1.0, 1.5, 2.0, 4.0], "trace_stride": 1, "dynamics": {"max_iterations": 2}},
        "e4": {"configurations": [[6, 2]], "seeds": [8840], "best_of_samples": [5, 30, 100], "rounding_margin": 0.02, "failure_penalty_multiplier": 2.0, "dynamics": {"max_iterations": 2}},
        "e5": {"fleet_sizes": [20], "robots_per_load": 5, "seed_blocks": {"20": [8850]}, "minimum_seeds_any_size": 1, "milp_max_n": 20, "rounding_margin": 0.02, "dynamics": {"max_iterations": 2}},
        "e6": {"fleet_sizes": [6], "robots_per_load": 3, "seeds": [8860], "scenarios": ["open", "warehouse"], "rounding_margin": 0.02, "dt_s": 0.1, "horizon_s": 1.0, "dynamics": {"max_iterations": 2}},
        "ablations": {"enabled": True, "n_robots": 6, "n_loads": 2, "seeds": [8870]},
    }
    config_path = tmp_path / "conference.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    manifest = run_conference_config(config_path)
    assert manifest["scientific_status"] == "partial"
    for name in (
        "audit.json", "manifest.json", "report.md", "report.pdf", "requirements-lock.txt",
        "seeds.csv", "exclusions.csv", "claim_evidence_matrix.md", "reviewer_risks.md",
        "all_runs.csv", "aggregated_results.csv",
    ):
        assert (output_dir / name).exists()
    audit = json.loads((output_dir / "audit.json").read_text(encoding="utf-8"))
    assert set(audit["gates"]) == {
        "tests_and_audits_pass", "e1_convergence_at_least_95pct", "e1_comparability_at_least_90pct",
        "e2_connected_disconnected_separated", "e2_sufficient_worlds_for_lambda2",
        "e4_repaired_feasibility_at_least_95pct", "e4_100_worlds_per_configuration_with_ci",
        "e5_multiple_seeds_reaches_n200", "distributed_nonpopulation_baseline_present", "claims_respect_scope",
    }
    resumed = run_conference_config(config_path, resume=True)
    resumed_audit = json.loads((output_dir / "audit.json").read_text(encoding="utf-8"))
    assert resumed["cached_experiments"] == ["e1", "e2", "e3", "e4", "e5", "e6"]
    assert "e1_exact_requested_world_count" in resumed_audit["checks"]
    assert "e5_all_requested_sizes_present" in resumed_audit["checks"]
    assert "e6_all_requested_size_scenario_seed_combinations" in resumed_audit["checks"]
    assert "conference_stdout.log" not in resumed["artifact_sha256"]
    for relative_path, expected_digest in resumed["artifact_sha256"].items():
        actual_digest = hashlib.sha256((output_dir / relative_path).read_bytes()).hexdigest()
        assert actual_digest == expected_digest

    partial_output = tmp_path / "conference-e6-only"
    config["output_dir"] = partial_output.as_posix()
    partial_config_path = tmp_path / "conference-e6-only.yaml"
    partial_config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    partial = run_conference_config(partial_config_path, experiment="e6")
    partial_audit = json.loads((partial_output / "audit.json").read_text(encoding="utf-8"))
    assert partial_audit["selected_experiments"] == ["e6"]
    assert partial["audit_status"] == "passed"
    assert (partial_output / "report.md").exists()

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from viu_mrob_tfm.sp1_canonical.validation.dynamics import make_graph, run_population_dynamics
from viu_mrob_tfm.sp1_canonical.validation.experiment import run_validation_config
from viu_mrob_tfm.sp1_canonical.validation.model import (
    build_costs,
    generate_resource_world,
    manual_world,
)
from viu_mrob_tfm.sp1_canonical.validation.rounding import argmax_round, evaluate_integer, repair_assignment
from viu_mrob_tfm.sp1_canonical.validation.simulation import astar_waypoints, build_warehouse_route_costs, simulate_approach
from viu_mrob_tfm.sp1_canonical.validation.solvers import (
    assignment_from_matrix,
    evaluate_relaxed,
    solve_lp,
    solve_milp,
    solve_regularized_lp,
)


WEIGHTS = {"distance": 0.45, "time": 0.25, "energy": 0.30}


def test_constructive_world_is_reproducible_and_milp_certified() -> None:
    first = generate_resource_world(10, 3, 701)
    second = generate_resource_world(10, 3, 701)
    assert first.world_hash == second.world_hash
    assert np.allclose(first.resources, second.resources)
    costs, _, _ = build_costs(first, WEIGHTS)
    solution = solve_milp(first, costs)
    metrics = evaluate_relaxed(first, solution.x, costs)
    assert solution.status == 0
    assert metrics["primal_residual"] <= 1e-8


def test_manual_world_rejects_low_battery_robot_and_needs_more_than_nearest_pair() -> None:
    world = manual_world()
    costs, compatibility, _ = build_costs(world, WEIGHTS)
    assert not compatibility[3, 0]
    assert np.any(world.resources[:2].sum(axis=0) < world.requirements[0])
    solution = solve_milp(world, costs)
    coverage = solution.x.T @ world.resources
    assert np.all(coverage >= world.requirements - 1e-8)


def test_lp_is_a_lower_bound_for_integer_reference() -> None:
    world = generate_resource_world(12, 3, 702)
    costs, _, _ = build_costs(world, WEIGHTS)
    lp = solve_lp(world, costs)
    integer = solve_milp(world, costs)
    assert lp.status == integer.status == 0
    assert lp.objective <= integer.objective + 1e-8


def test_regularized_lp_and_population_acceptance_on_manual_case() -> None:
    world = manual_world()
    costs, _, _ = build_costs(world, WEIGHTS)
    raw_lp = solve_lp(world, costs)
    regularized_lp = solve_regularized_lp(world, costs, entropy_tau=0.003)
    graph = make_graph(world, "complete")
    options = dict(
        integrator="mirror_prox",
        step=0.10,
        max_iterations=25_000,
        entropy_tau=0.003,
        primal_tolerance=1e-6,
        consensus_tolerance=1e-6,
        stationarity_tolerance=1e-5,
        lp_objective=raw_lp.objective,
    )
    central = run_population_dynamics(world, costs, graph, distributed=False, **options)
    distributed = run_population_dynamics(world, costs, graph, distributed=True, **options)
    assert regularized_lp.status == 0
    assert central.converged and distributed.converged
    assert np.linalg.norm(central.x - regularized_lp.x) < 2e-3
    assert np.linalg.norm(distributed.x - central.x) < 2e-3


def test_infeasible_population_gap_is_marked_not_comparable() -> None:
    world = generate_resource_world(8, 2, 706)
    costs, _, _ = build_costs(world, WEIGHTS)
    lp = solve_lp(world, costs)
    result = run_population_dynamics(
        world,
        costs,
        make_graph(world, "complete"),
        distributed=False,
        max_iterations=1,
        step=0.01,
        lp_objective=lp.objective,
    )
    final = result.history.iloc[-1]
    assert not bool(final["comparable_to_lp"])
    assert np.isnan(final["gap_lp"])


def test_complete_graph_distributed_dynamic_tracks_central_and_preserves_simplex() -> None:
    world = generate_resource_world(8, 2, 703)
    costs, _, _ = build_costs(world, WEIGHTS)
    lp = solve_lp(world, costs)
    graph = make_graph(world, "complete")
    options = dict(integrator="mirror_prox", step=0.03, max_iterations=150, entropy_tau=0.003)
    central = run_population_dynamics(world, costs, graph, distributed=False, lp_objective=lp.objective, **options)
    distributed = run_population_dynamics(world, costs, graph, distributed=True, lp_objective=lp.objective, **options)
    assert np.linalg.norm(central.x - distributed.x) < 0.02
    assert distributed.history["simplex_violation"].max() <= 1e-10
    assert distributed.history["min_x"].min() >= -1e-12
    assert distributed.history.iloc[-1]["consensus_residual"] < 0.01


def test_mirror_prox_uses_a_distinct_predictor_corrector_update() -> None:
    world = generate_resource_world(8, 2, 708)
    costs, _, _ = build_costs(world, WEIGHTS)
    graph = make_graph(world, "complete")
    common = dict(distributed=False, step=0.10, max_iterations=1, entropy_tau=0.003)
    exponential = run_population_dynamics(world, costs, graph, integrator="exponential", **common)
    mirror_prox = run_population_dynamics(world, costs, graph, integrator="mirror_prox", **common)
    assert np.linalg.norm(exponential.x - mirror_prox.x) > 1e-8


def test_relative_stopping_residuals_and_graph_laplacian_are_recorded() -> None:
    world = generate_resource_world(8, 2, 709)
    costs, _, _ = build_costs(world, WEIGHTS)
    graph = make_graph(world, "path")
    result = run_population_dynamics(
        world,
        costs,
        graph,
        distributed=True,
        convergence_residual_mode="relative",
        max_iterations=2,
        step=0.03,
    )
    final = result.history.iloc[-1]
    assert graph.connected and 0.0 < graph.lambda2 < 1.0
    assert final["convergence_residual_mode"] == "relative"
    assert final["stopping_primal_residual"] == final["primal_residual_relative"]
    assert final["stopping_consensus_residual"] == final["consensus_residual_relative"]
    assert final["stopping_stationarity_residual"] == final["stationarity_residual_relative"]


def test_projected_and_pure_euler_are_distinct_integrators() -> None:
    world = generate_resource_world(8, 2, 710)
    costs, _, _ = build_costs(world, WEIGHTS)
    graph = make_graph(world, "complete")
    common = dict(distributed=False, step=0.5, max_iterations=3, entropy_tau=0.0)
    pure = run_population_dynamics(world, costs, graph, integrator="euler_pure", **common)
    projected = run_population_dynamics(world, costs, graph, integrator="projected_euler", **common)
    assert pure.integrator == "euler_pure"
    assert projected.integrator == "projected_euler"
    assert projected.history["min_x"].min() >= -1e-12
    assert projected.history["simplex_violation"].max() <= 1e-10


def test_integer_repair_never_increases_deficit() -> None:
    world = generate_resource_world(10, 2, 704)
    costs, _, _ = build_costs(world, WEIGHTS)
    lp = solve_lp(world, costs)
    dynamic = run_population_dynamics(
        world,
        costs,
        make_graph(world, "complete"),
        distributed=True,
        max_iterations=100,
        step=0.03,
        lp_objective=lp.objective,
    )
    rounded = argmax_round(dynamic.x)
    raw = evaluate_integer(world, rounded, costs)
    repaired = repair_assignment(world, rounded, costs)
    assert repaired.deficit_l1 <= raw.deficit_l1 + 1e-9
    assert repaired.assignment.shape == (world.n_robots,)


def test_integer_repair_prunes_redundant_members_after_feasibility() -> None:
    world = generate_resource_world(12, 2, 707)
    costs, _, _ = build_costs(world, WEIGHTS)
    redundant = assignment_from_matrix(solve_milp(world, costs).x)
    for robot in np.flatnonzero(redundant < 0):
        compatible = np.flatnonzero(np.isfinite(costs[robot]))
        if compatible.size:
            redundant[robot] = int(compatible[0])
    before = evaluate_integer(world, redundant, costs)
    after = repair_assignment(world, redundant, costs)
    assert before.feasible and after.feasible
    assert after.objective <= before.objective + 1e-9
    assert after.pruned > 0


def test_astar_and_unicycle_approach_keep_assignment_and_targets_fixed() -> None:
    path = astar_waypoints(
        np.asarray([2.0, 8.0]),
        np.asarray([18.0, 8.0]),
        ((8.0, 12.0, 6.0, 10.0),),
    )
    assert path
    world = generate_resource_world(8, 2, 705)
    costs, _, _ = build_costs(world, WEIGHTS)
    assignment = assignment_from_matrix(solve_milp(world, costs).x)
    result = simulate_approach(world, assignment, scenario="warehouse", horizon_s=80.0)
    assert result.summary["assignment_changes"] == 0
    assert result.summary["target_changed"] is False
    assert result.summary["path_failures"] == 0
    assert result.summary["sampled_obstacle_intrusions"] == 0
    route_costs, _, route_components = build_warehouse_route_costs(world, WEIGHTS)
    assert np.isfinite(route_costs[np.isfinite(route_costs)]).all()
    assert np.all(route_components["distance"][np.isfinite(route_costs)] > 0.0)


def test_tiny_e0_e6_campaign_writes_passed_audit(tmp_path: Path) -> None:
    output_dir = tmp_path / "results"
    config = {
        "experiment_id": "test_sp1_full",
        "protocol_family": "sp1_resource_population_validation_e0_e6_v1",
        "output_dir": output_dir.as_posix(),
        "evidence_level": "C-test",
        "fail_on_audit": True,
        "reserve_energy": 5.0,
        "oracle_time_limit_s": 5.0,
        "cost_weights": WEIGHTS,
        "dynamics": {"integrator": "mirror_prox", "step": 0.03, "max_iterations": 20, "tolerance": 1e-3, "entropy_tau": 0.003, "consensus_gain": 1.0},
        "e0": {"solution_match_tolerance": 0.002, "dynamics": {"step": 0.10, "max_iterations": 25_000, "primal_tolerance": 1e-6, "consensus_tolerance": 1e-6, "stationarity_tolerance": 1e-5}},
        "e1": {"fleet_sizes": [6], "load_counts": [2], "seeds": [801]},
        "e2": {"n_robots": 6, "n_loads": 2, "seeds": [802], "topologies": ["complete", "ring"], "rdisk_radii_m": []},
        "e3": {"n_robots": 6, "n_loads": 2, "seeds": [803], "integrators": ["euler_pure", "projected_euler", "exponential", "mirror_prox"], "step_factors": [0.5]},
        "e4": {"fleet_sizes": [6], "load_counts": [2], "seeds": [804], "best_of_samples": [2]},
        "e5": {"fleet_sizes": [10], "robots_per_load": 5, "seeds": [805], "topology": "complete", "radius_m": 6.0, "lp_max_n": 10, "milp_max_n": 10},
        "e6": {"n_robots": 6, "n_loads": 2, "seeds": [806], "scenarios": ["open"], "topology": "complete", "radius_m": 6.0, "dt_s": 0.1, "horizon_s": 10.0},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    manifest = run_validation_config(config_path, experiment="all")
    assert manifest["audit_status"] == "passed"
    audit = json.loads((output_dir / "audit.json").read_text(encoding="utf-8"))
    assert all(audit["checks"].values())
    for experiment in ("e0", "e1", "e2", "e3", "e4", "e5", "e6"):
        assert (output_dir / "raw" / f"{experiment}_runs.csv").exists()

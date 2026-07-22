from __future__ import annotations

import json

import numpy as np

from viu_mrob_tfm.sp1_canonical.experiment import run_sp1_config
from viu_mrob_tfm.sp1_canonical.model import (
    bid_matrix,
    distributed_gossip_matching,
    evaluate_assignment,
    generate_world,
    greedy_matching,
    pair_cost_matrix,
    solve_central_milp,
)


WEIGHTS = {
    "distance": 0.55,
    "battery": 0.25,
    "switch_penalty": 0.20,
    "join": 0.04,
    "minimum_battery": 0.20,
}


def test_world_generation_is_reproducible() -> None:
    first = generate_world("tight", 8, 2, 9100)
    second = generate_world("tight", 8, 2, 9100)
    assert first.world_hash == second.world_hash
    assert np.array_equal(first.active, second.active)
    assert np.allclose(first.capabilities, second.capabilities)
    assert np.array_equal(first.previous_slot, second.previous_slot)


def test_central_milp_respects_exclusivity_roles_and_all_or_none_activation() -> None:
    world = generate_world("abundant", 8, 2, 9101)
    costs, _ = pair_cost_matrix(world, WEIGHTS)
    oracle = solve_central_milp(world, costs, time_limit_s=5.0)
    metrics = evaluate_assignment(world, oracle.assignment, costs)
    assert oracle.solver_status == 0
    assert metrics["invalid_assignments"] == 0
    assert metrics["duplicate_slots"] == 0
    assert metrics["waiting_loads"] == 0
    assert np.all((oracle.assignment < 0) | (oracle.assignment < world.n_slots))


def test_one_round_on_complete_graph_matches_global_greedy() -> None:
    world = generate_world("tight", 8, 2, 9101)
    costs, _ = pair_cost_matrix(world, WEIGHTS)
    scores = bid_matrix(world, costs)
    expected = greedy_matching(scores)
    distributed = distributed_gossip_matching(
        world,
        scores,
        radius_m=100.0,
        rounds=1,
    )
    assert np.array_equal(distributed.assignment, expected)
    assert np.isclose(distributed.mean_view_coverage, 1.0)
    assert distributed.network_components == 1


def test_local_profile_never_assigns_one_robot_to_multiple_slots_or_incompatible_role() -> None:
    world = generate_world("scarce", 10, 3, 9110)
    costs, _ = pair_cost_matrix(world, WEIGHTS)
    scores = bid_matrix(world, costs)
    distributed = distributed_gossip_matching(
        world,
        scores,
        radius_m=3.0,
        rounds=2,
    )
    metrics = evaluate_assignment(world, distributed.assignment, costs)
    assert distributed.assignment.shape == (world.n_robots,)
    assert metrics["invalid_assignments"] == 0
    assert np.all((distributed.assignment < 0) | (distributed.assignment < world.n_slots))


def test_evaluator_records_wait_and_abandonment_without_repairing_the_profile() -> None:
    world = generate_world("tight", 8, 2, 9101)
    costs, _ = pair_cost_matrix(world, WEIGHTS)

    abandoned = np.full(world.n_robots, -1, dtype=int)
    abandoned_metrics = evaluate_assignment(world, abandoned, costs)
    assert abandoned_metrics["abandonments"] == int(np.sum(world.previous_slot >= 0))
    assert abandoned_metrics["idle_loads"] == world.n_loads

    partial = abandoned.copy()
    robot, slot = np.argwhere(np.isfinite(costs))[0]
    partial[int(robot)] = int(slot)
    partial_metrics = evaluate_assignment(world, partial, costs)
    assert partial_metrics["started_loads"] == 0
    assert partial_metrics["waiting_loads"] == 1


def test_smoke_campaign_writes_complete_passed_artifacts(tmp_path) -> None:
    output_dir = tmp_path / "out"
    config = tmp_path / "sp1_canonical.yaml"
    config.write_text(
        "\n".join(
            [
                "experiment_id: test_sp1_canonical",
                "protocol_family: sp1_distributed_role_formation_v1",
                f"output_dir: {str(output_dir).replace(chr(92), '/')}",
                "regimes: [abundant]",
                "fleet_sizes: [8]",
                "load_counts: [2]",
                "seeds: [9100]",
                "network_cases:",
                "  - name: nominal",
                "    radius_m: 5.0",
                "    gossip_rounds: 3",
                "methods: [local_gossip, local_no_gossip, local_no_switch_penalty, global_greedy, central_milp]",
                "cost_weights:",
                "  distance: 0.55",
                "  battery: 0.25",
                "  switch_penalty: 0.20",
                "  join: 0.04",
                "  minimum_battery: 0.20",
                "oracle_time_limit_s: 5.0",
                "bootstrap_resamples: 50",
                "fail_on_audit: true",
            ]
        ),
        encoding="utf-8",
    )
    manifest = run_sp1_config(config)
    assert manifest["worlds"] == 1
    assert manifest["runs"] == 5
    audit = json.loads((output_dir / "audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "passed"
    assert (output_dir / "raw" / "runs.csv").exists()
    assert (output_dir / "raw" / "assignments.csv").exists()
    assert (output_dir / "processed" / "summary.csv").exists()
    assert (output_dir / "figures" / "fig-sp1-started-loads.pdf").exists()
    assert (output_dir / "manifest.json").exists()

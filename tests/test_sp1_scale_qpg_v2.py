from __future__ import annotations

from dataclasses import fields
from pathlib import Path
import copy
import json

import numpy as np

from viu_mrob_tfm.sp1_canonical.validation.quota_game_core import (
    evaluate_assignment,
    make_manual_quota_world,
    make_quota_graph,
)
from viu_mrob_tfm.sp1_canonical.validation.scale_qpg import (
    AtomicCommitProtocol,
    MessageLedger,
    Proposal,
    RobotLocalState,
    all_world_cost,
    atomic_potential,
    build_active_set,
    exact_move_delta,
    initialize_markets,
    residual_universe,
    run_local_recovery,
    run_scale_qpg,
)
from viu_mrob_tfm.sp1_canonical.validation.campaign_io import (
    load_resolved_config,
)
from viu_mrob_tfm.sp1_canonical.validation.scale_qpg_benchmark import (
    build_full_tasks,
    build_preview_tasks,
    run_task_set,
)
from viu_mrob_tfm.sp1_canonical.validation.validation_closure_v1_1 import (
    _convergence_tasks,
    _controlled_bernstein_state,
)


def _world():
    return make_manual_quota_world(
        case_id="scale_test",
        robot_positions=np.asarray([[0, 0], [1, 0], [9, 0], [10, 0]], dtype=float),
        load_positions=np.asarray([[0, 1], [10, 1]], dtype=float),
        capacities=np.ones(4),
        lower_quotas=np.asarray([2.0, 2.0]),
        upper_quotas=np.asarray([2.0, 2.0]),
        compatibility=np.ones((4, 2), dtype=bool),
        witness_assignment=np.asarray([0, 0, 1, 1]),
    )


def _config():
    return {
        "graph": {"eigen_tolerance": 1.0e-10},
        "scale": {
            "max_epochs": {"preview": 30, "full": 30, "calibration": 20},
            "max_wall_time_s": {"preview": 5, "full": 5, "calibration": 5},
            "max_proposals": {
                "preview": 10000,
                "full": 10000,
                "calibration": 10000,
            },
            "reservation_timeout_activations": 2,
            "stable_epochs_required": 1,
            "payload_schema": {
                "proposal": {"float64": 2, "int64": 6},
                "reservation": {"float64": 1, "int64": 5},
                "commit": {"float64": 2, "int64": 5},
                "rollback": {"float64": 0, "int64": 5},
                "market_update": {"float64": 4, "int64": 2},
                "active_set_update": {"float64": 1, "int64": 2},
                "recovery": {"float64": 2, "int64": 5},
            },
            "local_recovery": {
                "max_nodes_per_augmentation": 5000,
                "max_wall_time_s": 1.0,
                "candidates_per_load": 10,
                "compress": False,
                "local_exchange": False,
            },
        },
    }


def _parameters():
    return {
        "L": 4,
        "T0": 0.1,
        "T_min": 0.001,
        "anneal": 0.99,
        "R_explore": 10,
        "rho_minus": 20.0,
        "rho_plus": 30.0,
        "gamma_switch": 0.0,
        "epsilon_improvement": 1.0e-9,
        "epsilon_price": 0.01,
        "h": 2,
        "H": 8,
    }


def _protocol(assignment: np.ndarray):
    world = _world()
    graph = make_quota_graph(world, "complete", _config())
    markets = initialize_markets(
        world,
        assignment,
        rho_minus=20.0,
        rho_plus=30.0,
    )
    robots = [
        RobotLocalState(i, int(assignment[i]), int(assignment[i]))
        for i in range(world.n_robots)
    ]
    ledger = MessageLedger(_config()["scale"]["payload_schema"])
    protocol = AtomicCommitProtocol(
        world=world,
        graph=graph,
        assignment=assignment,
        robots=robots,
        markets=markets,
        ledger=ledger,
        rho_minus=20.0,
        rho_plus=30.0,
        gamma_switch=0.0,
        epsilon_improvement=1.0e-9,
        epsilon_price=0.01,
        reservation_timeout=2,
        previous_assignment=assignment.copy(),
    )
    return world, graph, markets, robots, ledger, protocol


def test_exact_potential_finite_difference():
    world = _world()
    assignment = np.asarray([0, 1, 1, 2])
    before = atomic_potential(
        world,
        assignment,
        rho_minus=20.0,
        rho_plus=30.0,
        gamma_switch=0.1,
        previous_assignment=np.asarray([0, 0, 1, 1]),
    )
    candidate = assignment.copy()
    candidate[3] = 0
    after = atomic_potential(
        world,
        candidate,
        rho_minus=20.0,
        rho_plus=30.0,
        gamma_switch=0.1,
        previous_assignment=np.asarray([0, 0, 1, 1]),
    )
    delta = exact_move_delta(
        world,
        assignment,
        3,
        0,
        rho_minus=20.0,
        rho_plus=30.0,
        gamma_switch=0.1,
        previous_assignment=np.asarray([0, 0, 1, 1]),
    )
    assert np.isclose(delta, after - before)


def test_active_set_is_sparse_and_robot_has_no_global_array():
    world = _world()
    assignment = np.full(world.n_robots, world.idle_index, dtype=int)
    markets = initialize_markets(
        world,
        assignment,
        rho_minus=20.0,
        rho_plus=30.0,
    )
    robot = RobotLocalState(0, world.idle_index, world.idle_index)
    active = build_active_set(
        world,
        markets,
        robot,
        maximum_size=3,
        gamma_switch=0.0,
    )
    assert len(active) <= 3
    assert world.idle_index in active
    assert all(
        not isinstance(getattr(robot, field.name), np.ndarray)
        for field in fields(robot)
    )


def test_two_phase_commit_changes_assignment_only_on_commit():
    assignment = np.asarray([0, 1, 1, 2])
    world, _, _, robots, _, protocol = _protocol(assignment)
    delta = exact_move_delta(
        world,
        assignment,
        3,
        0,
        rho_minus=20,
        rho_plus=30,
        gamma_switch=0,
        previous_assignment=assignment.copy(),
    )
    proposal = Proposal("p1", 3, 2, 0, 1.0, delta, -1, 0, 1)
    prepared = protocol.prepare(proposal, activation=1)
    assert prepared.accepted
    assert assignment[3] == 2
    assert robots[3].phase == "tentative"
    committed = protocol.commit("p1", activation=2)
    assert committed.accepted
    assert assignment[3] == 0
    assert robots[3].phase == "current"


def test_timeout_rolls_back_without_double_assignment():
    assignment = np.asarray([0, 1, 1, 2])
    world, _, _, robots, _, protocol = _protocol(assignment)
    delta = exact_move_delta(
        world,
        assignment,
        3,
        0,
        rho_minus=20,
        rho_plus=30,
        gamma_switch=0,
        previous_assignment=assignment.copy(),
    )
    proposal = Proposal("p2", 3, 2, 0, 1.0, delta, -1, 0, 1)
    assert protocol.prepare(proposal, activation=1).accepted
    protocol.expire(activation=4)
    assert assignment.tolist() == [0, 1, 1, 2]
    assert robots[3].phase == "current"
    assert protocol.rollbacks == 1


def test_stale_version_is_rejected():
    assignment = np.asarray([0, 1, 1, 2])
    world, _, _, _, _, protocol = _protocol(assignment)
    delta = exact_move_delta(
        world,
        assignment,
        3,
        0,
        rho_minus=20,
        rho_plus=30,
        gamma_switch=0,
        previous_assignment=assignment.copy(),
    )
    proposal = Proposal("p3", 3, 2, 0, 1.0, delta, -1, 99, 1)
    result = protocol.prepare(proposal, activation=1)
    assert not result.accepted
    assert result.reason == "version_conflict"
    assert protocol.version_conflicts == 1


def test_upper_and_protected_lower_quotas_reject_moves():
    feasible = np.asarray([0, 0, 1, 1])
    world, _, _, _, _, protocol = _protocol(feasible)
    delta = exact_move_delta(
        world,
        feasible,
        0,
        1,
        rho_minus=20,
        rho_plus=30,
        gamma_switch=0,
        previous_assignment=feasible.copy(),
    )
    proposal = Proposal("p4", 0, 0, 1, 1.0, delta, 0, 0, 1)
    result = protocol.prepare(proposal, activation=1)
    assert not result.accepted
    assert result.reason in {"upper_quota", "non_improving", "protected_lower_quota"}
    assert evaluate_assignment(world, feasible)["feasible"]


def test_message_accounting_is_recomputable():
    ledger = MessageLedger(_config()["scale"]["payload_schema"])
    ledger.record("proposal", route_hops=3, activation=1, robot=0, target=1)
    ledger.record("commit", route_hops=2, activation=2, robot=0, target=1)
    assert ledger.is_recomputable()
    assert ledger.totals()["payload"] == (2 * 8 + 6 * 8) * 3 + (
        2 * 8 + 5 * 8
    ) * 2


def test_local_residual_universe_and_recovery_respect_scope():
    world = _world()
    assignment = np.asarray([0, 2, 1, 1])
    active = [(0, 2), (0, 2), (1, 2), (1, 2)]
    universe = residual_universe(
        world,
        assignment,
        active,
        [0],
        radius=1,
    )
    assert 0 in universe.loads
    result = run_local_recovery(
        world,
        assignment,
        active,
        _config()["scale"]["local_recovery"],
        affected_loads=[0],
        radius=1,
        maximum_chain_length=4,
        previous_assignment=assignment.copy(),
        global_scope=False,
    )
    assert result.locality_respected
    assert set(result.touched_robots) <= set(result.universe.robots)
    assert set(result.touched_loads) <= set(result.universe.loads)


def test_scale_strict_moves_are_monotone_and_terminate():
    world = _world()
    graph = make_quota_graph(world, "complete", _config())
    result = run_scale_qpg(
        world,
        graph,
        "SCALE-QPG-LogitBR-LocalAR",
        _config(),
        _parameters(),
        stage="preview",
        seed=123,
    )
    assert result.strict_potential_monotone
    assert all(delta > _parameters()["epsilon_improvement"] for delta in result.potential_increments)
    assert result.cycles_detected == 0
    assert result.maximum_active_set_size <= _parameters()["L"]
    assert result.recovery.locality_respected
    assert result.first_atomic_assignment_time_s == 0.0
    assert result.final_termination_time_s >= 0.0
    assert result.payload_bytes_total == sum(
        row["payload_bytes"] for row in result.message_rows
    )


def test_all_world_cost_penalizes_infeasibility_above_any_feasible_distance():
    world = _world()
    feasible = np.asarray([0, 0, 1, 1])
    infeasible = np.full(4, world.idle_index, dtype=int)
    assert all_world_cost(world, infeasible) > all_world_cost(world, feasible)


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolved_benchmark_config():
    repo = _repo()
    return load_resolved_config(
        repo,
        repo / "experiments/configs/sp1_scale_qpg_benchmark_v2.yaml",
    )


def test_preview_and_full_task_counts_are_exact():
    config = _resolved_benchmark_config()
    preview = build_preview_tasks(config)
    full = build_full_tasks(config)
    assert len(preview) == 30
    observed = {
        experiment: sum(task["experiment"] == experiment for task in full)
        for experiment in [f"C{index}" for index in range(1, 10)]
    }
    assert observed == {
        "C1": 120,
        "C2": 160,
        "C3": 720,
        "C4": 120,
        "C5": 120,
        "C6": 150,
        "C7": 80,
        "C8": 400,
        "C9": 80,
    }
    calibration = set(config["calibration"]["seeds"])
    preview_seeds = set(config["preview"]["seeds"])
    evaluation_seeds = {int(task["seed"]) for task in full}
    assert calibration.isdisjoint(preview_seeds)
    assert calibration.isdisjoint(evaluation_seeds)
    assert preview_seeds.isdisjoint(evaluation_seeds)


def test_checkpoint_resume_reuses_completed_shard(tmp_path):
    config = copy.deepcopy(_resolved_benchmark_config())
    config["methods"]["scalar"] = ["SCALE-QPG-BR-LocalAR"]
    config["oracles"]["milp_max_n"] = 0
    task = build_preview_tasks(config)[0]
    parameters = {
        "profile": "test",
        **config["calibration"]["candidate_profiles"]["compact"],
    }
    _, first = run_task_set(
        tasks=[task],
        config=config,
        parameters=parameters,
        output_dir=tmp_path,
        stage="preview",
        workers=1,
        force=False,
    )
    _, second = run_task_set(
        tasks=[task],
        config=config,
        parameters=parameters,
        output_dir=tmp_path,
        stage="preview",
        workers=1,
        force=False,
    )
    assert first["tasks_executed"] == 1
    assert second["tasks_executed"] == 0
    assert second["tasks_reused"] == 1


def test_controlled_bernstein_state_uses_declared_population_size():
    world, probabilities, _ = _controlled_bernstein_state(
        0.10,
        2,
        89002,
        n=20,
        state_count=50,
    )
    assert world.n_robots == 20
    assert probabilities.shape == (20, 2)


def test_validation_closure_declares_nine_protocols_and_exact_count():
    repo = _repo()
    config = load_resolved_config(
        repo,
        repo
        / "experiments/configs/sp1_tfm_validation_closure_v1_1.yaml",
    )
    expected_methods = {
        "QPG-Replicator",
        "QPG-Logit",
        "QPG-Smith",
        "QPG-BNN",
        "QPG-Projection",
        "QPG-Damped-BestResponse",
        "DRD-simple-Replicator",
        "DRD-simple-Logit",
        "Atomic-Quota-Logit",
    }
    assert set(config["convergence"]["methods"]) == expected_methods
    assert len(_convergence_tasks(config)) == 1620
    assert config["convergence"]["max_rounds"] == 12000
    assert config["convergence"]["max_wall_time_s"] == 240
    assert config["convergence"]["dwell_rounds"] == 100


def test_v1_postcommit_audit_has_required_clean_flags():
    path = (
        _repo()
        / "results/sp1_validation/SP1_TFM_FINAL_QUOTA_GAME_BENCHMARK_v1"
        / "audit_postcommit.json"
    )
    audit = json.loads(path.read_text(encoding="utf-8"))
    assert audit["git_clean_start"] is True
    assert audit["git_clean_end"] is True
    assert audit["audit_passed_postcommit"] is True
    assert all(audit["gates"].values())

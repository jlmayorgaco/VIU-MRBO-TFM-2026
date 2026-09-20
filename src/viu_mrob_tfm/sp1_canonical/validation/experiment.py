"""Reproducible E0--E6 validation runner for canonical SP1."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import yaml

from viu_mrob_tfm.sp1_canonical.validation.dynamics import (
    estimate_operator_scale,
    make_graph,
    run_population_dynamics,
)
from viu_mrob_tfm.sp1_canonical.validation.model import (
    ResourceWorld,
    build_costs,
    generate_resource_world,
    manual_world,
    world_record,
)
from viu_mrob_tfm.sp1_canonical.validation.rounding import (
    argmax_round,
    best_of_samples,
    categorical_round,
    evaluate_integer,
    repair_assignment,
)
from viu_mrob_tfm.sp1_canonical.validation.simulation import (
    ApproachResult,
    build_warehouse_route_costs,
    simulate_approach,
)
from viu_mrob_tfm.sp1_canonical.validation.solvers import (
    allocation_entropy,
    assignment_from_matrix,
    evaluate_relaxed,
    greedy_deficit,
    solve_lp,
    solve_milp,
    solve_regularized_lp,
)


EXPERIMENTS = ("e0", "e1", "e2", "e3", "e4", "e5", "e6")


def execute(config_path: str | Path, *, experiment: str = "all") -> dict[str, Any]:
    return run_validation_config(config_path, experiment=experiment)


def run_validation_config(config_path: str | Path, *, experiment: str = "all") -> dict[str, Any]:
    config_path = Path(config_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    _validate_config(config)
    selected = list(EXPERIMENTS) if experiment == "all" else [experiment.lower()]
    unknown = set(selected) - set(EXPERIMENTS)
    if unknown:
        raise ValueError(f"Unknown SP1 validation experiments: {sorted(unknown)}")

    output_dir = Path(config["output_dir"])
    for subdir in ("raw", "processed", "tables", "figures"):
        (output_dir / subdir).mkdir(parents=True, exist_ok=True)
    config_snapshot = output_dir / "config_snapshot.yaml"
    config_snapshot.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")

    results: dict[str, dict[str, pd.DataFrame]] = {}
    checks: dict[str, bool] = {}
    for name in selected:
        payload, experiment_checks = globals()[f"_run_{name}"](config, output_dir)
        results[name] = payload
        checks.update({f"{name}_{key}": bool(value) for key, value in experiment_checks.items()})

    scientific_acceptance = _scientific_acceptance(results, checks)
    audit = {
        "status": "passed" if checks and all(checks.values()) else "failed",
        "audit_scope": "software_invariants_and_small_case_mathematical_alignment",
        "scientific_status": "partial" if scientific_acceptance.get("e0_small_case_alignment", False) else "not_established",
        "scientific_acceptance": scientific_acceptance,
        "checks": checks,
        "canonical_sp": "SP1",
        "experiments": selected,
        "evidence_level": str(config.get("evidence_level", "C-pilot")),
        "model_scope": "resource coalition formation, sampled neighbor dynamics, integer closure and unicycle approach",
        "not_claimed": (
            "La campaña de humo no demuestra los teoremas propuestos, optimalidad o convergencia global de Rep-D, "
            "seguridad continua, docking, factibilidad de wrench, transporte de carga ni validez en hardware."
        ),
    }
    (output_dir / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    report = _build_report(config, results, audit)
    (output_dir / "report.md").write_text(report, encoding="utf-8")
    manifest = _build_manifest(config_path, config, output_dir, selected, audit)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if bool(config.get("fail_on_audit", True)) and audit["status"] != "passed":
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(f"SP1 validation audit failed: {failed}")
    return manifest


def _run_e0(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    world = manual_world()
    costs, compatible, components = build_costs(world, config["cost_weights"], reserve_energy=float(config.get("reserve_energy", 5.0)))
    lp = solve_lp(world, costs)
    entropy_tau = float(_dynamic_options(config, "e0")["entropy_tau"])
    regularized_lp = solve_regularized_lp(world, costs, entropy_tau=entropy_tau)
    milp = solve_milp(world, costs, time_limit_s=float(config["oracle_time_limit_s"]))
    greedy = greedy_deficit(world, costs)
    graph = make_graph(world, "complete")
    dyn = _dynamic_options(config, "e0")
    rep_c = run_population_dynamics(world, costs, graph, distributed=False, lp_objective=lp.objective, **dyn)
    rep_d = run_population_dynamics(world, costs, graph, distributed=True, lp_objective=lp.objective, **dyn)
    rows: list[dict[str, Any]] = []
    for method, x, status, runtime, messages in (
        ("LP-raw", lp.x, lp.status, 0.0, 0),
        ("LP-tau", regularized_lp.x, regularized_lp.status, 0.0, 0),
        ("MILP", milp.x, milp.status, 0.0, 0),
        ("Greedy", greedy.x, greedy.status, 0.0, 0),
        ("Rep-C", rep_c.x, int(not rep_c.converged), rep_c.runtime_s, rep_c.messages),
        ("Rep-D", rep_d.x, int(not rep_d.converged), rep_d.runtime_s, rep_d.messages),
    ):
        metrics = evaluate_relaxed(world, x, costs)
        rows.append(
            {
                "method": method,
                "status": status,
                "objective": metrics["objective"],
                "primal_residual": metrics["primal_residual"],
                "error_to_lp": float(np.linalg.norm(x - lp.x)),
                "error_to_lp_regularized": float(np.linalg.norm(x - regularized_lp.x)),
                "regularized_objective": _regularized_objective(x, costs, entropy_tau),
                "runtime_s": runtime,
                "messages": messages,
            }
        )
    runs = pd.DataFrame(rows)
    robots = pd.DataFrame(
        {
            "robot_id": np.arange(world.n_robots),
            "payload": world.resources[:, 1],
            "force": world.resources[:, 2],
            "battery": world.battery_energy,
            "distance": components["distance"][:, 0],
            "energy_required": components["energy"][:, 0],
            "compatible": compatible[:, 0],
            "milp_selected": milp.x[:, 0] > 0.5,
        }
    )
    histories = pd.concat(
        [rep_c.history.assign(method="Rep-C"), rep_d.history.assign(method="Rep-D")], ignore_index=True
    )
    _write_payload(output_dir, "e0", {"runs": runs, "robots": robots, "history": histories})
    coverage = np.einsum("ik,im->km", milp.x, world.resources)
    checks = {
        "lp_solved": lp.status == 0,
        "regularized_lp_solved": regularized_lp.status == 0,
        "milp_solved": milp.status == 0,
        "milp_covers_resources": bool(np.all(coverage + 1e-8 >= world.requirements)),
        "low_battery_robot_rejected": bool(not compatible[3, 0]),
        "two_nearest_are_insufficient": bool(np.any(world.resources[:2].sum(axis=0) + 1e-8 < world.requirements[0])),
        "exponential_simplex_preserved": bool(rep_d.history["simplex_violation"].max() <= 1e-10 and rep_d.history["min_x"].min() >= -1e-12),
        "rep_c_converged": rep_c.converged,
        "rep_d_converged": rep_d.converged,
        "rep_c_matches_regularized_lp": bool(np.linalg.norm(rep_c.x - regularized_lp.x) <= float(config["e0"].get("solution_match_tolerance", 2e-3))),
        "rep_d_matches_rep_c": bool(np.linalg.norm(rep_d.x - rep_c.x) <= float(config["e0"].get("solution_match_tolerance", 2e-3))),
    }
    return {"runs": runs, "robots": robots, "history": histories}, checks


def _run_e1(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e1"]
    runs: list[dict[str, Any]] = []
    histories: list[pd.DataFrame] = []
    worlds: list[dict[str, Any]] = []
    for n, k, seed in _factor_worlds(section):
        world = generate_resource_world(n, k, seed)
        costs, _, _ = build_costs(world, config["cost_weights"], reserve_energy=float(config.get("reserve_energy", 5.0)))
        lp = solve_lp(world, costs)
        entropy_tau = float(_dynamic_options(config, "e1")["entropy_tau"])
        regularized_lp = solve_regularized_lp(world, costs, entropy_tau=entropy_tau)
        graph = make_graph(world, "complete")
        worlds.append(world_record(world))
        runs.append(
            _relaxed_row(
                "LP-raw", world, lp.x, costs, lp.objective, 0, 0.0, 0, 0, True, graph.lambda2,
                entropy_tau=entropy_tau, regularized_reference=regularized_lp.regularized_objective,
            )
        )
        runs.append(
            _relaxed_row(
                "LP-tau", world, regularized_lp.x, costs, lp.objective, 0, 0.0, 0, 0, True, graph.lambda2,
                entropy_tau=entropy_tau, regularized_reference=regularized_lp.regularized_objective,
            )
        )
        for method, distributed in (("Rep-C", False), ("Rep-D", True)):
            result = run_population_dynamics(
                world,
                costs,
                graph,
                distributed=distributed,
                lp_objective=lp.objective,
                **_dynamic_options(config, "e1"),
            )
            row = _relaxed_row(
                method,
                world,
                result.x,
                costs,
                lp.objective,
                result.iterations,
                result.runtime_s,
                result.messages,
                result.scalars_sent,
                result.converged,
                graph.lambda2,
                entropy_tau=entropy_tau,
                regularized_reference=regularized_lp.regularized_objective,
            )
            row["error_to_lp"] = float(np.linalg.norm(result.x - lp.x))
            row["error_to_lp_regularized"] = float(np.linalg.norm(result.x - regularized_lp.x))
            row.update(_final_dynamic_metrics(result))
            runs.append(row)
            histories.append(result.history.assign(method=method, world_hash=world.world_hash, n_robots=n, n_loads=k, seed=seed))
    runs_df = pd.DataFrame(runs)
    history_df = pd.concat(histories, ignore_index=True) if histories else pd.DataFrame()
    worlds_df = pd.DataFrame(worlds).drop_duplicates("world_hash")
    summary = _numeric_summary(runs_df, ["method", "n_robots", "n_loads"])
    payload = {"runs": runs_df, "history": history_df, "worlds": worlds_df, "summary": summary}
    _write_payload(output_dir, "e1", payload)
    _plot_e1(output_dir, history_df)
    expected = len(list(_factor_worlds(section))) * 4
    checks = {
        "expected_runs": len(runs_df) == expected,
        "lp_solved_and_feasible": bool((runs_df[runs_df.method.isin(["LP-raw", "LP-tau"])]["primal_residual"] <= 1e-7).all()),
        "paired_worlds": bool((runs_df.groupby("world_hash")["method"].nunique() == 4).all()),
        "population_simplex": bool((runs_df[runs_df.method.str.startswith("Rep")]["simplex_violation"] <= 1e-9).all()),
        "finite_metrics": _finite_columns(runs_df, ["objective", "primal_residual", "runtime_s"]),
        "infeasible_gaps_are_not_comparable": bool(runs_df.loc[~runs_df["comparable_to_lp"], "gap_lp"].isna().all()),
    }
    return payload, checks


def _run_e2(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e2"]
    runs: list[dict[str, Any]] = []
    histories: list[pd.DataFrame] = []
    for seed in _seeds(section["seeds"]):
        world = generate_resource_world(int(section["n_robots"]), int(section["n_loads"]), seed)
        costs, _, _ = build_costs(world, config["cost_weights"], reserve_energy=float(config.get("reserve_energy", 5.0)))
        lp = solve_lp(world, costs)
        graph_cases: list[tuple[str, str, float, bool]] = [(str(name), str(name), 0.0, True) for name in section["topologies"]]
        graph_cases += [(f"rdisk_connected_{radius:g}", "rdisk", float(radius), True) for radius in section.get("rdisk_radii_m", [])]
        graph_cases += [(f"rdisk_negative_{radius:g}", "rdisk", float(radius), False) for radius in section.get("negative_control_radii_m", [])]
        for graph_case, topology, requested_radius, force_connected in graph_cases:
            # Keep the requested R-disk radius literal.  Silently increasing
            # it until connectivity would change the experimental factor and
            # can make two requested radii generate the same graph.
            effective_radius = requested_radius or 6.0
            graph = make_graph(world, topology, radius_m=effective_radius)
            dynamic_options = _dynamic_options(config, "e2")
            if not force_connected:
                dynamic_options["max_iterations"] = int(
                    section.get("negative_control_max_iterations", dynamic_options["max_iterations"])
                )
            result = run_population_dynamics(
                world,
                costs,
                graph,
                distributed=True,
                lp_objective=lp.objective,
                **dynamic_options,
            )
            row = _relaxed_row(
                "Rep-D",
                world,
                result.x,
                costs,
                lp.objective,
                result.iterations,
                result.runtime_s,
                result.messages,
                result.scalars_sent,
                result.converged,
                graph.lambda2,
            )
            assumption_class = "theorem_connected" if force_connected else "negative_disconnected"
            row.update(
                {
                    "graph_case": graph_case,
                    "graph_fingerprint": _graph_fingerprint(graph.adjacency),
                    "edges": graph.edges,
                    "lambda_max": graph.lambda_max,
                    "connected": graph.connected,
                    "assumption_class": assumption_class,
                    "requested_radius_m": requested_radius,
                    "effective_radius_m": effective_radius,
                    "expected_connected": bool(force_connected),
                    "R_epsilon": float(result.iterations) if result.converged else math.nan,
                    "right_censored": not result.converged,
                    "iteration_limit": int(dynamic_options["max_iterations"]),
                }
            )
            row.update(_final_dynamic_metrics(result))
            runs.append(row)
            histories.append(result.history.assign(world_hash=world.world_hash, seed=seed, graph_case=graph_case, lambda2=graph.lambda2))
    runs_df = pd.DataFrame(runs)
    history_df = pd.concat(histories, ignore_index=True) if histories else pd.DataFrame()
    summary = _numeric_summary(runs_df, ["assumption_class", "graph_case"])
    payload = {"runs": runs_df, "history": history_df, "summary": summary}
    _write_payload(output_dir, "e2", payload)
    _plot_e2(output_dir, runs_df)
    checks = {
        "all_graphs_recorded": bool(
            runs_df["graph_case"].nunique()
            == len(section["topologies"]) + len(section.get("rdisk_radii_m", [])) + len(section.get("negative_control_radii_m", []))
        ),
        "theorem_graphs_connected": bool(runs_df.loc[runs_df.assumption_class == "theorem_connected", "connected"].all()),
        "connected_radius_is_not_silently_adjusted": bool(
            np.isclose(
                runs_df.loc[runs_df.requested_radius_m > 0, "requested_radius_m"],
                runs_df.loc[runs_df.requested_radius_m > 0, "effective_radius_m"],
            ).all()
        ),
        "negative_controls_separated": bool((~runs_df.loc[runs_df.assumption_class == "negative_disconnected", "connected"]).all()),
        "theorem_graphs_are_distinct": bool(
            runs_df.loc[runs_df.assumption_class == "theorem_connected"]
            .groupby("world_hash")["graph_fingerprint"]
            .nunique()
            .eq(len(section["topologies"]) + len(section.get("rdisk_radii_m", [])))
            .all()
        ),
        "lambda2_targets_are_separated": bool(
            runs_df.loc[runs_df.assumption_class == "theorem_connected"]
            .groupby("world_hash")["lambda2"]
            .nunique()
            .ge(
                int(
                    section.get(
                        "minimum_distinct_lambda2",
                        min(4, len(section["topologies"]) + len(section.get("rdisk_radii_m", []))),
                    )
                )
            )
            .all()
        ),
        "spectra_nonnegative": bool((runs_df["lambda2"] >= -1e-9).all() and (runs_df["lambda_max"] >= -1e-9).all()),
        "messages_match_scope": bool(((runs_df["edges"] == 0) == (runs_df["messages"] == 0)).all()),
        "simplex_preserved": bool((runs_df["simplex_violation"] <= 1e-9).all()),
        "finite_metrics": _finite_columns(runs_df, ["objective", "primal_residual", "consensus_residual"]),
    }
    return payload, checks


def _run_e3(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e3"]
    runs: list[dict[str, Any]] = []
    histories: list[pd.DataFrame] = []
    terminal_states: dict[tuple[int, float, str], np.ndarray] = {}
    for seed in _seeds(section["seeds"]):
        world = generate_resource_world(int(section["n_robots"]), int(section["n_loads"]), seed)
        costs, _, _ = build_costs(world, config["cost_weights"], reserve_energy=float(config.get("reserve_energy", 5.0)))
        lp = solve_lp(world, costs)
        graph = make_graph(world, "complete")
        alpha_reference = 1.0 / estimate_operator_scale(world, costs)
        for integrator in section["integrators"]:
            for factor in section["step_factors"]:
                step = float(factor) * alpha_reference
                options = _dynamic_options(config, "e3")
                options.pop("integrator", None)
                options["step"] = step
                result = run_population_dynamics(
                    world,
                    costs,
                    graph,
                    distributed=False,
                    integrator=str(integrator),
                    lp_objective=lp.objective,
                    **options,
                )
                canonical_integrator = "euler_pure" if str(integrator) == "explicit_euler" else str(integrator)
                row = _relaxed_row(
                    canonical_integrator, world, result.x, costs, lp.objective, result.iterations, result.runtime_s, 0, 0, result.converged, graph.lambda2
                )
                row.update({"integrator": canonical_integrator, "step_factor": float(factor), "step": step, "alpha_reference": alpha_reference})
                row.update(_final_dynamic_metrics(result))
                runs.append(row)
                histories.append(result.history.assign(world_hash=world.world_hash, seed=seed, integrator=canonical_integrator, step_factor=float(factor), step=step))
                terminal_states[(seed, float(factor), canonical_integrator)] = result.x.copy()
    runs_df = pd.DataFrame(runs)
    history_df = pd.concat(histories, ignore_index=True) if histories else pd.DataFrame()
    summary = _numeric_summary(runs_df, ["integrator", "step_factor"])
    payload = {"runs": runs_df, "history": history_df, "summary": summary}
    _write_payload(output_dir, "e3", payload)
    _plot_e3(output_dir, runs_df)
    protected = runs_df[runs_df.integrator.isin(["projected_euler", "exponential", "mirror_prox"])]
    pure = runs_df[runs_df.integrator == "euler_pure"]
    predictor_differences = [
        float(np.linalg.norm(terminal_states[(seed, float(factor), "mirror_prox")] - terminal_states[(seed, float(factor), "exponential")]))
        for seed in _seeds(section["seeds"])
        for factor in section["step_factors"]
        if (seed, float(factor), "mirror_prox") in terminal_states and (seed, float(factor), "exponential") in terminal_states
    ]
    checks = {
        "all_factor_integrator_pairs": bool(len(runs_df) == len(_seeds(section["seeds"])) * len(section["integrators"]) * len(section["step_factors"])),
        "projected_methods_nonnegative": bool((protected["min_x"] >= -1e-12).all()),
        "projected_methods_simplex": bool((protected["simplex_violation"] <= 1e-9).all()),
        "pure_euler_recorded_without_projection": bool(not pure.empty),
        "finite_reference_step": bool(np.isfinite(runs_df["alpha_reference"]).all() and (runs_df["alpha_reference"] > 0).all()),
        "mirror_prox_differs_from_single_step": bool(predictor_differences and max(predictor_differences) > 1e-8),
    }
    return payload, checks


def _run_e4(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e4"]
    rows: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    for n, k, seed in _factor_worlds(section):
        world = generate_resource_world(n, k, seed)
        costs, _, _ = build_costs(world, config["cost_weights"], reserve_energy=float(config.get("reserve_energy", 5.0)))
        lp = solve_lp(world, costs)
        milp = solve_milp(world, costs, time_limit_s=float(config["oracle_time_limit_s"]))
        graph = make_graph(world, "complete")
        dynamic = run_population_dynamics(
            world, costs, graph, distributed=True, lp_objective=lp.objective, **_dynamic_options(config, "e4")
        )
        rng = np.random.default_rng(seed + 424_243)
        argmax_assignment = argmax_round(dynamic.x)
        one_sample = categorical_round(dynamic.x, rng)
        methods = {
            "Argmax": evaluate_integer(world, argmax_assignment, costs),
            "Categorical-1": evaluate_integer(world, one_sample, costs),
            "Argmax+repair": repair_assignment(world, argmax_assignment, costs),
            "Categorical+repair": repair_assignment(world, one_sample, costs),
        }
        for samples in section.get("best_of_samples", [5, 30]):
            methods[f"Best-{int(samples)}"] = best_of_samples(world, dynamic.x, costs, samples=int(samples), rng=rng, repair=False)
        milp_assignment = assignment_from_matrix(milp.x)
        methods["MILP"] = evaluate_integer(world, milp_assignment, costs)
        integrality_gap = 100.0 * (milp.objective - lp.objective) / max(abs(milp.objective), 1e-12)
        for method, result in methods.items():
            integer_gap = math.nan
            if result.feasible and np.isfinite(milp.objective):
                integer_gap = 100.0 * (result.objective - milp.objective) / max(abs(milp.objective), 1e-12)
            rows.append(
                {
                    "world_hash": world.world_hash,
                    "seed": seed,
                    "n_robots": n,
                    "n_loads": k,
                    "method": method,
                    "feasible": result.feasible,
                    "objective": result.objective,
                    "integer_gap_percent": integer_gap,
                    "integrality_gap_percent": integrality_gap,
                    "deficit_l1": result.deficit_l1,
                    "overassignment_l1": result.overassignment_l1,
                    "repairs": result.repairs,
                    "pruned": result.pruned,
                    "exchanges": result.exchanges,
                    "milp_status": milp.status,
                }
            )
            for robot, load in enumerate(result.assignment):
                assignments.append({"world_hash": world.world_hash, "method": method, "robot_id": robot, "load_id": int(load)})
    runs_df = pd.DataFrame(rows)
    assignments_df = pd.DataFrame(assignments)
    summary = _integer_summary(runs_df)
    payload = {"runs": runs_df, "assignments": assignments_df, "summary": summary}
    _write_payload(output_dir, "e4", payload)
    _plot_e4(output_dir, summary)
    milp_rows = runs_df[runs_df.method == "MILP"]
    argmax_pairs = runs_df.pivot(index="world_hash", columns="method", values="deficit_l1")
    checks = {
        "milp_certifies_all_worlds": bool(milp_rows["feasible"].all() and (milp_rows["milp_status"] == 0).all()),
        "one_assignment_per_robot": bool(assignments_df.groupby(["world_hash", "method", "robot_id"]).size().eq(1).all()),
        "argmax_repair_not_worse": bool((argmax_pairs["Argmax+repair"] <= argmax_pairs["Argmax"] + 1e-9).all()),
        "nonnegative_certified_gaps": bool((milp_rows["integer_gap_percent"].abs() <= 1e-8).all()),
        "finite_deficits": _finite_columns(runs_df, ["deficit_l1", "overassignment_l1"]),
    }
    return payload, checks


def _run_e5(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e5"]
    rows: list[dict[str, Any]] = []
    for n in section["fleet_sizes"]:
        n = int(n)
        k = max(1, int(round(n / float(section.get("robots_per_load", 5.0)))))
        for seed in _seeds(section["seeds"]):
            world = generate_resource_world(n, k, seed)
            costs, _, _ = build_costs(world, config["cost_weights"], reserve_energy=float(config.get("reserve_energy", 5.0)))
            witness = evaluate_integer(world, world.feasibility_witness, costs)
            topology = str(section.get("topology", "rdisk"))
            effective_radius = float(section.get("radius_m", 6.0))
            graph = make_graph(world, topology, radius_m=effective_radius)
            if bool(section.get("ensure_connected", True)):
                while not graph.connected and topology == "rdisk" and effective_radius < 30.0:
                    effective_radius += 0.5
                    graph = make_graph(world, topology, radius_m=effective_radius)
            start = time.perf_counter()
            greedy = greedy_deficit(world, costs)
            greedy_time = time.perf_counter() - start
            greedy_integer = evaluate_integer(world, assignment_from_matrix(greedy.x), costs)

            lp = solve_lp(world, costs) if n <= int(section.get("lp_max_n", 100)) else None
            dynamic = run_population_dynamics(
                world,
                costs,
                graph,
                distributed=True,
                lp_objective=lp.objective if lp is not None else None,
                **_dynamic_options(config, "e5"),
            )
            rounded = evaluate_integer(world, argmax_round(dynamic.x), costs)
            repair_start = time.perf_counter()
            repaired = repair_assignment(world, rounded.assignment, costs)
            repair_time = time.perf_counter() - repair_start
            best_known = math.nan
            if n <= int(section.get("milp_max_n", 30)):
                milp_start = time.perf_counter()
                milp = solve_milp(world, costs, time_limit_s=float(config["oracle_time_limit_s"]))
                milp_time = time.perf_counter() - milp_start
                milp_integer = evaluate_integer(world, assignment_from_matrix(milp.x), costs)
                best_known = milp_integer.objective if milp_integer.feasible else math.nan
                milp_row = _scale_row("MILP", world, milp_integer, milp_time, 1, 0, graph, best_known)
                milp_row.update(
                    {
                        "world_constructively_feasible": witness.feasible,
                        "graph_connected": graph.connected,
                        "effective_radius_m": effective_radius,
                        "dynamics_converged": True,
                        "fractional_converged": None,
                        "rounded_feasible": None,
                        "repair_succeeded": None,
                        "pruning_completed": None,
                        "failure_stage": "none" if milp_integer.feasible else "oracle_not_certified",
                    }
                )
                rows.append(milp_row)
            greedy_row = _scale_row("Greedy", world, greedy_integer, greedy_time, 1, 0, graph, best_known)
            greedy_row.update(
                {
                    "world_constructively_feasible": witness.feasible,
                    "graph_connected": graph.connected,
                    "effective_radius_m": effective_radius,
                    "dynamics_converged": True,
                    "fractional_converged": None,
                    "rounded_feasible": None,
                    "repair_succeeded": None,
                    "pruning_completed": None,
                    "failure_stage": "none" if greedy_integer.feasible else "greedy_heuristic_failed",
                }
            )
            rows.append(greedy_row)
            rep_row = _scale_row(
                    "Rep-D+repair",
                    world,
                    repaired,
                    dynamic.runtime_s + repair_time,
                    max(dynamic.iterations, 1),
                    dynamic.messages,
                    graph,
                    best_known,
                    scalars=dynamic.scalars_sent,
            )
            if repaired.feasible:
                failure_stage = "none"
            elif not witness.feasible:
                failure_stage = "world_infeasible"
            elif not graph.connected:
                failure_stage = "graph_disconnected"
            elif not dynamic.converged:
                failure_stage = "dynamics_not_converged"
            else:
                failure_stage = "integer_recovery_failed"
            rep_row.update(
                {
                    "world_constructively_feasible": witness.feasible,
                    "graph_connected": graph.connected,
                    "effective_radius_m": effective_radius,
                    "dynamics_converged": dynamic.converged,
                    "fractional_converged": dynamic.converged,
                    "fractional_comparable_to_lp": bool(dynamic.history.iloc[-1]["comparable_to_lp"]),
                    "rounded_feasible": rounded.feasible,
                    "rounded_deficit_l1": rounded.deficit_l1,
                    "repair_succeeded": repaired.feasible,
                    "pruning_completed": repaired.feasible,
                    "repair_actions": repaired.repairs,
                    "pruned_robots": repaired.pruned,
                    "local_exchanges": repaired.exchanges,
                    "failure_stage": failure_stage,
                }
            )
            rows.append(rep_row)
    runs_df = pd.DataFrame(rows)
    summary = _numeric_summary(runs_df, ["method", "n_robots"])
    payload = {"runs": runs_df, "summary": summary}
    _write_payload(output_dir, "e5", payload)
    _plot_e5(output_dir, runs_df)
    checks = {
        "all_sizes_present": bool(runs_df["n_robots"].nunique() == len(section["fleet_sizes"])),
        "finite_runtime": _finite_columns(runs_df, ["runtime_s", "time_per_iteration_s"]),
        "nonnegative_communication": bool((runs_df["messages"] >= 0).all() and (runs_df["scalars_sent"] >= 0).all()),
        "local_memory_recorded": bool((runs_df["estimated_state_scalars"] > 0).all()),
        "worlds_constructively_feasible": bool(runs_df["world_constructively_feasible"].all()),
        "failures_classified": bool(runs_df["failure_stage"].notna().all()),
        "rep_d_phases_recorded": bool(
            runs_df.loc[runs_df.method == "Rep-D+repair", [
                "fractional_converged", "rounded_feasible", "repair_succeeded", "pruning_completed"
            ]].notna().all().all()
        ),
    }
    return payload, checks


def _run_e6(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e6"]
    rows: list[dict[str, Any]] = []
    trajectories: list[pd.DataFrame] = []
    visual_results: list[tuple[ResourceWorld, ApproachResult, str]] = []
    for seed in _seeds(section["seeds"]):
        world = generate_resource_world(int(section["n_robots"]), int(section["n_loads"]), seed)
        for scenario in section["scenarios"]:
            if str(scenario) == "warehouse":
                costs, _, components = build_warehouse_route_costs(
                    world,
                    config["cost_weights"],
                    reserve_energy=float(config.get("reserve_energy", 5.0)),
                )
                cost_model = "astar_route_length"
            else:
                costs, _, components = build_costs(
                    world,
                    config["cost_weights"],
                    reserve_energy=float(config.get("reserve_energy", 5.0)),
                )
                cost_model = "euclidean_distance"
            lp = solve_lp(world, costs)
            graph = make_graph(world, str(section.get("topology", "complete")), radius_m=float(section.get("radius_m", 6.0)))
            dynamic = run_population_dynamics(
                world, costs, graph, distributed=True, lp_objective=lp.objective, **_dynamic_options(config, "e6")
            )
            integer = repair_assignment(world, argmax_round(dynamic.x), costs)
            if not integer.feasible:
                oracle = solve_milp(world, costs, time_limit_s=float(config["oracle_time_limit_s"]))
                integer = evaluate_integer(world, assignment_from_matrix(oracle.x), costs)
                assignment_source = "MILP_fallback_after_failed_local_repair"
            else:
                assignment_source = "Rep-D_argmax_repair"
            estimated_energy_by_robot = np.zeros(world.n_robots)
            for robot, load in enumerate(integer.assignment):
                if load >= 0:
                    estimated_energy_by_robot[robot] = components["energy"][robot, load]
            result = simulate_approach(
                world,
                integer.assignment,
                scenario=str(scenario),
                dt_s=float(section.get("dt_s", 0.10)),
                horizon_s=float(section.get("horizon_s", 80.0)),
                estimated_energy_by_robot=estimated_energy_by_robot,
            )
            row = dict(result.summary)
            row.update(
                {
                    "world_hash": world.world_hash,
                    "seed": seed,
                    "n_robots": world.n_robots,
                    "n_loads": world.n_loads,
                    "assignment_feasible": integer.feasible,
                    "assignment_source": assignment_source,
                    "cost_model": cost_model,
                    "messages": dynamic.messages,
                }
            )
            rows.append(row)
            trajectories.append(result.trajectories.assign(world_hash=world.world_hash, seed=seed, assignment_source=assignment_source))
            if len(visual_results) < len(section["scenarios"]):
                visual_results.append((world, result, str(scenario)))
    runs_df = pd.DataFrame(rows)
    trajectories_df = pd.concat(trajectories, ignore_index=True) if trajectories else pd.DataFrame()
    summary = _numeric_summary(runs_df, ["scenario", "assignment_source"])
    payload = {"runs": runs_df, "trajectories": trajectories_df, "summary": summary}
    _write_payload(output_dir, "e6", payload)
    _plot_e6(output_dir, visual_results)
    checks = {
        "assignments_feasible": bool(runs_df["assignment_feasible"].all()),
        "fixed_assignment": bool((runs_df["assignment_changes"] == 0).all()),
        "fixed_targets": bool((~runs_df["target_changed"]).all()),
        "paths_found": bool((runs_df["path_failures"] == 0).all()),
        "finite_trajectories": bool(not trajectories_df.empty and np.isfinite(trajectories_df[["x_m", "y_m", "theta_rad"]].to_numpy()).all()),
        "no_sampled_obstacle_intrusion": bool((runs_df["sampled_obstacle_intrusions"] == 0).all()),
        "warehouse_uses_route_energy": bool((runs_df.loc[runs_df.scenario == "warehouse", "cost_model"] == "astar_route_length").all()),
    }
    return payload, checks


def _dynamic_options(config: dict[str, Any], experiment: str) -> dict[str, Any]:
    common = dict(config["dynamics"])
    common.update(config.get(experiment, {}).get("dynamics", {}))
    return {
        "integrator": str(common.get("integrator", "mirror_prox")),
        "step": float(common.get("step", 0.03)),
        "max_iterations": int(common.get("max_iterations", 300)),
        "tolerance": float(common.get("tolerance", 1e-3)),
        "primal_tolerance": float(common.get("primal_tolerance", common.get("tolerance", 1e-3))),
        "consensus_tolerance": float(common.get("consensus_tolerance", common.get("tolerance", 1e-3))),
        "stationarity_tolerance": float(common.get("stationarity_tolerance", common.get("tolerance", 1e-3))),
        "convergence_residual_mode": str(common.get("convergence_residual_mode", "absolute")),
        "comparison_feasibility_tolerance": float(common.get("comparison_feasibility_tolerance", 1e-6)),
        "entropy_tau": float(common.get("entropy_tau", 0.005)),
        "consensus_gain": float(common.get("consensus_gain", 1.0)),
    }


def _graph_fingerprint(adjacency: np.ndarray) -> str:
    packed = np.packbits(np.asarray(adjacency, dtype=np.uint8), axis=None)
    return hashlib.sha256(packed.tobytes()).hexdigest()[:16]


def _factor_worlds(section: dict[str, Any]) -> Iterable[tuple[int, int, int]]:
    for n in section["fleet_sizes"]:
        for k in section["load_counts"]:
            if int(n) >= int(k):
                for seed in _seeds(section["seeds"]):
                    yield int(n), int(k), seed


def _seeds(specification: list[int] | dict[str, int]) -> list[int]:
    if isinstance(specification, list):
        return [int(seed) for seed in specification]
    start = int(specification["start"])
    return list(range(start, start + int(specification["count"])))


def _relaxed_row(
    method: str,
    world: ResourceWorld,
    x: np.ndarray,
    costs: np.ndarray,
    lp_objective: float,
    iterations: int,
    runtime_s: float,
    messages: int,
    scalars_sent: int,
    converged: bool,
    lambda2: float,
    *,
    entropy_tau: float = 0.0,
    regularized_reference: float = math.nan,
) -> dict[str, Any]:
    metrics = evaluate_relaxed(world, x, costs)
    normalized = world.resources[:, None, :] / np.maximum(world.requirements[None, :, :], 1e-12)
    coverage = np.einsum("ik,ikm->km", x, normalized)
    raw_gap = (metrics["objective"] - lp_objective) / max(abs(lp_objective), 1e-12)
    comparable = bool(float(np.linalg.norm(np.maximum(1.0 - coverage, 0.0))) <= 1e-6)
    gap = raw_gap if comparable else math.nan
    regularized_objective = _regularized_objective(x, costs, entropy_tau)
    regularized_gap = math.nan
    if comparable and np.isfinite(regularized_reference):
        regularized_gap = (regularized_objective - regularized_reference) / max(abs(regularized_reference), 1e-12)
    return {
        "world_hash": world.world_hash,
        "seed": world.seed,
        "n_robots": world.n_robots,
        "n_loads": world.n_loads,
        "method": method,
        "objective": metrics["objective"],
        "lp_objective": lp_objective,
        "gap_lp": gap,
        "gap_lp_unfiltered": raw_gap,
        "comparable_to_lp": comparable,
        "regularized_objective": regularized_objective,
        "regularized_reference": regularized_reference,
        "gap_regularized_lp": regularized_gap,
        "primal_residual": metrics["primal_residual"],
        "primal_residual_normalized": float(np.linalg.norm(np.maximum(1.0 - coverage, 0.0))),
        "primal_residual_relative": 0.0,
        "consensus_residual": 0.0,
        "consensus_residual_relative": 0.0,
        "stationarity_residual": 0.0,
        "stationarity_residual_relative": 0.0,
        "min_x": metrics["min_x"],
        "simplex_violation": metrics["simplex_violation"],
        "iterations": int(iterations),
        "runtime_s": float(runtime_s),
        "messages": int(messages),
        "scalars_sent": int(scalars_sent),
        "converged": bool(converged),
        "lambda2": float(lambda2),
    }


def _scale_row(
    method: str,
    world: ResourceWorld,
    result: Any,
    runtime_s: float,
    iterations: int,
    messages: int,
    graph: Any,
    best_known: float,
    *,
    scalars: int = 0,
) -> dict[str, Any]:
    gap = math.nan
    if result.feasible and np.isfinite(best_known):
        gap = (result.objective - best_known) / max(abs(best_known), 1e-12)
    members = result.assignment[result.assignment >= 0]
    counts = np.bincount(members, minlength=world.n_loads) if members.size else np.zeros(world.n_loads, dtype=int)
    return {
        "world_hash": world.world_hash,
        "seed": world.seed,
        "n_robots": world.n_robots,
        "n_loads": world.n_loads,
        "method": method,
        "runtime_s": float(runtime_s),
        "iterations": int(iterations),
        "time_per_iteration_s": float(runtime_s / max(iterations, 1)),
        "messages": int(messages),
        "scalars_sent": int(scalars),
        "estimated_state_scalars": int(world.n_robots * world.n_loads if method == "MILP" else world.n_loads * world.requirements.shape[1] + graph.adjacency[0].sum()),
        "feasible": bool(result.feasible),
        "objective": float(result.objective),
        "gap_best_known": gap,
        "mean_robots_per_coalition": float(np.mean(counts)),
        "max_robots_per_coalition": int(np.max(counts)),
        "edges": int(graph.edges),
        "lambda2": float(graph.lambda2),
    }


def _final_dynamic_metrics(result: Any) -> dict[str, Any]:
    final = result.history.iloc[-1]
    return {
        "primal_residual": float(final["primal_residual"]),
        "primal_residual_normalized": float(final["primal_residual_normalized"]),
        "primal_residual_relative": float(final["primal_residual_relative"]),
        "consensus_residual": float(final["consensus_residual"]),
        "consensus_disagreement_residual": float(final["consensus_disagreement_residual"]),
        "consensus_residual_relative": float(final["consensus_residual_relative"]),
        "stationarity_residual": float(final["stationarity_residual"]),
        "fixed_point_residual": float(final["fixed_point_residual"]),
        "stationarity_residual_relative": float(final["stationarity_residual_relative"]),
        "stopping_primal_residual": float(final["stopping_primal_residual"]),
        "stopping_consensus_residual": float(final["stopping_consensus_residual"]),
        "stopping_stationarity_residual": float(final["stopping_stationarity_residual"]),
        "convergence_residual_mode": str(final["convergence_residual_mode"]),
        "primal_stationarity_residual": float(final["primal_stationarity_residual"]),
        "dual_stationarity_residual": float(final["dual_stationarity_residual"]),
        "min_x": float(final["min_x"]),
        "simplex_violation": float(final["simplex_violation"]),
    }


def _regularized_objective(x: np.ndarray, costs: np.ndarray, entropy_tau: float) -> float:
    finite = costs[np.isfinite(costs)]
    scale = max(float(np.max(finite)) if finite.size else 1.0, 1e-12)
    raw = float(np.sum(np.where(np.isfinite(costs), costs, 0.0) * x))
    return float(raw / scale - entropy_tau * allocation_entropy(x))


def _write_payload(output_dir: Path, name: str, payload: dict[str, pd.DataFrame]) -> None:
    for key, frame in payload.items():
        target_dir = output_dir / ("tables" if key == "summary" else "raw")
        frame.to_csv(target_dir / f"{name}_{key}.csv", index=False)


def _numeric_summary(frame: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    numeric = [column for column in frame.select_dtypes(include=[np.number, "bool"]).columns if column not in groups and column not in {"seed"}]
    if not numeric:
        return frame[groups].drop_duplicates().reset_index(drop=True)
    summary = frame.groupby(groups, dropna=False)[numeric].agg(["count", "mean", "median", "std"]).reset_index()
    # ``DataFrameGroupBy.agg`` creates a MultiIndex for the metric/statistic
    # pairs.  Leaving it intact produces duplicate column names in CSV (the
    # second header row is easy to lose when the table is consumed outside
    # pandas), which undermines the audit trail.  Use stable, explicit names
    # while keeping the grouping columns unchanged.
    if isinstance(summary.columns, pd.MultiIndex):
        summary.columns = [
            first if not second else f"{first}_{second}"
            for first, second in summary.columns.to_flat_index()
        ]
    return summary


def _integer_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for method, group in frame.groupby("method", sort=False):
        feasible_gaps = group.loc[group.feasible, "integer_gap_percent"].dropna()
        rows.append(
            {
                "method": method,
                "n": len(group),
                "feasible_n": int(group.feasible.sum()),
                "feasibility_rate": float(group.feasible.mean()),
                "gap_median_percent": float(feasible_gaps.median()) if not feasible_gaps.empty else math.nan,
                "gap_p95_percent": float(feasible_gaps.quantile(0.95)) if not feasible_gaps.empty else math.nan,
                "repairs_mean": float(group.repairs.mean()),
                "pruned_mean": float(group.pruned.mean()),
                "exchanges_mean": float(group.exchanges.mean()),
                "overassignment_mean": float(group.overassignment_l1.mean()),
                "gap_scope": "conditional_on_feasible_runs",
            }
        )
    return pd.DataFrame(rows)


def _finite_columns(frame: pd.DataFrame, columns: list[str]) -> bool:
    return bool(not frame.empty and np.isfinite(frame[columns].to_numpy(dtype=float)).all())


def _plot_e1(output_dir: Path, history: pd.DataFrame) -> None:
    if history.empty:
        return
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    mean = history.groupby(["method", "iteration"])["primal_residual_relative"].mean().reset_index()
    for method, group in mean.groupby("method"):
        ax.plot(group.iteration, np.maximum(group.primal_residual_relative, 1e-12), label=method)
    ax.set_yscale("log")
    ax.set_xlabel("Iteración digital")
    ax.set_ylabel("Residuo primal relativo")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    _save_figure(fig, output_dir / "figures" / "fig-sp1-e1-relaxed-convergence")


def _plot_e2(output_dir: Path, runs: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.0))
    for graph_case, group in runs.groupby("graph_case"):
        marker = "o" if bool(group.connected.all()) else "x"
        observed_rounds = group["R_epsilon"].fillna(group["iteration_limit"])
        axes[0].scatter(group.lambda2.mean(), observed_rounds.mean(), label=graph_case, marker=marker)
        axes[1].scatter(group.lambda2.mean(), group.scalars_sent.mean(), label=graph_case, marker=marker)
    axes[0].set(xlabel=r"Conectividad algebraica $\lambda_2$", ylabel=r"$R_\varepsilon$ (x = censura)")
    axes[1].set(xlabel=r"Conectividad algebraica $\lambda_2$", ylabel="Escalares transmitidos")
    for ax in axes:
        ax.grid(alpha=0.25)
    axes[1].legend(fontsize=7, frameon=False)
    fig.tight_layout()
    _save_figure(fig, output_dir / "figures" / "fig-sp1-e2-connectivity")


def _plot_e3(output_dir: Path, runs: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for integrator, group in runs.groupby("integrator"):
        means = group.groupby("step_factor")["primal_residual_relative"].mean()
        ax.plot(means.index, np.maximum(means.values, 1e-12), marker="o", label=integrator)
    ax.set_yscale("log")
    ax.set_xlabel(r"Factor de paso $\alpha/\alpha_{ref}$")
    ax.set_ylabel("Residuo primal relativo final")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    _save_figure(fig, output_dir / "figures" / "fig-sp1-e3-step")


def _plot_e4(output_dir: Path, summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.1))
    axes[0].bar(summary.method, summary.feasibility_rate, color="#2C7FB8")
    axes[0].set_ylim(0.0, 1.05)
    axes[0].set_ylabel("Tasa de factibilidad")
    axes[1].bar(summary.method, summary.gap_median_percent.fillna(0.0), color="#7FCDBB")
    axes[1].set_ylabel("Gap mediano condicional a factibilidad (%)")
    for ax in axes:
        ax.tick_params(axis="x", rotation=28, labelsize=8)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    _save_figure(fig, output_dir / "figures" / "fig-sp1-e4-integer-recovery")


def _plot_e5(output_dir: Path, runs: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.0))
    for method, group in runs.groupby("method"):
        mean = group.groupby("n_robots").mean(numeric_only=True)
        axes[0].plot(mean.index, mean.runtime_s, marker="o", label=method)
        axes[1].plot(mean.index, mean.messages, marker="o", label=method)
    axes[0].set(xlabel="Robots N", ylabel="Tiempo total (s)")
    axes[1].set(xlabel="Robots N", ylabel="Mensajes")
    for ax in axes:
        ax.grid(alpha=0.25)
    axes[0].legend(fontsize=8, frameon=False)
    fig.tight_layout()
    _save_figure(fig, output_dir / "figures" / "fig-sp1-e5-scale")


def _plot_e6(output_dir: Path, visual_results: list[tuple[ResourceWorld, ApproachResult, str]]) -> None:
    for world, result, scenario in visual_results:
        fig, ax = plt.subplots(figsize=(6.0, 6.0))
        for rectangle in result.obstacles:
            x0, x1, y0, y1 = rectangle
            ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, color="#666666", alpha=0.45))
        for robot, group in result.trajectories.groupby("robot_id"):
            ax.plot(group.x_m, group.y_m, linewidth=1.2, label=f"R{robot}")
        ax.scatter(world.load_positions_m[:, 0], world.load_positions_m[:, 1], marker="s", s=80, color="black", label="Cargas")
        assigned = result.trajectories.robot_id.unique().astype(int) if not result.trajectories.empty else np.asarray([], dtype=int)
        if assigned.size:
            ax.scatter(result.contact_targets[assigned, 0], result.contact_targets[assigned, 1], marker="x", color="#D62728", label="Contactos")
        ax.set(xlim=(0, 20), ylim=(0, 20), xlabel="x (m)", ylabel="y (m)", title=f"E6 — {scenario}")
        ax.set_aspect("equal")
        ax.grid(alpha=0.2)
        ax.legend(fontsize=7, frameon=False, ncol=2)
        fig.tight_layout()
        _save_figure(fig, output_dir / "figures" / f"fig-sp1-e6-{scenario}")


def _save_figure(fig: plt.Figure, path_without_suffix: Path) -> None:
    fig.savefig(path_without_suffix.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(path_without_suffix.with_suffix(".png"), dpi=180, bbox_inches="tight")
    plt.close(fig)


def _build_report(config: dict[str, Any], results: dict[str, dict[str, pd.DataFrame]], audit: dict[str, Any]) -> str:
    lines = [
        f"# {config['experiment_id']}",
        "",
        f"- Experimentos: `{', '.join(audit['experiments'])}`",
        f"- Auditoría: `{audit['status']}`",
        f"- Estado científico: `{audit['scientific_status']}`",
        f"- Nivel de evidencia: `{audit['evidence_level']}`",
        "",
    ]
    titles = {
        "e0": "E0 — Casos manuales",
        "e1": "E1 — Óptimo relajado",
        "e2": "E2 — Grafo de comunicación",
        "e3": "E3 — Paso discreto",
        "e4": "E4 — Recuperación entera",
        "e5": "E5 — Escalabilidad",
        "e6": "E6 — Aproximación uniciclo",
    }
    for name, payload in results.items():
        lines.extend([f"## {titles[name]}", ""])
        table = payload.get("summary", payload.get("runs", pd.DataFrame()))
        lines.extend(["```text", table.to_string(index=False, max_rows=30), "```", ""])
    lines.extend(["## Limitación de alcance", "", str(audit["not_claimed"]), ""])
    return "\n".join(lines)


def _build_manifest(
    config_path: Path,
    config: dict[str, Any],
    output_dir: Path,
    selected: list[str],
    audit: dict[str, Any],
) -> dict[str, Any]:
    artifacts: dict[str, str] = {}
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            relative = path.relative_to(output_dir).as_posix()
            if _artifact_belongs_to_selection(relative, selected):
                artifacts[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    commit = _git_value(["rev-parse", "HEAD"])
    dirty = bool(_git_value(["status", "--porcelain"]))
    return {
        "experiment_id": config["experiment_id"],
        "canonical_sp": "SP1",
        "protocol_family": config["protocol_family"],
        "experiments": selected,
        "config_path": str(config_path),
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "output_dir": str(output_dir),
        "audit_status": audit["status"],
        "scientific_status": audit["scientific_status"],
        "evidence_level": audit["evidence_level"],
        "git_commit": commit,
        "git_dirty": dirty,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "artifact_sha256": artifacts,
    }


def _artifact_belongs_to_selection(relative: str, selected: list[str]) -> bool:
    if relative in {"audit.json", "config_snapshot.yaml", "report.md"}:
        return True
    name = Path(relative).name
    if relative.startswith(("raw/", "processed/", "tables/")):
        return any(name.startswith(f"{experiment}_") for experiment in selected)
    if relative.startswith("figures/"):
        return any(f"-{experiment}-" in name for experiment in selected)
    return False


def _scientific_acceptance(
    results: dict[str, dict[str, pd.DataFrame]],
    checks: dict[str, bool],
) -> dict[str, bool]:
    acceptance: dict[str, bool] = {
        "e0_small_case_alignment": bool(
            checks.get("e0_rep_c_converged", False)
            and checks.get("e0_rep_d_converged", False)
            and checks.get("e0_rep_c_matches_regularized_lp", False)
            and checks.get("e0_rep_d_matches_rep_c", False)
        ),
        "confirmatory_campaign_completed": False,
        "theorems_1_to_5_validated": False,
    }
    if "e1" in results:
        runs = results["e1"]["runs"]
        population = runs[runs.method.str.startswith("Rep")]
        acceptance["e1_all_population_runs_converged"] = bool(not population.empty and population.converged.all())
        acceptance["e1_all_population_runs_lp_comparable"] = bool(
            not population.empty and population.comparable_to_lp.all()
        )
        acceptance["e1_complete_relaxed_validation"] = bool(
            acceptance["e1_all_population_runs_converged"]
            and acceptance["e1_all_population_runs_lp_comparable"]
        )
    if "e2" in results:
        runs = results["e2"]["runs"]
        connected = runs[runs.assumption_class == "theorem_connected"]
        acceptance["e2_all_connected_runs_converged"] = bool(not connected.empty and connected.converged.all())
    if "e3" in results:
        runs = results["e3"]["runs"]
        acceptance["e3_all_integrator_runs_converged"] = bool(not runs.empty and runs.converged.all())
    return acceptance


def _git_value(arguments: list[str]) -> str:
    try:
        return subprocess.run(["git", *arguments], check=False, capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def _validate_config(config: dict[str, Any]) -> None:
    required = {
        "experiment_id",
        "protocol_family",
        "output_dir",
        "cost_weights",
        "dynamics",
        "oracle_time_limit_s",
        *EXPERIMENTS,
    }
    missing = required - set(config)
    if missing:
        raise ValueError(f"Missing SP1 validation configuration keys: {sorted(missing)}")


__all__ = ["EXPERIMENTS", "execute", "run_validation_config"]

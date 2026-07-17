"""Canonical SP8 scale and imperfect-network experiment.

The experiment extends the SP7 route game without introducing a new physical
plant.  Coalitions exchange versioned route intentions on a static undirected
graph.  Radio range, bounded discrete delay and independent packet loss are
varied independently and jointly.  The model measures logical coordination,
not continuous collision avoidance or a real network stack.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy import stats
import yaml

from viu_mrob_tfm.sp8.theory import (
    RouteResources,
    asynchronous_visible_better_response,
    exhaustive_global_oracle,
    global_conflict_pairs,
    missed_conflict_pairs,
    network_potential,
    profile_space_size,
    retransmission_failure_probability,
    social_cost,
    verify_exact_network_potential,
    visible_conflict_pairs,
)


METHODS = (
    "periodic_versioned_local",
    "event_driven_local",
    "perfect_information_response",
    "random_static",
    "central_exhaustive_oracle",
)

METHOD_LABELS = {
    "periodic_versioned_local": "Local periódico versionado",
    "event_driven_local": "Local solo por evento",
    "perfect_information_response": "Mejor respuesta con información perfecta",
    "random_static": "Perfil inicial aleatorio",
    "central_exhaustive_oracle": "Oráculo exhaustivo restringido",
}

REGIME_LABELS = {
    "nominal": "Nominal",
    "sparse_radio": "Radio reducido",
    "bounded_delay": "Retardo",
    "independent_loss": "Pérdida",
    "harsh_combined": "Combinado adverso",
}


@dataclass(frozen=True, slots=True)
class NetworkWorld:
    regime: str
    n_coalitions: int
    n_robots: int
    seed: int
    positions: np.ndarray
    adjacency: np.ndarray
    base_costs: np.ndarray
    route_resources: RouteResources
    initial_profile: np.ndarray
    penalty: float
    communication_radius: float
    max_delay_events: int
    packet_loss: float
    horizon_events: int
    message_bytes: int
    instance_hash: str
    world_hash: str


@dataclass(frozen=True, slots=True)
class ProtocolOutcome:
    profile: np.ndarray
    accepted_changes: int
    messages_attempted: int
    messages_delivered: int
    messages_dropped: int
    events: int
    stable: bool
    runtime_ms: float
    protocol_state_bytes: int
    mean_version_lag: float
    max_version_lag: int
    missing_view_fraction: float


def run_sp8_config(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path)
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    experiment_id = str(config["experiment_id"])
    output_dir = Path(config.get("output_dir", f"results/processed/sp8/{experiment_id}"))
    tables_dir = output_dir / "tables"
    figures_dir = output_dir / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    coalition_counts = [int(value) for value in config["coalition_counts"]]
    regimes = {str(key): dict(value) for key, value in config["network_regimes"].items()}
    seeds = _expand_seeds(config["seeds"])
    methods = [str(value) for value in config.get("methods", METHODS)]
    if tuple(methods) != METHODS:
        raise ValueError(f"Canonical SP8 requires methods in this order: {METHODS}")
    oracle_cap = int(config.get("oracle_max_profiles", 4096))
    penalty = float(config.get("penalty", 2.0))
    horizon_sweeps = int(config.get("horizon_sweeps", 20))
    message_bytes = int(config.get("message_bytes", 32))

    rows: list[dict[str, Any]] = []
    theory_rows: list[dict[str, Any]] = []
    for n_coalitions in coalition_counts:
        for seed in seeds:
            oracle_cache: dict[str, Any] | None = None
            for regime, regime_params in regimes.items():
                world = generate_world(
                    regime,
                    regime_params,
                    n_coalitions,
                    seed,
                    penalty=penalty,
                    horizon_sweeps=horizon_sweeps,
                    message_bytes=message_bytes,
                )
                theory_rows.append(audit_world_theory(world, oracle_cap=oracle_cap))
                if oracle_cache is None:
                    started = perf_counter()
                    oracle = exhaustive_global_oracle(
                        world.base_costs,
                        world.route_resources,
                        world.penalty,
                        max_profiles=oracle_cap,
                    )
                    oracle_cache = {
                        "result": oracle,
                        "runtime_ms": 1000.0 * (perf_counter() - started),
                    }
                for method in methods:
                    rows.append(simulate_method(world, method, oracle_cache))

    runs = pd.DataFrame(rows)
    theory = pd.DataFrame(theory_rows)
    summary = summarize_runs(runs)
    hypotheses = evaluate_hypotheses(runs)
    audit = build_audit(
        config,
        runs,
        theory,
        coalition_counts=coalition_counts,
        regimes=list(regimes),
        seeds=seeds,
        methods=methods,
        oracle_cap=oracle_cap,
    )

    runs.to_csv(tables_dir / "runs.csv", index=False)
    theory.to_csv(tables_dir / "theory_checks.csv", index=False)
    summary.to_csv(tables_dir / "summary.csv", index=False)
    hypotheses.to_csv(tables_dir / "hypotheses.csv", index=False)
    _write_latex_tables(output_dir, runs, summary, hypotheses, theory)
    _plot_results(output_dir, runs, summary)
    (output_dir / "audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "report.md").write_text(
        _report(experiment_id, runs, summary, hypotheses, audit), encoding="utf-8"
    )

    manifest = {
        "experiment_id": experiment_id,
        "protocol_family": str(config.get("protocol_family", "sp8_visible_route_network_v1")),
        "config_path": str(path),
        "output_dir": str(output_dir),
        "coalition_counts": coalition_counts,
        "robot_counts": [2 * value for value in coalition_counts],
        "network_regimes": list(regimes),
        "seeds": seeds,
        "methods": methods,
        "worlds": int(len(theory)),
        "runs": int(len(runs)),
        "oracle_max_profiles": oracle_cap,
        "oracle_certified_worlds": int(theory["oracle_certified"].sum()),
        "evidence_level": "C",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "gpu_used": False,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest


def generate_world(
    regime: str,
    regime_params: dict[str, Any],
    n_coalitions: int,
    seed: int,
    *,
    penalty: float = 2.0,
    horizon_sweeps: int = 20,
    message_bytes: int = 32,
) -> NetworkWorld:
    n = int(n_coalitions)
    if n < 2:
        raise ValueError("SP8 requires at least two coalitions.")
    stable_offset = int.from_bytes(hashlib.sha256(str(regime).encode("utf-8")).digest()[:4], "little")
    instance_rng = np.random.default_rng(int(seed) + 4099 * n)
    network_rng = np.random.default_rng(int(seed) + 4099 * n + stable_offset)
    positions = instance_rng.uniform(0.0, 1.0, size=(n, 2))
    permutation = instance_rng.permutation(n)
    if np.array_equal(permutation, np.arange(n)) and n > 2:
        permutation = np.roll(permutation, 1)
    route_resources: RouteResources = tuple(
        (
            frozenset({f"z{agent}"}),
            frozenset({f"z{int(permutation[agent])}"}),
        )
        for agent in range(n)
    )
    route_zero = instance_rng.uniform(0.05, 0.65, size=n)
    route_one = np.clip(route_zero + instance_rng.normal(0.08, 0.20, size=n), 0.02, 0.98)
    base_costs = np.column_stack([route_zero, route_one])
    initial_profile = instance_rng.integers(0, 2, size=n, dtype=int)

    radius = float(regime_params.get("radius", 2.0))
    distances = np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)
    adjacency = (distances <= radius) & (~np.eye(n, dtype=bool))
    if bool(regime_params.get("random_edge_thinning", False)):
        keep = network_rng.random((n, n)) <= float(regime_params.get("edge_keep_probability", 1.0))
        keep = np.triu(keep, 1)
        keep = keep | keep.T
        adjacency &= keep
    max_delay = int(regime_params.get("max_delay_events", 0))
    packet_loss = float(regime_params.get("packet_loss", 0.0))
    if max_delay < 0 or not 0.0 <= packet_loss <= 1.0:
        raise ValueError("Invalid SP8 network regime.")

    instance_payload = {
        "n_coalitions": n,
        "seed": int(seed),
        "positions": positions.round(12).tolist(),
        "permutation": permutation.tolist(),
        "base_costs": base_costs.round(12).tolist(),
        "initial_profile": initial_profile.tolist(),
    }
    instance_hash = hashlib.sha256(
        json.dumps(instance_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    world_payload = {
        **instance_payload,
        "regime": str(regime),
        "adjacency": adjacency.astype(int).tolist(),
        "max_delay_events": max_delay,
        "packet_loss": packet_loss,
    }
    world_hash = hashlib.sha256(
        json.dumps(world_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return NetworkWorld(
        regime=str(regime),
        n_coalitions=n,
        n_robots=2 * n,
        seed=int(seed),
        positions=positions,
        adjacency=adjacency,
        base_costs=base_costs,
        route_resources=route_resources,
        initial_profile=initial_profile,
        penalty=float(penalty),
        communication_radius=radius,
        max_delay_events=max_delay,
        packet_loss=packet_loss,
        horizon_events=int(horizon_sweeps) * n,
        message_bytes=int(message_bytes),
        instance_hash=instance_hash,
        world_hash=world_hash,
    )


def _graph_fields(adjacency: np.ndarray) -> dict[str, Any]:
    graph = np.asarray(adjacency, dtype=bool)
    n = len(graph)
    edges = int(np.sum(graph) // 2)
    degrees = np.sum(graph, axis=1).astype(int)
    visited: set[int] = set()
    components = 0
    for root in range(n):
        if root in visited:
            continue
        components += 1
        stack = [root]
        visited.add(root)
        while stack:
            current = stack.pop()
            for neighbor in np.flatnonzero(graph[current]):
                neighbor = int(neighbor)
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
    laplacian = np.diag(degrees.astype(float)) - graph.astype(float)
    eigenvalues = np.linalg.eigvalsh(laplacian) if n else np.asarray([0.0])
    lambda2 = float(eigenvalues[1]) if n > 1 else 0.0
    return {
        "communication_edges": edges,
        "mean_degree": float(np.mean(degrees)) if n else 0.0,
        "max_degree": int(np.max(degrees)) if n else 0,
        "components": components,
        "connected": components == 1,
        "algebraic_connectivity": lambda2,
    }


def audit_world_theory(world: NetworkWorld, *, oracle_cap: int) -> dict[str, Any]:
    graph = _graph_fields(world.adjacency)
    profile_space = profile_space_size(world.route_resources)
    exact_checked = world.n_coalitions <= 8
    exact_identity = (
        verify_exact_network_potential(
            world.base_costs,
            world.route_resources,
            world.adjacency,
            world.penalty,
        )
        if exact_checked
        else True
    )
    result = asynchronous_visible_better_response(
        world.base_costs,
        world.route_resources,
        world.adjacency,
        world.penalty,
        initial_profile=world.initial_profile,
        seed=world.seed + 31,
    )
    guaranteed_profile_zero = np.zeros(world.n_coalitions, dtype=int)
    guaranteed_profile_one = np.ones(world.n_coalitions, dtype=int)
    return {
        "world_hash": world.world_hash,
        "instance_hash": world.instance_hash,
        "regime": world.regime,
        "n_coalitions": world.n_coalitions,
        "n_robots": world.n_robots,
        "seed": world.seed,
        **graph,
        "profile_space": profile_space,
        "oracle_certified": profile_space <= int(oracle_cap),
        "exact_identity_exhaustively_checked": exact_checked,
        "exact_network_potential_verified": exact_identity,
        "strict_potential_monotonicity": bool(np.all(np.diff(result.potential_trace) > 0.0)),
        "better_response_visible_nash": bool(result.visible_nash),
        "strict_moves": result.strict_moves,
        "finite_move_bound": profile_space - 1,
        "catalogue_has_conflict_free_profile": bool(
            global_conflict_pairs(guaranteed_profile_zero, world.route_resources) == 0
            and global_conflict_pairs(guaranteed_profile_one, world.route_resources) == 0
        ),
        "single_message_failure_probability": retransmission_failure_probability(
            world.packet_loss, 1
        ),
        "failure_after_five_retransmissions": retransmission_failure_probability(
            world.packet_loss, 5
        ),
    }


def _send_message(
    queue: list[tuple[int, int, int, int, int]],
    *,
    event: int,
    sender: int,
    receiver: int,
    version: int,
    route: int,
    max_delay: int,
    packet_loss: float,
    rng: np.random.Generator,
) -> bool:
    if rng.random() < float(packet_loss):
        return False
    delay = int(rng.integers(0, int(max_delay) + 1))
    queue.append((event + delay + 1, receiver, sender, version, route))
    return True


def simulate_local_protocol(world: NetworkWorld, *, periodic: bool) -> ProtocolOutcome:
    started = perf_counter()
    n = world.n_coalitions
    profile = world.initial_profile.copy()
    versions = np.zeros(n, dtype=int)
    views = np.full((n, n), -1, dtype=int)
    view_versions = np.full((n, n), -1, dtype=int)
    np.fill_diagonal(views, profile)
    np.fill_diagonal(view_versions, versions)
    queue: list[tuple[int, int, int, int, int]] = []
    rng = np.random.default_rng(world.seed + (911 if periodic else 353) + int.from_bytes(world.regime.encode("utf-8")[:2], "little"))
    attempted = delivered = dropped = accepted = 0
    last_change = -world.horizon_events

    def broadcast(sender: int, event: int) -> None:
        nonlocal attempted, delivered, dropped
        for receiver in np.flatnonzero(world.adjacency[sender]):
            attempted += 1
            ok = _send_message(
                queue,
                event=event,
                sender=sender,
                receiver=int(receiver),
                version=int(versions[sender]),
                route=int(profile[sender]),
                max_delay=world.max_delay_events,
                packet_loss=world.packet_loss,
                rng=rng,
            )
            delivered += int(ok)
            dropped += int(not ok)

    for sender in range(n):
        broadcast(sender, -1)

    for event in range(world.horizon_events):
        pending = []
        for delivery_event, receiver, sender, version, route in queue:
            if delivery_event <= event:
                if version >= int(view_versions[receiver, sender]):
                    view_versions[receiver, sender] = version
                    views[receiver, sender] = route
            else:
                pending.append((delivery_event, receiver, sender, version, route))
        queue = pending

        agent = event % n
        old_route = int(profile[agent])

        def perceived_utility(route: int) -> float:
            conflicts = 0
            for other in np.flatnonzero(world.adjacency[agent]):
                other = int(other)
                observed = int(views[agent, other])
                if observed < 0:
                    continue
                conflicts += len(
                    world.route_resources[agent][route]
                    & world.route_resources[other][observed]
                )
            return -float(world.base_costs[agent, route]) - world.penalty * conflicts

        utilities = [perceived_utility(route) for route in range(2)]
        best_route = int(max(range(2), key=lambda route: (utilities[route], -route)))
        changed = utilities[best_route] > utilities[old_route] + 1e-10
        if changed:
            profile[agent] = best_route
            versions[agent] += 1
            views[agent, agent] = best_route
            view_versions[agent, agent] = versions[agent]
            accepted += 1
            last_change = event
            broadcast(agent, event)
        elif periodic:
            broadcast(agent, event)

    graph = _graph_fields(world.adjacency)
    state_bytes = int((2 * graph["communication_edges"] + n) * 8)
    edge_receivers, edge_senders = np.nonzero(world.adjacency)
    if edge_receivers.size:
        observed_versions = view_versions[edge_receivers, edge_senders]
        current_versions = versions[edge_senders]
        missing = observed_versions < 0
        lags = np.where(missing, current_versions + 1, current_versions - observed_versions)
        mean_version_lag = float(np.mean(lags))
        max_version_lag = int(np.max(lags))
        missing_view_fraction = float(np.mean(missing))
    else:
        mean_version_lag = 0.0
        max_version_lag = 0
        missing_view_fraction = 0.0
    return ProtocolOutcome(
        profile=profile,
        accepted_changes=accepted,
        messages_attempted=attempted,
        messages_delivered=delivered,
        messages_dropped=dropped,
        events=world.horizon_events,
        stable=(world.horizon_events - last_change) >= 2 * n,
        runtime_ms=1000.0 * (perf_counter() - started),
        protocol_state_bytes=state_bytes,
        mean_version_lag=mean_version_lag,
        max_version_lag=max_version_lag,
        missing_view_fraction=missing_view_fraction,
    )


def _conflict_agent_count(profile: np.ndarray, route_resources: RouteResources) -> int:
    agents: set[int] = set()
    for i in range(len(profile)):
        for j in range(i + 1, len(profile)):
            if route_resources[i][int(profile[i])] & route_resources[j][int(profile[j])]:
                agents.update((i, j))
    return len(agents)


def simulate_method(
    world: NetworkWorld,
    method: str,
    oracle_cache: dict[str, Any],
) -> dict[str, Any]:
    graph = _graph_fields(world.adjacency)
    oracle = oracle_cache["result"]
    run_status = "executed"
    if method == "periodic_versioned_local":
        outcome = simulate_local_protocol(world, periodic=True)
    elif method == "event_driven_local":
        outcome = simulate_local_protocol(world, periodic=False)
    elif method == "perfect_information_response":
        started = perf_counter()
        complete = np.ones((world.n_coalitions, world.n_coalitions), dtype=bool)
        np.fill_diagonal(complete, False)
        response = asynchronous_visible_better_response(
            world.base_costs,
            world.route_resources,
            complete,
            world.penalty,
            initial_profile=world.initial_profile,
            seed=world.seed + 101,
        )
        outcome = ProtocolOutcome(
            profile=response.profile,
            accepted_changes=response.strict_moves,
            messages_attempted=0,
            messages_delivered=0,
            messages_dropped=0,
            events=response.activations,
            stable=True,
            runtime_ms=1000.0 * (perf_counter() - started),
            protocol_state_bytes=int(world.n_coalitions**2 * 8),
            mean_version_lag=0.0,
            max_version_lag=0,
            missing_view_fraction=0.0,
        )
    elif method == "random_static":
        outcome = ProtocolOutcome(
            profile=world.initial_profile.copy(),
            accepted_changes=0,
            messages_attempted=0,
            messages_delivered=0,
            messages_dropped=0,
            events=0,
            stable=True,
            runtime_ms=0.0,
            protocol_state_bytes=int(world.n_coalitions * 8),
            mean_version_lag=0.0,
            max_version_lag=0,
            missing_view_fraction=0.0,
        )
    elif method == "central_exhaustive_oracle":
        if oracle.certified and oracle.profile is not None:
            profile = oracle.profile.copy()
        else:
            profile = world.initial_profile.copy()
            run_status = "not_certified_profile_cap"
        outcome = ProtocolOutcome(
            profile=profile,
            accepted_changes=0,
            messages_attempted=0,
            messages_delivered=0,
            messages_dropped=0,
            events=oracle.evaluated_profiles,
            stable=bool(oracle.certified),
            runtime_ms=float(oracle_cache["runtime_ms"]),
            protocol_state_bytes=int(oracle.evaluated_profiles * 8),
            mean_version_lag=0.0,
            max_version_lag=0,
            missing_view_fraction=0.0,
        )
    else:
        raise ValueError(f"Unknown SP8 method: {method}")

    conflicts = global_conflict_pairs(outcome.profile, world.route_resources)
    visible = visible_conflict_pairs(
        outcome.profile, world.route_resources, world.adjacency
    )
    missed = missed_conflict_pairs(
        outcome.profile, world.route_resources, world.adjacency
    )
    conflict_agents = _conflict_agent_count(outcome.profile, world.route_resources)
    cost = social_cost(
        outcome.profile, world.base_costs, world.route_resources, world.penalty
    )
    gap = (
        (cost - float(oracle.social_cost)) / max(abs(float(oracle.social_cost)), 1e-12)
        if oracle.certified and np.isfinite(oracle.social_cost)
        else float("nan")
    )
    sweeps = max(outcome.events / world.n_coalitions, 1.0)
    return {
        "world_hash": world.world_hash,
        "instance_hash": world.instance_hash,
        "regime": world.regime,
        "regime_label": REGIME_LABELS.get(world.regime, world.regime),
        "n_coalitions": world.n_coalitions,
        "n_loads": world.n_coalitions,
        "n_robots": world.n_robots,
        "seed": world.seed,
        "method": method,
        "method_label": METHOD_LABELS[method],
        "run_status": run_status,
        "communication_radius": world.communication_radius,
        "max_delay_events": world.max_delay_events,
        "packet_loss": world.packet_loss,
        **graph,
        "global_conflict_pairs": conflicts,
        "visible_conflict_pairs": visible,
        "missed_conflict_pairs": missed,
        "conflict_free": int(conflicts == 0),
        "coordinated_fraction": 1.0 - conflict_agents / world.n_coalitions,
        "logical_throughput_per_sweep": (world.n_coalitions - conflict_agents) / sweeps,
        "social_cost": cost,
        "gap_vs_certified_oracle": gap,
        "accepted_changes": outcome.accepted_changes,
        "events": outcome.events,
        "stable": int(outcome.stable),
        "messages_attempted": outcome.messages_attempted,
        "messages_delivered": outcome.messages_delivered,
        "messages_dropped": outcome.messages_dropped,
        "messages_per_agent": outcome.messages_attempted / world.n_coalitions,
        "bytes_attempted": outcome.messages_attempted * world.message_bytes,
        "bytes_per_agent": outcome.messages_attempted * world.message_bytes / world.n_coalitions,
        "runtime_ms": outcome.runtime_ms,
        "runtime_ms_per_agent": outcome.runtime_ms / world.n_coalitions,
        "protocol_state_bytes": outcome.protocol_state_bytes,
        "state_bytes_per_agent": outcome.protocol_state_bytes / world.n_coalitions,
        "mean_version_lag": outcome.mean_version_lag,
        "max_version_lag": outcome.max_version_lag,
        "missing_view_fraction": outcome.missing_view_fraction,
        "oracle_certified": int(oracle.certified),
        "oracle_profile_space": oracle.profile_space,
        "oracle_profiles_evaluated": oracle.evaluated_profiles,
    }


def summarize_runs(runs: pd.DataFrame) -> pd.DataFrame:
    executed = runs[runs["run_status"] == "executed"].copy()
    metrics = [
        "conflict_free",
        "global_conflict_pairs",
        "missed_conflict_pairs",
        "coordinated_fraction",
        "logical_throughput_per_sweep",
        "gap_vs_certified_oracle",
        "messages_per_agent",
        "bytes_per_agent",
        "runtime_ms",
        "runtime_ms_per_agent",
        "state_bytes_per_agent",
        "mean_version_lag",
        "max_version_lag",
        "missing_view_fraction",
    ]
    rows: list[dict[str, Any]] = []
    for keys, group in executed.groupby(["regime", "n_coalitions", "method"], sort=True):
        regime, n_coalitions, method = keys
        row: dict[str, Any] = {
            "regime": regime,
            "n_coalitions": int(n_coalitions),
            "n_robots": 2 * int(n_coalitions),
            "method": method,
            "n": int(len(group)),
        }
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values)) if values.size else float("nan")
            row[f"{metric}_median"] = float(np.median(values)) if values.size else float("nan")
            row[f"{metric}_std"] = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def _paired_frame(
    runs: pd.DataFrame,
    method_a: str,
    method_b: str,
    metric: str,
    *,
    regimes: list[str] | None = None,
) -> pd.DataFrame:
    selected = runs[runs["run_status"] == "executed"].copy()
    if regimes is not None:
        selected = selected[selected["regime"].isin(regimes)]
    pivot = selected[selected["method"].isin([method_a, method_b])].pivot_table(
        index=["instance_hash", "world_hash", "regime", "n_coalitions", "seed"],
        columns="method",
        values=metric,
        aggfunc="first",
    )
    return pivot.dropna(subset=[method_a, method_b])


def _bootstrap_mean_ci(values: np.ndarray, *, seed: int) -> tuple[float, float]:
    data = np.asarray(values, dtype=float)
    if data.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(int(seed))
    means = np.empty(3000, dtype=float)
    for index in range(len(means)):
        means[index] = float(np.mean(rng.choice(data, size=data.size, replace=True)))
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


def _holm(rows: list[dict[str, Any]]) -> None:
    order = sorted(range(len(rows)), key=lambda index: float(rows[index]["p_value_raw"]))
    running = 0.0
    m = len(rows)
    for rank, index in enumerate(order):
        adjusted = min(1.0, (m - rank) * float(rows[index]["p_value_raw"]))
        running = max(running, adjusted)
        rows[index]["p_value_holm"] = running
        rows[index]["reject_holm"] = bool(running < 0.05)


def evaluate_hypotheses(runs: pd.DataFrame) -> pd.DataFrame:
    degraded = sorted(str(value) for value in runs["regime"].unique() if str(value) != "nominal")
    rows: list[dict[str, Any]] = []

    paired = _paired_frame(
        runs,
        "periodic_versioned_local",
        "event_driven_local",
        "conflict_free",
        regimes=degraded,
    )
    pair_diffs = (
        paired["periodic_versioned_local"] - paired["event_driven_local"]
    ).to_numpy(dtype=float)
    diffs = (
        paired.assign(difference=pair_diffs)
        .reset_index()
        .groupby(["instance_hash", "n_coalitions", "seed"], sort=True)["difference"]
        .mean()
        .to_numpy(dtype=float)
    )
    favorable = int(np.sum((paired["periodic_versioned_local"] == 1) & (paired["event_driven_local"] == 0)))
    adverse = int(np.sum((paired["periodic_versioned_local"] == 0) & (paired["event_driven_local"] == 1)))
    p_value = float(stats.wilcoxon(diffs).pvalue) if np.any(diffs != 0) else 1.0
    low, high = _bootstrap_mean_ci(diffs, seed=88001)
    rows.append({
        "id": "H8.1",
        "metric": "conflict_free",
        "comparison": "periodic_versioned_local - event_driven_local",
        "n": len(diffs),
        "n_regime_pairs": len(pair_diffs),
        "effect": float(np.mean(diffs)),
        "ci95_low": low,
        "ci95_high": high,
        "p_value_raw": p_value,
        "test": "Wilcoxon bilateral sobre medias por instancia",
        "favorable_discordances": favorable,
        "adverse_discordances": adverse,
    })

    paired = _paired_frame(
        runs,
        "periodic_versioned_local",
        "perfect_information_response",
        "global_conflict_pairs",
        regimes=degraded,
    )
    pair_diffs = (
        paired["periodic_versioned_local"] - paired["perfect_information_response"]
    ).to_numpy(dtype=float)
    diffs = (
        paired.assign(difference=pair_diffs)
        .reset_index()
        .groupby(["instance_hash", "n_coalitions", "seed"], sort=True)["difference"]
        .mean()
        .to_numpy(dtype=float)
    )
    p_value = float(stats.wilcoxon(diffs, alternative="greater").pvalue) if np.any(diffs != 0) else 1.0
    low, high = _bootstrap_mean_ci(diffs, seed=88002)
    rows.append({
        "id": "H8.2",
        "metric": "global_conflict_pairs",
        "comparison": "periodic_versioned_local - perfect_information_response",
        "n": len(diffs),
        "n_regime_pairs": len(pair_diffs),
        "effect": float(np.mean(diffs)),
        "ci95_low": low,
        "ci95_high": high,
        "p_value_raw": p_value,
        "test": "Wilcoxon unilateral sobre medias por instancia",
        "favorable_discordances": float("nan"),
        "adverse_discordances": float("nan"),
    })

    paired = _paired_frame(
        runs,
        "periodic_versioned_local",
        "event_driven_local",
        "messages_per_agent",
        regimes=degraded,
    )
    pair_diffs = (
        paired["periodic_versioned_local"] - paired["event_driven_local"]
    ).to_numpy(dtype=float)
    diffs = (
        paired.assign(difference=pair_diffs)
        .reset_index()
        .groupby(["instance_hash", "n_coalitions", "seed"], sort=True)["difference"]
        .mean()
        .to_numpy(dtype=float)
    )
    p_value = float(stats.wilcoxon(diffs, alternative="greater").pvalue) if np.any(diffs != 0) else 1.0
    low, high = _bootstrap_mean_ci(diffs, seed=88003)
    rows.append({
        "id": "H8.3",
        "metric": "messages_per_agent",
        "comparison": "periodic_versioned_local - event_driven_local",
        "n": len(diffs),
        "n_regime_pairs": len(pair_diffs),
        "effect": float(np.mean(diffs)),
        "ci95_low": low,
        "ci95_high": high,
        "p_value_raw": p_value,
        "test": "Wilcoxon unilateral sobre medias por instancia",
        "favorable_discordances": float("nan"),
        "adverse_discordances": float("nan"),
    })
    _holm(rows)
    return pd.DataFrame(rows)


def build_audit(
    config: dict[str, Any],
    runs: pd.DataFrame,
    theory: pd.DataFrame,
    *,
    coalition_counts: list[int],
    regimes: list[str],
    seeds: list[int],
    methods: list[str],
    oracle_cap: int,
) -> dict[str, Any]:
    expected_worlds = len(coalition_counts) * len(regimes) * len(seeds)
    expected_runs = expected_worlds * len(methods)
    method_counts = runs.groupby("world_hash")["method"].nunique()
    executed = runs[runs["run_status"] == "executed"]
    finite_columns = [
        "global_conflict_pairs",
        "coordinated_fraction",
        "messages_per_agent",
        "runtime_ms",
        "state_bytes_per_agent",
    ]
    checks = {
        "world_count": len(theory) == expected_worlds,
        "run_count": len(runs) == expected_runs,
        "paired_methods": bool((method_counts == len(methods)).all()),
        "world_hash_unique": theory["world_hash"].nunique() == expected_worlds,
        "instance_hash_shared_across_regimes": bool(
            (theory.groupby(["n_coalitions", "seed"])["instance_hash"].nunique() == 1).all()
        ),
        "finite_executed_metrics": bool(
            np.isfinite(executed[finite_columns].to_numpy(dtype=float)).all()
        ),
        "exact_network_potential": bool(theory["exact_network_potential_verified"].all()),
        "strict_potential_monotonicity": bool(theory["strict_potential_monotonicity"].all()),
        "better_response_visible_nash": bool(theory["better_response_visible_nash"].all()),
        "finite_profile_move_bound": bool((theory["strict_moves"] <= theory["finite_move_bound"]).all()),
        "conflict_free_catalogue": bool(theory["catalogue_has_conflict_free_profile"].all()),
        "oracle_cap_respected": bool(
            ((theory["profile_space"] <= oracle_cap) == theory["oracle_certified"]).all()
        ),
        "no_fabricated_oracle_gap": bool(
            runs.loc[runs["oracle_certified"] == 0, "gap_vs_certified_oracle"].isna().all()
        ),
        "message_accounting": bool(
            (runs["messages_attempted"] == runs["messages_delivered"] + runs["messages_dropped"]).all()
        ),
        "probability_bound_valid": bool(
            (theory["failure_after_five_retransmissions"] <= theory["single_message_failure_probability"] + 1e-12).all()
        ),
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "evidence_level": "C",
        "worlds": int(len(theory)),
        "runs": int(len(runs)),
        "executed_runs": int(len(executed)),
        "oracle_certified_worlds": int(theory["oracle_certified"].sum()),
        "model_scope": "finite binary route game on a static undirected communication graph with sampled delay and independent packet loss",
        "not_claimed": "No continuous physical safety, real radio stack, correlated loss, switching-topology convergence, global MAPF optimality, hardware scaling or energy measurement is claimed.",
        "historical_campaign_used": False,
        "config_protocol": str(config.get("protocol_family", "sp8_visible_route_network_v1")),
    }


def _write_latex_tables(
    output_dir: Path,
    runs: pd.DataFrame,
    summary: pd.DataFrame,
    hypotheses: pd.DataFrame,
    theory: pd.DataFrame,
) -> None:
    tables = output_dir / "tables"
    proposed = runs[
        (runs["method"] == "periodic_versioned_local") & (runs["run_status"] == "executed")
    ]
    naive = runs[
        (runs["method"] == "event_driven_local") & (runs["run_status"] == "executed")
    ]
    perfect = runs[
        (runs["method"] == "perfect_information_response") & (runs["run_status"] == "executed")
    ]
    degraded = proposed[proposed["regime"] != "nominal"]
    h1 = hypotheses[hypotheses["id"] == "H8.1"].iloc[0]
    h2 = hypotheses[hypotheses["id"] == "H8.2"].iloc[0]
    h3 = hypotheses[hypotheses["id"] == "H8.3"].iloc[0]
    macros = "\n".join([
        f"\\newcommand{{\\SPEightWorlds}}{{{len(theory)}}}",
        f"\\newcommand{{\\SPEightRecords}}{{{len(runs)}}}",
        f"\\newcommand{{\\SPEightExecutedRuns}}{{{int((runs['run_status'] == 'executed').sum())}}}",
        f"\\newcommand{{\\SPEightCertified}}{{{int(theory['oracle_certified'].sum())}}}",
        f"\\newcommand{{\\SPEightProposedSuccess}}{{{proposed['conflict_free'].mean():.3f}}}",
        f"\\newcommand{{\\SPEightDegradedSuccess}}{{{degraded['conflict_free'].mean():.3f}}}",
        f"\\newcommand{{\\SPEightNaiveSuccess}}{{{naive['conflict_free'].mean():.3f}}}",
        f"\\newcommand{{\\SPEightPerfectSuccess}}{{{perfect['conflict_free'].mean():.3f}}}",
        f"\\newcommand{{\\SPEightHOneEffect}}{{{float(h1['effect']):.3f}}}",
        f"\\newcommand{{\\SPEightHTwoEffect}}{{{float(h2['effect']):.3f}}}",
        f"\\newcommand{{\\SPEightHThreeEffect}}{{{float(h3['effect']):.1f}}}",
        f"\\newcommand{{\\SPEightMaxScale}}{{{int(theory['n_coalitions'].max())}}}",
        f"\\newcommand{{\\SPEightMaxRobots}}{{{int(theory['n_robots'].max())}}}",
    ]) + "\n"
    (tables / "sp8_numbers.tex").write_text(macros, encoding="utf-8")

    result_lines = [
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Método & Libre de conflicto & Pares & Mens./agente & CPU (ms) \\\\",
        "\\midrule",
    ]
    for method in METHODS[:4]:
        selected = runs[(runs["method"] == method) & (runs["run_status"] == "executed")]
        result_lines.append(
            f"{METHOD_LABELS[method]} & {selected['conflict_free'].mean():.3f} & "
            f"{selected['global_conflict_pairs'].mean():.2f} & {selected['messages_per_agent'].mean():.1f} & "
            f"{selected['runtime_ms'].mean():.2f} \\\\"
        )
    result_lines.extend(["\\bottomrule", "\\end{tabular}"])
    (tables / "sp8_results.tex").write_text("\n".join(result_lines) + "\n", encoding="utf-8")

    hypothesis_lines = [
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "ID & Métrica & $n$ & Efecto & IC 95\\% & $p_{Holm}$ \\\\",
        "\\midrule",
    ]
    for row in hypotheses.itertuples(index=False):
        hypothesis_lines.append(
            f"{row.id} & {str(row.metric).replace('_', ' ')} & {int(row.n)} & {row.effect:.3f} & "
            f"[{row.ci95_low:.3f}; {row.ci95_high:.3f}] & {row.p_value_holm:.2e} \\\\"
        )
    hypothesis_lines.extend(["\\bottomrule", "\\end{tabular}"])
    (tables / "sp8_hypotheses.tex").write_text(
        "\n".join(hypothesis_lines) + "\n", encoding="utf-8"
    )


def _plot_results(output_dir: Path, runs: pd.DataFrame, summary: pd.DataFrame) -> None:
    figures = output_dir / "figures"
    proposed = summary[summary["method"] == "periodic_versioned_local"]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for regime in REGIME_LABELS:
        selected = proposed[proposed["regime"] == regime].sort_values("n_coalitions")
        ax.plot(
            selected["n_robots"],
            selected["conflict_free_mean"],
            marker="o",
            label=REGIME_LABELS[regime],
        )
    ax.set_xlabel("Robots N (dos por coalición)")
    ax.set_ylabel("Tasa libre de conflictos lógicos")
    ax.set_ylim(-0.03, 1.03)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(figures / "fig-sp8-network-scale.pdf", bbox_inches="tight")
    plt.close(fig)

    executed = runs[(runs["run_status"] == "executed") & (runs["method"].isin(METHODS[:4]))]
    grouped = executed.groupby("method", as_index=False).agg(
        messages_per_agent=("messages_per_agent", "mean"),
        coordinated_fraction=("coordinated_fraction", "mean"),
        runtime_ms=("runtime_ms", "mean"),
    )
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    for row in grouped.itertuples(index=False):
        size = 50.0 + 12.0 * math.sqrt(max(float(row.runtime_ms), 0.0))
        ax.scatter(row.messages_per_agent, row.coordinated_fraction, s=size, label=METHOD_LABELS[row.method])
    ax.set_xlabel("Mensajes intentados por agente y mundo")
    ax.set_ylabel("Fracción coordinada")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(figures / "fig-sp8-quality-communication.pdf", bbox_inches="tight")
    plt.close(fig)

    oracle_rows = runs[runs["method"] == "central_exhaustive_oracle"].drop_duplicates(
        ["n_coalitions", "seed"]
    )
    local_rows = runs[runs["method"] == "periodic_versioned_local"]
    local_cpu = local_rows.groupby("n_coalitions", as_index=False)["runtime_ms"].median()
    fig, ax1 = plt.subplots(figsize=(7.0, 4.2))
    ax1.plot(
        local_cpu["n_coalitions"],
        local_cpu["runtime_ms"],
        marker="o",
        color="#0066A4",
        label="CPU local mediana",
    )
    ax1.set_xlabel("Coaliciones K")
    ax1.set_ylabel("CPU local (ms)", color="#0066A4")
    ax2 = ax1.twinx()
    spaces = oracle_rows.groupby("n_coalitions", as_index=False)["oracle_profile_space"].first()
    ax2.plot(
        spaces["n_coalitions"],
        spaces["oracle_profile_space"],
        marker="s",
        color="#E65300",
        label="Perfiles del oráculo",
    )
    ax2.set_yscale("log", base=2)
    ax2.set_ylabel("Perfiles $2^K$", color="#E65300")
    ax1.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(figures / "fig-sp8-cost-frontier.pdf", bbox_inches="tight")
    plt.close(fig)


def _report(
    experiment_id: str,
    runs: pd.DataFrame,
    summary: pd.DataFrame,
    hypotheses: pd.DataFrame,
    audit: dict[str, Any],
) -> str:
    proposed = runs[(runs["method"] == "periodic_versioned_local") & (runs["run_status"] == "executed")]
    lines = [
        f"# {experiment_id}",
        "",
        "Canonical SP8 campaign: network-visible route coordination under scale, finite radio, sampled delay and independent packet loss.",
        "",
        f"- Worlds: `{audit['worlds']}`",
        f"- Runs: `{audit['runs']}`",
        f"- Audit: `{audit['status']}`",
        f"- Certified oracle worlds: `{audit['oracle_certified_worlds']}`",
        f"- Proposed conflict-free rate: `{proposed['conflict_free'].mean():.4f}`",
        "",
        "## Confirmatory contrasts",
    ]
    for row in hypotheses.itertuples(index=False):
        lines.append(
            f"- `{row.id}` {row.comparison}: effect={row.effect:.6g}, "
            f"CI95=[{row.ci95_low:.6g}, {row.ci95_high:.6g}], Holm p={row.p_value_holm:.6g}."
        )
    lines.extend([
        "",
        "## Scope",
        "",
        audit["not_claimed"],
    ])
    return "\n".join(lines) + "\n"


def _expand_seeds(spec: Any) -> list[int]:
    if isinstance(spec, dict):
        start = int(spec["start"])
        return list(range(start, start + int(spec["count"])))
    return [int(value) for value in spec]


__all__ = [
    "METHODS",
    "NetworkWorld",
    "ProtocolOutcome",
    "audit_world_theory",
    "build_audit",
    "evaluate_hypotheses",
    "generate_world",
    "run_sp8_config",
    "simulate_local_protocol",
    "simulate_method",
    "summarize_runs",
]

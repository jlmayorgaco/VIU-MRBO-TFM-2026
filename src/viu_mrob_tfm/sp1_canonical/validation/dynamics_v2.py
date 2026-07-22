"""Preconditioned, two-phase population dynamics for SP1 validation V2.

The scale below is an empirical dimensionless proxy for the normalized
mean-field coupling and graph stiffness.  It is deliberately named
``operator_scale_estimate``: no Lipschitz bound is claimed.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from viu_mrob_tfm.sp1_canonical.validation.dynamics import (
    DynamicResult,
    GraphInfo,
    run_population_dynamics,
)
from viu_mrob_tfm.sp1_canonical.validation.model import ResourceWorld, normalized_constraints


@dataclass(frozen=True, slots=True)
class InstancePreconditioner:
    operator_scale_estimate: float
    normalized_coupling_scale: float
    normalized_graph_scale: float
    eta: float
    step: float
    step_unclipped: float
    step_min: float
    step_max: float


@dataclass(frozen=True, slots=True)
class TwoPhaseDynamicResult:
    operational: DynamicResult
    refinement: DynamicResult | None
    preconditioner: InstancePreconditioner
    operational_converged: bool
    refinement_attempted: bool
    refinement_converged: bool
    comparable_at_1e6: bool
    stop_reason: str
    history: pd.DataFrame

    @property
    def final(self) -> DynamicResult:
        return self.refinement if self.refinement is not None else self.operational

    @property
    def messages_total(self) -> int:
        return self.operational.messages + (self.refinement.messages if self.refinement is not None else 0)

    @property
    def scalars_sent_total(self) -> int:
        return self.operational.scalars_sent + (
            self.refinement.scalars_sent if self.refinement is not None else 0
        )


def _coupling_matrix(world: ResourceWorld) -> np.ndarray:
    """Matrix of the normalized aggregate-coverage map."""

    normalized = normalized_constraints(world)
    n, k, m = normalized.shape
    matrix = np.zeros((k * m, n * k), dtype=float)
    for robot in range(n):
        for load in range(k):
            matrix[load * m : (load + 1) * m, robot * k + load] = normalized[robot, load]
    return matrix


def estimate_instance_preconditioner(
    world: ResourceWorld,
    graph: GraphInfo,
    *,
    distributed: bool,
    eta: float = 0.22,
    step_min: float = 0.01,
    step_max: float = 0.10,
) -> InstancePreconditioner:
    """Compute a reproducible per-instance scalar preconditioner.

    The aggregate constraint map is normalized by ``sqrt(N)`` because the
    dynamics uses mean-field residuals.  Graph stiffness is normalized by
    ``1 + d_max`` consistently with Metropolis mixing.  The resulting quantity
    is a numerical scale estimate, not a proven smoothness constant.
    """

    if eta <= 0.0 or step_min <= 0.0 or step_max < step_min:
        raise ValueError("eta and step bounds must be positive and ordered")
    coupling = float(np.linalg.norm(_coupling_matrix(world), ord=2)) / np.sqrt(world.n_robots)
    if distributed:
        max_degree = float(np.max(graph.adjacency.sum(axis=1))) if world.n_robots else 0.0
        graph_scale = float(graph.lambda_max) / (1.0 + max_degree)
    else:
        graph_scale = 0.0
    scale = max(1.0, 1.0 + coupling + graph_scale)
    raw_step = float(eta) / scale
    step = float(np.clip(raw_step, step_min, step_max))
    return InstancePreconditioner(
        operator_scale_estimate=scale,
        normalized_coupling_scale=coupling,
        normalized_graph_scale=graph_scale,
        eta=float(eta),
        step=step,
        step_unclipped=raw_step,
        step_min=float(step_min),
        step_max=float(step_max),
    )


def run_two_phase_dynamics(
    world: ResourceWorld,
    costs: np.ndarray,
    graph: GraphInfo,
    *,
    distributed: bool,
    eta: float = 0.22,
    step_min: float = 0.01,
    step_max: float = 0.10,
    operational_max_iterations: int = 30_000,
    refinement_max_iterations: int = 100_000,
    operational_tolerance: float = 1e-3,
    refinement_primal_tolerance: float = 1e-6,
    refinement_consensus_tolerance: float = 1e-4,
    refinement_stationarity_tolerance: float = 1e-4,
    comparison_feasibility_tolerance: float = 1e-6,
    entropy_tau: float = 0.003,
    consensus_gain: float = 1.0,
    use_integral_consensus: bool = True,
    history_stride: int = 500,
    lp_objective: float | None = None,
    attempt_refinement: bool = True,
) -> TwoPhaseDynamicResult:
    """Run operational convergence and, only after success, strict refinement."""

    preconditioner = estimate_instance_preconditioner(
        world,
        graph,
        distributed=distributed,
        eta=eta,
        step_min=step_min,
        step_max=step_max,
    )
    shared = {
        "integrator": "mirror_prox",
        "step": preconditioner.step,
        "comparison_feasibility_tolerance": comparison_feasibility_tolerance,
        "entropy_tau": entropy_tau,
        "consensus_gain": consensus_gain,
        "use_integral_consensus": use_integral_consensus,
        "history_stride": history_stride,
        "lp_objective": lp_objective,
    }
    operational = run_population_dynamics(
        world,
        costs,
        graph,
        distributed=distributed,
        max_iterations=operational_max_iterations,
        convergence_residual_mode="relative",
        primal_tolerance=operational_tolerance,
        consensus_tolerance=operational_tolerance,
        stationarity_tolerance=operational_tolerance,
        **shared,
    )
    refinement: DynamicResult | None = None
    if operational.converged and attempt_refinement:
        refinement = run_population_dynamics(
            world,
            costs,
            graph,
            distributed=distributed,
            max_iterations=refinement_max_iterations,
            convergence_residual_mode="absolute",
            primal_tolerance=refinement_primal_tolerance,
            consensus_tolerance=(refinement_consensus_tolerance if distributed else 1.0),
            stationarity_tolerance=refinement_stationarity_tolerance,
            initial_x=operational.x,
            initial_dual=operational.dual,
            **shared,
        )
    final = refinement if refinement is not None else operational
    final_primal = float(final.history.iloc[-1]["primal_residual_normalized"])
    comparable = bool(final_primal <= comparison_feasibility_tolerance)
    if not operational.converged:
        stop_reason = "operational_iteration_limit_or_nonfinite"
    elif not attempt_refinement:
        stop_reason = "operational_only"
    elif refinement is not None and refinement.converged:
        stop_reason = "refinement_converged"
    else:
        stop_reason = "refinement_iteration_limit_or_nonfinite"
    histories = [operational.history.assign(phase="operational")]
    if refinement is not None:
        histories.append(refinement.history.assign(phase="refinement"))
    return TwoPhaseDynamicResult(
        operational=operational,
        refinement=refinement,
        preconditioner=preconditioner,
        operational_converged=bool(operational.converged),
        refinement_attempted=bool(refinement is not None),
        refinement_converged=bool(refinement is not None and refinement.converged),
        comparable_at_1e6=comparable,
        stop_reason=stop_reason,
        history=pd.concat(histories, ignore_index=True),
    )


__all__ = [
    "InstancePreconditioner",
    "TwoPhaseDynamicResult",
    "estimate_instance_preconditioner",
    "run_two_phase_dynamics",
]

# PhD Research Statement

## Working Title

Game-theoretic and physics-aware coalition control for cooperative AMR transport under uncertainty.

## Core Thesis

The long-term research direction is to unify allocation, contact feasibility, motion control and resilience in cooperative AMR systems through a physically grounded game formulation. Robots should not merely be assigned to loads; they should form coalitions whose roles, slots, forces, energy state and communication structure make the transport task feasible and efficient.

## Research Spine

The SP1-SP8 pipeline suggests a staged doctoral program:

| Stage | Research object | Current evidence | Doctoral extension |
|---|---|---|---|
| SP1 | Recruitment/coalitions | Implemented | Formal game and convergence analysis |
| SP2 | Capacity heterogeneity | Implemented | Online uncertainty and load estimation |
| SP3 | Wrench feasibility | Implemented | Full friction cones, nonconvex contact and proof of approximation |
| SP4 | Motion/control | Implemented | Coupled allocation-control stability |
| SP5 | Obstacle-aware cooperative transport | Implemented | Traffic-aware formation MPC and safety certificates |
| SP6 | Failure/battery resilience | Implemented | Online reconfiguration with temporal logic |
| SP7 | Communication and sensing robustness | Implemented | Networked control with temporal connectivity guarantees |
| SP8 | Warehouse-scale scalability and intractability | Implemented compact MC + extended 5-50k fleet ladder | Mean-field limits, distributed guarantees, GNN/MARL wrench decoders and benchmark release |

## Mathematical Threads

Priority theoretical lines:

- Potential games for load-deficit/payoff design.
- Population dynamics: replicator, Smith, logit, Brown/BNN and primal-dual flows.
- Generalized Nash games with coupled capacity, wrench and collision constraints.
- Mean-field game limits for large AMR fleets.
- Euler-Lagrange/Hamiltonian modeling of payload pose and contact wrench generation.
- Passivity and energy shaping for safe cooperative transport.
- Hybrid systems for recruit-contact-transport-recover transitions.
- Statistical decision theory for fair comparison of trained vs low-parameter controllers.

## Novelty Hypotheses

1. A wrench-aware coalition game can explain why scalar capacity methods fail under rotational payload demands.
2. Local repair layers can provide most of the feasibility benefit of centralized search at lower communication/training cost.
3. MARL methods need explicit feasibility decoders or safety filters to remain competitive under OOD coalition constraints.
4. Resource-normalized evaluation can change the practical ranking of "best" algorithms for industrial AMR deployment.

## Near-Term Work Needed

- Extend SP8 from the current 5-50k, 5-seed high-power fleet ladder to finite-N mean-field error analysis and full data-driven/GNN ablations.
- Add CI and an experiment manifest with git hash and environment capture.
- Make video catalogs uniform for SP1-SP6.
- Strengthen formal proofs around wrench complementarity and non-submodularity.
- Decide which result set is thesis core and which is doctoral roadmap.

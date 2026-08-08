# SP1.N3 — discovery, audit and proposed design

**Status:** design only. No confirmatory seed opened, no campaign run, no RAW written.
**Baseline freezes:** `SP1-N1-FROZEN` (13263e80), `SP1-N2-FROZEN` (42e05aad). Both immutable.
**Date:** 2026-08-08

N3 keeps the frozen N2 problem exactly and removes only the optimizer and the global
robot registry:

```
min  sum_{i,k} d_ik y_ik
s.t. sum_k y_ik <= 1          for every robot i
     sum_i c_i y_ik >= m_k    for every load k
     y in {0,1}^{N x K}
```

---

## 1. Dependency map of N3

| Layer | Artifact | Reusable for N3? |
|---|---|---|
| Problem + oracle | `scripts/sp1_n2_oracle.py` | **Yes, unchanged.** `build_model`, `solve`, status classes `OPTIMAL / FEASIBLE_TIME_LIMIT / INFEASIBLE / UNKNOWN`. |
| World generator | `scripts/sp1_n2_confirmatory.py::make_world` | **Yes, but it discards positions** — see §6. |
| Level packaging | `scripts/sp1_levels_common.py` | Yes (figures, manifests, `write_level_manifest`). |
| Existing N3 package | `scripts/sp1_n3.py` + `scripts/results/sp1_levels/n3/` | **No.** Historical pilot over a different problem — see §14. |
| Distributed allocators | `src/viu_mrob_tfm/sp1_geo/allocators/{cbba,grape}.py` | **No.** Neither is distributed and neither solves the N2 problem — see §2–4. |
| Recovery | `src/viu_mrob_tfm/sp1_geo/recovery.py` | **No.** Centralized — see §5. |
| Comm graph | `src/viu_mrob_tfm/sp1_geo/scenario.py::_connected_knn_graph` | **No.** Cannot express the negative control — see §6. |

Nothing in `sp1_geo` can be lifted into N3 unmodified. N3 needs a new module.

---

## 2. Audit — `allocate_capacity_cbba` (`allocators/cbba.py`)

**It is not a distributed algorithm.** It computes the global winner directly and then
*charges* a communication cost as if consensus had happened.

| # | Finding | Evidence |
|---|---|---|
| C1 | **No message passing exists.** A single `winners` dict is built centrally over every robot's proposal; the global lexicographic argmax is taken in one pass. | `cbba.py:102-108` |
| C2 | **The algorithm reads the global graph diameter as a decision input** — explicitly forbidden by the N3 contract. | `cbba.py:47`, used at `:109` |
| C3 | **The disconnected negative control silently passes.** `_graph_diameter` returns `n` for a disconnected graph, so partition only makes rounds *more expensive* — the winner is still globally consistent. An impossibility experiment run against this code would report success. | `cbba.py:27-28` |
| C4 | **Global mutable state.** `occupied` is one slot table shared by all robots. | `cbba.py:44,116,120` |
| C5 | **Bids are not marginal on the residual deficit.** `base_bids` is computed once at `x = 0` and never recomputed, so a 10 kg load values a 1 kg robot and a 5 kg robot by a static score. This is precisely the defect the design brief warns about. | `cbba.py:46`, reused at `:76,82,94` |
| C6 | **Messages and bytes are formulas, not measurements.** `messages = 2·edges·rounds`, `bytes = messages · 40`. | `cbba.py:136-137` |
| C7 | Tie-breaking *is* deterministic — `(bid, -robot, action)` — and is worth keeping. | `cbba.py:104` |

Consequence: **no CBBA convergence property can be claimed from this code**, because no
consensus is executed. C5 also means the multi-winner bid has no diminishing-marginal-gain
structure to appeal to.

## 3. Audit — `allocate_grape` unilateral (`allocators/grape.py`)

| # | Finding | Evidence |
|---|---|---|
| G1 | **The move selector is centralized.** `_best_unilateral` scans every robot and returns the single best deviation fleet-wide; the main loop applies that one move. A distributed GRAPE has each agent act on its own view. `adjacency_restricted` only limits *which loads* a robot may join, never who gets to move. | `grape.py:67,173,185-196` |
| G2 | **The potential is evaluated globally** over the whole profile at every candidate. | `grape.py:61,92` |
| G3 | **Global conflict table.** `_valid_unique` checks slot uniqueness across all robots. | `grape.py:13-28,90` |
| G4 | **`rounds` is the number of accepted moves, not communication rounds**; bytes are `messages · 48`. | `grape.py:208-209,226` |
| G5 | Status separation `local_stable` / `max_iterations` is sound and worth keeping — but the blocking check mixes an *adjacency-restricted* unilateral test with an *unrestricted* pair test, so "stable" is measured against two different neighbourhoods. | `grape.py:199-206,221` |
| G6 | The initial profile is a global greedy lexsort over all actions. | `grape.py:41-49` |

## 4. Audit — `_best_pair_swap` (Weighted-Pair-GRAPE)

| # | Finding | Evidence |
|---|---|---|
| P1 | Pair enumeration *is* adjacency-restricted (`left`–`right` must be neighbours) — the one genuinely local part of the module. | `grape.py:116` |
| P2 | But selection is again a **global argmax over all pairs**. | `grape.py:115-157,187` |
| P3 | The swap **exchanges slots only**. Two robots trade positions; neither can move to a load nobody occupies. This is strictly weaker than the pairwise deviation a hedonic-stability claim needs. | `grape.py:123-142` |
| P4 | Both robots must already be assigned (`left_action < 0 → continue`), so no pair move can ever recruit an idle robot. | `grape.py:121` |

## 5. Audit — recovery and the objective

**The objective is not N2's.** `welfare.py` maximizes a concave saturating coverage value

```
value_k = priority_k * mean( 1 - exp( -curvature * service_k / demand_k ) )
```

minus a **five-term blended cost** (`distance 0.38, energy 0.24, time 0.18, turn 0.12,
reliability 0.08`, `contributions.py:14-20`). Capacity is a *reward that saturates*, not a
*hard constraint*. N2's `sum_i c_i y_ik >= m_k` has no counterpart, and `min sum d_ik y_ik`
is not what is optimized.

**The model is not N2's either.** `sp1_geo` is a physical contact-slot model — `ContactSlot`
with `offset_xy_m`, wrench columns, battery and energy margins (`models.py:90-144`,
`contributions.py:48-58`). N2 has no slots and no physics.

**Recovery is centralized.** `recover_assignment` calls `certify_assignment(world, ...)` on
the whole world (`recovery.py:245,247,332`) and ranks candidates against a global
`available_robots` set (`recovery.py:35-40`). It cannot serve as N3's recovery layer without
being rewritten.

## 6. Audit — communication graph

`_connected_knn_graph` (`scenario.py:83-108`) builds a kNN graph and then **forces
connectivity** with a spanning chain. Edge dropping refuses any removal that disconnects the
graph (`scenario.py:355-360`).

Consequences: it is kNN, not R-disk; the graph is connected *by construction*, so **the
permanent-partition negative control cannot be expressed at all**; and degree, not radius, is
the tuning knob, which makes `lambda_2` and diameter hard to sweep independently.

## 7. Audit — byte accounting, and why N4 fairness is already at risk

```
cbba.py:137   bytes = messages * 40
grape.py:226  bytes = messages * 48
qpg.py:283    bytes = messages * (16 + 8 * n_loads * resource_dimension)
```

Three different hardcoded constants, and **Geo-QPG's is the only one that scales with the
number of loads**. Any N3-vs-N4 communication comparison built on this would measure the
constants, not the algorithms. Fixing this is a precondition for N4, not a detail.

---

## 8. Proposed information contract (N3.0)

To be frozen before any implementation and inherited unchanged by N4.

| Information | Access |
|---|---|
| Load catalog `(k, l_k, m_k)` | Immutable, announced to all robots at t=0 |
| Own `(c_i, p_i)` | Private to robot i |
| Any other robot's capacity, position, bid, commitment or coalition state | **Only** via messages on `E` |
| Global robot table | Forbidden |
| MILP at runtime | Forbidden |
| Central repair | Forbidden in the primary result |
| Graph diameter, `lambda_2`, remaining rounds, global convergence flag | Forbidden as algorithm inputs; recorded by the observer only |
| Global observer | Records metrics; never influences a decision |

Precise name: **distributed decision with globally announced tasks and robot state exchanged
only between neighbours.** Not "fully local perception" — the load catalog is a common input.
Propagating tasks over the graph too is a *later sensitivity*, not the primary campaign.

**Enforcement, not convention.** Each robot gets an explicit `RobotView` exposing only its own
state plus its inbox. Anything global is unreachable by construction, and a test asserts that
the step function of every method accepts no other argument. An audit that relies on reading
the code is the failure mode that produced C1–C6.

**Graph.** `G = (I, E)` static, undirected, geometric R-disk over the N2 robot positions.
Regimes: complete / dense / medium / near-threshold / **permanently partitioned** (negative
control). Recorded per world: `lambda_2(L)`, mean degree, diameter, components.

**Three orthogonal status fields**, never collapsed:

```
algorithm_status : CONVERGED | QUIESCENT | MAX_ROUNDS | TIME_LIMIT | DEADLOCK | ERROR
solution_status  : RAW_FEASIBLE | RECOVERED_FEASIBLE | CAPACITY_DEFICIT | ROBOT_CONFLICT
oracle_status    : OPTIMAL | FEASIBLE_TIME_LIMIT | INFEASIBLE | UNKNOWN
```

A timeout is not an infeasible assignment, and a feasible assignment at the round cap is not
convergence.

---

## 9. Theory N3 can actually support

**T1 — distributed feasibility certificate.** Exclusivity `sum_k y_ik <= 1` is certifiable by
robot i alone; capacity `Q_k(y) = sum_i c_i y_ik >= m_k` by the members of coalition k alone.
Hence *conflict-free*, *capacity-feasible* and *strictly feasible* are distinct, locally
checkable predicates. Conflict-freedom alone must never be reported as feasible.

**T2 — impossibility under permanent partition.** On a permanently disconnected graph, no
algorithm using only its own component's information can guarantee a globally feasible
assignment for every instance in which robots of different components compete for common
loads. Proof by two globally distinct, component-indistinguishable worlds requiring different
commitments. This is why connectivity is an assumption, not a simulator detail — and it is
exactly what the current CBBA code (C3) would fail to detect.

**T3 — potential termination for Weighted-GRAPE.** With

```
Phi(y) = -sum_{i,k} d_ik y_ik - lambda_d sum_k [m_k - Q_k(y)]_+ - lambda_e sum_k [Q_k(y) - m_k]_+
```

and strictly improving moves only: the profile space is finite, `Phi` strictly increases, so
the sequence terminates at a unilateral equilibrium (pairwise, with pair moves). **This is
termination, not optimality**, and it holds only if the implementation accepts strict
improvements only — which must be a test, not an assumption.

**T4 — Capacity-CBBA invariants.** Provable: at most one commitment per robot; winners
identifiable by version/timestamp; deterministic tie-break; final assignment verifiable by T1.

**Explicitly NOT inherited:** canonical CBBA convergence in `<= N·D` rounds, the DMG
(diminishing marginal gain) guarantee, and CBBA's conflict-resolution optimality. The
multi-winner adaptation with deficit-dependent bids does not satisfy the hypotheses. If
termination holds it will be reported as an **empirical** result with the round budget stated.

---

## 10. Claims N3 must not make

1. That any baseline "converges" without a proof valid for the adapted scoring.
2. That a hedonic equilibrium is optimal — it is compared to the MILP, never called optimal.
3. That CBBA or GRAPE is "better". N3 builds the reference frontier; it does not crown a winner.
4. That RECOVERED output is the method's native output.
5. That a round-cap timeout is infeasibility.
6. Any communication comparison until §7 is fixed.

---

## 11. Experiments

| | Question |
|---|---|
| **N3.E1** | White-box: do the implementations respect their invariants, stay deterministic, and match a same-protocol reference on small worlds? |
| **N3.E2** | Feasibility and quality vs the N2 MILP on connected graphs. |
| **N3.E3** | Price of locality: quality/feasibility lost per byte saved. |
| **N3.E4** | Scale, packet loss, delay, round budget. |

**E1** — hand-built instances plus property tests: exclusivity, capacity, deterministic
tie-breaks, strict `Phi` monotonicity, winner-list consistency, bit-identical reruns, ID-permutation
invariance, complete graph, minimal connected graph, **partitioned graph as negative control
(must fail to guarantee feasibility)**. No p-values — invariants only.

**E2** — worlds where N2's oracle is `OPTIMAL`; gap computed only there:
`gap_w = (J_w^method - J_w^MILP) / J_w^MILP`.

**E3** — same worlds and methods across the five graph regimes. Primary figure: Pareto front of
feasibility/quality vs **bytes per agent**. The question is not "is the complete graph better"
but how much is lost per byte saved.

**E4** — factors varied one at a time: N; packet loss; fixed/random delay; round cap.

**RAW vs RECOVERED are reported side by side, always:**

| Method | RAW feasible | RECOVERED feasible | gap RAW | gap RECOVERED | recovery cost |

---

## 12. Factors, levels, seeds and run count

Reusing N2's generator (`q_bar = 5.0`, workspace 100×100 m, lognormal renormalized capacities,
Dirichlet `alpha = 3.0`) so N3 worlds are N2 worlds.

| Exp | Grid | Worlds | × methods | Runs |
|---|---|---|---|---|
| E1 | ~40 hand-built + property tests | 40 | 3 | 120 |
| E2 | N=16,K=5; CV {0, 0.35, 0.65, 1.00}; rho {0.70, 0.85}; 5 scenarios; 30 seeds | 1 200 | 3 | 3 600 |
| E3 | E2 subset (CV {0.35,0.65}, rho {0.85}, 5 scenarios, 30 seeds) × 5 graph regimes | 300 × 5 | 3 | 4 500 |
| E4 | N ∈ {16,24,32,48,64}, K = 3N/10; CV 0.65; rho 0.85; 15 seeds; {loss 0/0.05/0.15} ∪ {delay 0/2} ∪ {cap 25/100} | 5 × 15 × 7 | 3 | 1 575 |

**Total ≈ 9 795 method-world runs + 1 500 MILP oracle solves** (E2 grid, 30 s limit; E3/E4
reuse E2's oracle where the world is identical). Estimated wall clock: oracle ~45 min,
baselines ~2–4 h single-threaded. Seeds derive from a new `base_seed` opened only after approval.

**Metrics per run:** `raw_feasible`, `recovered_feasible`, `robot_conflict`, `capacity_deficit`,
`distance_cost`, `optimality_gap`, `excess_capacity`, `coalition_size`, `rounds`, `messages`,
`bytes`, `runtime`, `recourse`, `censoring_status`, plus `algorithm_status`, `solution_status`,
`oracle_status`, `lambda_2`, `mean_degree`, `diameter`, `components`.

---

## 13. Methodological risks

| Risk | Mitigation |
|---|---|
| Reusing `sp1_geo` allocators because the names match | Rejected: §2–4. New implementations. |
| A simulated-consensus shortcut reappearing (C1) | `RobotView` makes global state unreachable; partition control must fail. |
| Byte constants deciding the N4 comparison (§7) | Freeze one message schema; count serialized bytes per message type. |
| Reporting only RECOVERED (as `sp1_n3.py` does) | RAW and RECOVERED are separate mandatory endpoints. |
| Gap computed where the oracle is uncertified | Gap only where `oracle_status == OPTIMAL`. |
| Positions not in N2 RAW | §6 below — regenerate from seed, assert identity. |
| Inheriting CBBA's theorems | §9 lists what cannot be inherited. |

**World reproduction.** `make_world` returns `(capacities, masses, distance)` and drops
positions (`sp1_n2_confirmatory.py:105-153`), but it is deterministic in `seed`. N3 will add
`make_world_with_positions` in a **new** module that replays the same RNG stream, with a
regression test asserting its `(capacities, masses, distance)` is byte-identical to
`make_world`'s. N2 is not modified.

---

## 14. Historical pilot — what `scripts/results/sp1_levels/n3/` actually is

`scripts/sp1_n3.py` repackages the SP1-GEO benchmark (`GEO_SOURCE_ROOT`). It filters
`closure_stage == "RECOVERED"` only (`sp1_n3.py:39-42`), reports `served_load_rate` and
`physical_welfare`, and computes gaps against the GEO MILP — a different objective, a different
model, a different recovery layer and a different information contract.

**Treat as historical pilot.** Useful for choosing sizes and spotting failures; not usable for
N3 results. It stays on disk untouched; the new campaign writes to `n3_v1/`.

---

## 15. Files that would be created / modified

**Created**
```
experiments/configs/sp1_n3_confirmatory_v1.yaml
src/viu_mrob_tfm/sp1_n3/{__init__,contract,graph,messages,capacity_cbba,weighted_grape,recovery,certificate,worlds}.py
scripts/sp1_n3_confirmatory.py
scripts/sp1_n3_analysis.py
tests/test_sp1_n3_contract.py
tests/test_sp1_n3_invariants.py
scripts/results/sp1_levels/n3_v1/**
```

**Modified**
```
scripts/sp1_levels_common.py   (method labels/colors for the three N3 methods)
docs/04_CLAIMS_EVIDENCE.md     (N3 claim rows, after the campaign)
```

**Untouched:** everything under `n1_v2/`, `n2_v1/`, `scripts/sp1_n1*.py`, `scripts/sp1_n2*.py`,
`thesis/sp1_levels_23p/main.tex`, `scripts/sp1_n3.py`, `scripts/results/sp1_levels/n3/`,
and the whole `sp1_geo` tree.

---

## 16. Open decisions for approval

1. **Rewrite vs adapt** — this plan assumes new implementations. Adapting `sp1_geo` in place
   would change the objective, the model, the graph and the recovery layer at once.
2. **R-disk radii** — proposed from `lambda_2` targets; needs a pilot to pick five separated regimes.
3. **`lambda_d`, `lambda_e`** in `Phi` — GRAPE needs a penalty to make infeasible profiles comparable.
   N2's objective has `lambda_excess = lambda_robot = 0`; the penalties are a *solver* device and
   must be reported as such, with the N2 objective used for all quality metrics.
4. **Shared recovery layer** — must be redesigned as a neighbourhood-local augmenting procedure
   with a stated radius, or dropped in favour of RAW-only reporting.

---

## 17. Confirmation

N1 and N2 were not touched. This phase was read-only apart from this file:

- `scripts/results/sp1_levels/n1_v2/` — no diff vs `SP1-N1-FROZEN`
- `scripts/results/sp1_levels/n2_v1/` — no diff vs `SP1-N2-FROZEN`
- no solver run, no seed opened, no RAW written, no figure regenerated

**Awaiting approval before Phase 5 pilots.**

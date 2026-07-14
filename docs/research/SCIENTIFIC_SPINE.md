# Scientific spine

## Focal problem and research question

The focal problem is distributed coalition formation and safe execution for heterogeneous AMRs transporting loads whose feasibility depends on cardinality, scalar capacity, contact roles, and the wrench that the coalition can generate.

Research question: **When does adding physical marginal information, pair complementarity, integer closure, and physical guards turn a locally coordinated AMR coalition from nominally sufficient into an executable, safe transport coalition, and what does each layer contribute?**

Central hypothesis: cardinality and scalar capacity are necessary but insufficient. A pair-aware Smith revision process with integer closure and a wrench/safety guard should reduce physically false-positive assignments without obtaining apparent precision by abstaining from all tasks.

## Canonical candidate

The only canonical proposed-method candidate is:

**Wrench-Gated Pair-Aware Smith–QR**

Descriptive name: Smith revision dynamics with marginal physical signal, pair-aware integer QR closure, wrench feasibility guard, and safe-motion execution.

This is a candidate, not yet a validated end-to-end algorithm. The closest implemented allocation component is `smith_wrench_pairs_guarded` in `src/viu_mrob_tfm/sp3/methods.py`; later SP5/SP6 methods reuse or approximate only parts of the pipeline. A confirmatory A0–FULL campaign is still required.

## Contributions

| ID | Exact novelty claim | What is not claimed | Mathematics | Code | Campaign/metric | Status |
|---|---|---|---|---|---|---|
| C1 | Operational distinction and falsification ladder between cardinality, scalar capacity, and planar wrench feasibility | cardinality/capacity never matter; 3-D contact dynamics solved | feasibility sets and counterexample conditions | SP1–SP3 scenarios/metrics | SP3 scalar false-positive metrics | empirically supported in reduced-order simulation; generality exploratory |
| C2 | Marginal physical deficit can be used as a local incentive signal for coalition revision | global optimality or faithful reproduction of every cited market dynamic | marginal residual/price definitions | `sp3/methods.py` Smith marginal/support-dual variants | regret, wrench residual/margin | exploratory |
| C3 | Pair-aware insertions represent complementary contact choices missed by single-robot marginal moves | arbitrary higher-order complementarity solved | pair insertion search over bounded neighborhoods | `_best_wrench_insertion(... pair_aware=True)` | pair-aware ablation | implemented; confirmatory effect unsupported |
| C4 | Integer pair-aware closure plus wrench guard can reject/drop incomplete or wrench-infeasible coalitions | learned policy receives credit for deterministic closure; universal feasibility | finite bounded local search/guard contract | guarded repair in SP3; explicit law in control layer | feasibility, coverage, precision–coverage | exploratory/partially demonstrated |
| C5 | An incremental SP0–SP8 falsification ladder can trace where a method first fails | each SP is an independent proof or hardware validation | protocol/claim graph, not a theorem | per-SP runners plus common draft | SPFTC and layer-wise secondary metrics | future integrated validation |

## Validation ladder

1. **SP0 — cardinality assignment mechanics:** separates signal, dynamics, and closure; historical learned-policy claims are blocked by the audit.
2. **SP1 — integer quorum recruitment:** tests complete versus partial coalitions and idle behavior; new confirmatory holdout not opened.
3. **SP2 — scalar heterogeneous capacity:** asks whether enough nominal payload is recruited.
4. **SP3 — planar wrench/contact roles:** falsifies scalar sufficiency and houses the pair-aware guarded allocation candidate.
5. **SP4 — motion/arrival:** asks whether an allocated coalition can safely reach the load.
6. **SP5 — transport:** asks whether it can move the load while maintaining pose/formation/clearance.
7. **SP6 — recovery:** introduces robot/battery/feasibility disruptions.
8. **SP7 — information:** introduces loss, delay, jitter, sensing, and temporal connectivity.
9. **SP8 — scale/OOD:** tests computational and mesoscopic scaling; it is not industrial deployment evidence.

Success at one level is only permission to test the next level, never proof of the next.

## TFM scope versus future papers

The TFM should contain the falsification ladder, the exact SP1 coalition reference, the SP3 counterexample/ablation, a bounded integrated A0–FULL study, negative results, and simulation limitations. Full 3-D contact dynamics, hardware transfer, rigorous mean-field limits, large-scale asynchronous convergence proofs, learned wrench decoders, and industrial deployment belong to future work.

## Claim rules

- Use “implemented” for code, “demonstrated in [model]” for finite reproducible evidence, and “exploratory” for observed but unsealed results.
- Do not say “physically validated” for simulation, “converged” for budget completion, “SOTA” for repository proxies, or “MAPPO learned allocation” when RAW behavior is unchanged and repair supplies success.
- The canonical method becomes supported only if the integrated preregistered campaign shows finite uncertainty intervals, nontrivial coverage, and a reproducible benefit attributable to its added layers.

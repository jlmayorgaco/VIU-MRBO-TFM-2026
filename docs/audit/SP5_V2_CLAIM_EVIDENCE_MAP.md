# SP5 v2 claim--evidence map and writing self-review

## Reverse outline

1. SP4 ends at fixed contacts; SP5 evaluates the post-docking payload plant.
2. Lagrange--Hamilton mechanics defines RAW demand, SAFE command and EXEC realization.
3. The protocol freezes 108 paired worlds before six confirmatory seeds are opened.
4. Results distinguish safety from completion and retain collisions/timeouts.
5. Supported, unsupported and out-of-scope claims are stated separately.

## Claim--evidence map

| Claim | Evidence | Status |
|---|---|---|
| SP5 v2 never repairs positions after integration. | `theory_audit.json`, 864 run rows and lifecycle audit. | supported |
| RAW, SAFE and EXEC are distinct and only EXEC drives the plant. | `stage_ablation.csv`, traces and mechanics identity residual <= 1.14e-13. | supported |
| Hamiltonian+CBF reduces collision and improves safe success versus Hamiltonian RAW. | H5.1 and H5.2, Holm-adjusted p < 1.2e-8. | supported |
| Distributed preview-CBF reduces collision versus the VO proxy. | H5.5, effect -0.3426, Holm p = 2.91e-11. | supported |
| The centralized preview reference improves safe success versus local CBF. | H5.3 effect -0.4259. | not supported |
| Local CBF reduces EXEC barrier violation versus APF in the preregistered direction. | H5.4 effect +0.0012. | not supported |
| SP5 demonstrates frictional contact, wheel dynamics, hardware safety or universal controller dominance. | Not represented by the reduced-order plant. | not claimed |

## Five-dimension adversarial self-review

- Contribution: the new contribution is the auditable command/realization split, not a new global safety theorem.
- Clarity: every paragraph moves from plant, to protocol, to evidence, to limitation.
- Experimental strength: all eight methods share 108 worlds; collisions and 297 timeouts remain observed outcomes.
- Completeness: scenario and N breakdowns, Holm decisions, stage ablation, figures, hashes and failure cases are retained.
- Method soundness: the discrete mechanics identity passes; fixed contacts and planar bounded forces remain explicit assumptions.

No unresolved claim in the Abstract or Introduction depends on the superseded 20,040-run SP5 package.

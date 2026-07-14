# Editorial decision package — Round 1

## Decision: Minor Revision

Four scored reviewers recommend Minor Revision (confidence 4, 5, 4 and 4). The Devil's Advocate found no CRITICAL issue after the post-hoc locality audit, but identified three framing constraints that must remain visible.

## Consensus matrix

| Issue | EIC | R1 | R2 | R3 | DA |
|---|---|---|---|---|---|
| Integrated ladder is the primary contribution | support | support | support | support | support if diagnostic |
| End-to-end local/distributed recovery is not demonstrated | major limit | major limit | noted | major limit | MAJOR |
| Negative A2--A3 result strengthens credibility | support | support | support | support | support |
| Theory must remain assumption-bounded | support | support | major framing | support | MAJOR if generalized |
| Protocol and paired inference are auditable | support | strong support | support | support | support |

## Consensus

- **[CONSENSUS-4]** The A0--FULL ladder and the non-equivalence of static wrench feasibility and dynamic authority are the clearest contributions.
- **[CONSENSUS-4]** Claims must remain limited to the planar numerical model; no functional-safety or hardware claim is justified.
- **[CONSENSUS-3]** FULL is a global replacement proxy under degraded messages, not end-to-end local recovery (EIC, R1, R3; R2 does not oppose).
- **[CONSENSUS-3]** The common-Lyapunov result is a valid application under assumptions, not a new general ISS theory (EIC, R2, R3; R1 does not oppose).

## Arbitration

The only severity disagreement concerns whether the global replacement selector requires Major Revision. R1 and the Devil's Advocate treat it as major for causal attribution; EIC and R3 judge it fixable by precise framing. Because the data remain valid for the bundled recovery proxy and the manuscript now exposes the implementation, the editorial action is Minor Revision with a mandatory claim restriction, not new experimentation.

## Required revisions

| ID | Revision | Sources | Acceptance criterion |
|---|---|---|---|
| R1 | Replace every implication of local FULL recovery with “global replacement proxy under degraded messages.” | EIC, R1, R3, DA | Abstract, results and limitations agree. |
| R2 | Attribute $+0.62$ to the complete FULL bundle, never to messaging alone. | R1, DA | The Section 6.1 result names the bundled estimand. |
| R3 | Calibrate theory novelty: derived application of common Lyapunov ISS; retain assumptions next to the claim. | EIC, R2, DA | Abstract, theory and conclusion use bounded wording. |
| R4 | Clarify that $n=100$ is a prespecified cap and does not necessarily mean every CI is below threshold. | R1 | Methodology and results state the cap. |

## Suggested revisions

- State that $\rho\leq0.16$, HOCBF gains and the 22-s horizon were frozen but not subjected to post-hoc sensitivity analysis.
- Keep stage/family frequencies from being read as warehouse prevalence.
- Present the integrated campaign before the legacy modular campaigns in the defense narrative.

## Decision rationale

The manuscript is fundamentally acceptable as a Master's Thesis. Its central evidence is reproducible, adverse results are retained and the theory is mathematically bounded. The required changes concern attribution and scope, not re-analysis or new data. They can be addressed in one focused revision round. A journal article would require a narrower manuscript and a genuinely graph-local replacement comparison, but those additions are not necessary for the TFM claim set.
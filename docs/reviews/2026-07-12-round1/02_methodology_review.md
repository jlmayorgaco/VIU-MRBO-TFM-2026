# Methodology review report

## Recommendation

**Minor Revision**. Confidence: 5/5.

## Summary

The integrated campaign has a sound paired design. Worlds, stages and seeds are deterministic; the base count is exact; failures remain outcomes; extensions depend on interval width rather than significance; Holm is applied at the final sample size. This directly addresses the principal risks of pseudoreplication, optional stopping and selective seed replacement. Exact McNemar tests and paired bootstrap intervals match the binary endpoint.

The main methodological risk is attribution. A stage changes more than one mechanism: FULL adds degraded messages, memory and a replacement selector, so the $+0.62$ contrast cannot be assigned to communication quality or locality. Code inspection further shows that replacement enumerates all idle robots. The manuscript now classifies it as a proxy, which resolves overclaiming but should be reflected in every stage description. A second issue is that the final cap of 100 worlds can be reached while interval width remains above threshold; the protocol should say “stopped at the prespecified cap,” not “precision achieved.”

## Strengths

1. **Correct unit of analysis**: world-level pairing is explicit in Methodology and Statistics.
2. **Stopping discipline**: all four families extended at 40; nominal stopped at 60 and the rest at 100 solely by CI width.
3. **Failure preservation**: 2,160 rows, 2,160 run IDs and zero numerical errors are auditable.
4. **Result completeness**: negative, null and non-estimable historical findings remain visible.

## Weaknesses and actions

1. **Bundled treatment in FULL (Major for attribution, not validity)**. Rename the estimand as the effect of the whole FULL bundle; do not attribute it to messaging or decentralized recovery.
2. **Precision-cap wording (Minor)**. Report whether each contrast still exceeded $0.20$ at $n=100$ and clarify that 100 is a hard cap.
3. **Sensitivity of engineering constants (Minor)**. The threshold $\rho\leq0.16$, HOCBF gains and 22-s horizon are frozen but not stress-tested. Add a limitation; do not tune them post-hoc.
4. **Runtime interpretation (Minor)**. Invocation time is wall-clock for the four-worker run, whereas per-row runtime is method time. Keep both labels distinct.

## Statistical reporting

Adequate-to-strong. Effect estimates, IC95, exact raw p-values, Holm p-values and paired world counts are reported. Classical a priori power analysis is replaced by a prespecified precision design, which is appropriate here. No p-hacking pattern was found. The main missing item is the final width at the $n=100$ cap.

## Scores

| Dimension | Score |
|---|---:|
| Originality | 78 |
| Methodological rigor | 88 |
| Evidence sufficiency | 86 |
| Argument coherence | 82 |
| Writing quality | 84 |
| Weighted average | 84.2 |
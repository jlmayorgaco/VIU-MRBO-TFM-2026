# Cross-disciplinary and practical review report

## Recommendation

**Minor Revision**. Confidence: 4/5.

## Summary

From an industrial safety and systems-engineering perspective, the manuscript is strongest when it refuses to convert numerical collision avoidance into certification. The explicit $14\%$ residual collision rate, CPU-only execution and separation of visual inspection from physical validation are responsible choices. The certificate ladder resembles an assurance case: each stage contributes evidence, while a failed downstream claim invalidates the operational conclusion.

The practical blind spot is that the ladder is not yet a deployable assurance architecture. Hardware health, localization uncertainty, attachment state, braking distance and network membership would need independent monitors. The current global replacement proxy also assumes a system-level roster. This can be useful in a warehouse fleet manager, but it is different from robot-local autonomy. The paper should name the intended authority boundary rather than presenting central coordination as inherently undesirable.

## Strengths

1. **Safety boundary is explicit**: no functional-safety claim is made.
2. **Resource trade-off is visible**: FULL increases messages from 7--8 to 428--661.
3. **Failure cases are first-class outputs**, which aligns with hazard-analysis practice.
4. **CPU-only reproducibility** is credible for a Master's Thesis environment.

## Weaknesses and actions

1. **Authority model (Major for deployment)**. Draw a boundary between robot-local logic, fleet-manager information and post-hoc evaluation. The replacement selector belongs to the fleet-manager side.
2. **Hazard coverage (Minor)**. The obstacle family has one circular hazard and one dropout. State that simultaneous failures, localization drift and attachment loss are untested.
3. **Operational metrics (Minor)**. Message count lacks packet size distributions, deadlines and network contention; do not equate it with deployable bandwidth.
4. **Stakeholders (Minor)**. A defense presentation should include operator intervention, maintenance and safe-stop behavior, even if not modeled.

## Cross-disciplinary recommendations

For a future industrial paper, map the evidence to ISO 3691-4 safety functions, IEC 61508 assurance logic and an STPA-style control structure. These are recommendations for future framing, not missing requirements for the current simulation thesis.

## Scores

| Dimension | Score |
|---|---:|
| Originality | 79 |
| Methodological rigor | 82 |
| Evidence sufficiency | 80 |
| Argument coherence | 83 |
| Writing quality | 84 |
| Significance and impact | 78 |
| Weighted average | 81.2 |
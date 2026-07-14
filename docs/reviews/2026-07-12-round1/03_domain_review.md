# Domain review report

## Recommendation

**Minor Revision**. Confidence: 4/5.

## Summary

The manuscript makes a credible domain contribution by defining physical coalition operationally rather than treating robot count as transport feasibility. The A0--FULL evidence is especially useful because the scarcity counterexample shows why grasp feasibility and control authority must remain coupled. The Euler--Lagrange/Hamilton identity and HOCBF inequality are technically appropriate, and the common-Lyapunov proof is correct under its stated fixed-matrix interpretation.

The novelty should be calibrated. Common quadratic Lyapunov ISS for a stable linear system with bounded input is established control theory; the novelty lies in applying it as the boundary between coalition replacement and load dynamics. Likewise, wrench-cone projection and HOCBF are not new individually. The contribution is their auditable composition and the empirical counterexample to stagewise monotonicity. The rigid-grasp transition from unilateral static forces to signed dynamic traction is a modeling assumption, not a consequence of the static cone, and should remain prominent.

## Strengths

1. **Physical-coalition definition** connects allocation, grasp geometry and execution.
2. **Mechanics matters empirically**: the $-0.18$ scarcity effect is a strong counterexample to scalar thinking.
3. **Independent theory checks** replace the former formula-versus-itself validations.
4. **No universal dominance claim**: uniform and centralized guards are acknowledged where they explain performance.

## Weaknesses and actions

1. **Novelty calibration (Major in journal framing, Minor for TFM)**. Present Theorem 5.1 as a derived application/bound, not a new general ISS theorem.
2. **Rigid-grasp abstraction (Minor)**. State that signed traction presumes an established bilateral fixture or equivalent attachment; it is not available to a unilateral pushing contact.
3. **Contact assignment scope (Minor)**. A3 searches a bounded one/two-robot neighborhood and greedy slots; it does not solve joint robot--load--contact optimization.
4. **Terminology (Minor)**. Use “wrench feasibility residual” consistently; avoid alternating among force capacity, physical capacity and contact validity.

## Literature positioning

The thesis covers MRTA taxonomy, coalition formation, population games, cooperative transport and CBF foundations. A journal version could position the rigid-grasp assumption more directly against grasp/force-closure literature and discuss actuation-aware CBF feasibility. Existing citations to Gerkey and Matarić (2004), Korsah et al. (2013), Ames et al. (2017), Farivarnejad et al. (2022), and Sandholm (2010) provide an adequate TFM foundation.

## Scores

| Dimension | Score |
|---|---:|
| Originality | 80 |
| Methodological rigor | 84 |
| Evidence sufficiency | 82 |
| Argument coherence | 84 |
| Writing quality | 84 |
| Literature integration | 82 |
| Weighted average | 82.8 |
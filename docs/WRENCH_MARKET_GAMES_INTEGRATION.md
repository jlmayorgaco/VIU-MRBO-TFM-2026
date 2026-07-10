# Wrench-Market Games Integration Map

This note maps `C:/Users/walla/Downloads/wrench_market_games_paper (1).pdf` into the executable TFM pipelines. It is intentionally conservative: theory is mapped to SP claims only when the repository has a corresponding method, metric, audit, or experiment config.

## Core Theory To Carry Into The TFM

| Paper object | Meaning | Repo integration |
|---|---|---|
| Vector-aggregative potential game | Each AMR contributes a vector `E_ik` to a load aggregate `S_k`; marginal pricing aligns individual payoff with team potential. | SP1 scalar quorum, SP2 effective capacity, SP3 wrench contribution are the three concrete instances. |
| Factorization obstruction | Plain payoff is potential-aligned only under homogeneous/factorizable contributions. | SP2 keeps `*_plain` vs `*_marginal` ablations and `sp2_potential_alignment`. |
| Positive-correlation protocol class | Smith, BNN/Brown and replicator should differ mainly in transient/cost when the payoff signal is the same. | SP3 protocol-invariance config compares `replicator_wrench_deficit`, `bnn_wrench_deficit`, `smith_wrench_deficit`. |
| Hybrid integer clearing with guard | Continuous preferences must be rounded to integer coalitions; a finite local guard prevents worsening assignments. | SP1/SP2 `LocalRepair*Allocator`; SP3 guarded wrench repair methods. |
| Reachable wrench set `W(C)` | Cardinality and scalar capacity do not imply physical feasibility. | SP3 scenarios, residual wrench, false-positive metrics, wrench oracle. |
| Wrench complementarity | Pure torque may require two opposite slots; marginal 0/1 auctions can fail. | SP3 `bar_torque_pure`, complementarity gain, pair-aware guarded repair. |
| Continuous wrench margin | Residual/support signal can escape indicator-based complementarity failures. | SP3 `support_dual_wrench_market` and guarded variant. |
| Triple price identity | Market price, contact Lagrange multiplier, and supporting facet normal coincide under the idealized model. | SP3 theory section and doctoral control roadmap; not yet a closed numerical theorem in the current code. |
| Strategic-mechanical potential | Strategy revision and Euler-Lagrange motion can share one Lyapunov/energy argument. | SP3 pose demo and SP4 motion policies; current implementation is a controlled planar proxy. |
| Safety as wrench half-spaces | HOCBF constraints can be represented as affine constraints in wrench space. | SP4 and doctoral roadmap; SP4 has CBF-like motion safety but not full wrench-space HOCBF yet. |
| Endogenous communication topology | Relaying has a physical price and pairwise comparison can select light AMR as relays. | SP5 roadmap; current SP1-SP4 report communication messages/radius degradation but do not yet implement relay-role markets. |

## New Experiment Configs

| SP | Config | Purpose |
|---|---|---|
| SP1 | `configs/experiments/sp1/SP1_MC_wrench_market_protocol_repair.yaml` | Tests protocol engines and finite local repair for integer coalition recruitment. |
| SP2 | `configs/experiments/sp2/SP2_MC_wrench_market_vector_potential_repair.yaml` | Tests marginal pricing, plain-payoff factorization failure, and completion repair. |
| SP3 | `configs/experiments/sp3/SP3_MC_wrench_market_protocol_invariance.yaml` | Tests scalar insufficiency, complementarity, continuous wrench signal, guarded repair, and engine-invariance diagnostics. |
| SP4 | `configs/experiments/sp4/SP4_MC_wrench_market_motion_safety.yaml` | Tests safe motion-field families after allocation: replicator, logit, BNN, Smith, primal-dual, PID and tensor-flow. |

These configs are not replacements for the already reported final Monte Carlo campaigns. They are the next frozen campaigns to run if the TFM narrative is upgraded around wrench-market games.

## Fast Diagnostic Results

Fast no-video diagnostic configs were added and executed to check whether the new family actually improves metrics before running the full video campaigns.

| SP | Diagnostic run | Main outcome |
|---|---|---|
| SP1 | `results/sp1/SP1_DIAG_wrench_market_protocol_repair` | Local repair clearly improves recruitment quality. `replicator_cardinality_repair` reduces oracle gap vs `replicator_cardinality` by `-0.510` paired mean difference (`p_Holm=2.64e-69`); `tensor_quorum_flow_repair` reduces gap vs `cbba` by `-0.289` (`p_Holm=4.29e-38`). |
| SP2 | `results/sp2/SP2_DIAG_wrench_market_vector_potential_repair` | Marginal pricing still works: `smith_capacity_marginal` reduces gap vs `smith_capacity_plain` by `-0.221` (`p_Holm=7.70e-124`). Completion repair improves success/incomplete-capacity but worsens score gap vs marginal, so it needs retuning before being claimed as globally better. |
| SP3 | `results/sp3/SP3_DIAG_wrench_market_protocol_invariance` | Guarded/pair repair fixes the SP3 false-positive problem. `smith_wrench_pairs_guarded` reaches precision `1.0`, `fp_given_assigned=0.0` and oracle gap `0.000012`; pair repair reduces gap vs `smith_wrench_marginal` by `-0.0923` (`p_Holm=1.36e-25`). |
| SP4 | `results/sp4/SP4_DIAG_wrench_market_motion_safety` | Tensor/primal-dual motion improve safety tradeoffs, not raw arrival. `tensor_flow_motion_field` reduces collision rate vs direct motion by `-0.0382` (`p_Holm=2.06e-14`); `primal_dual_motion_field` reduces performance gap vs APF by `-0.0707` (`p_Holm=3.43e-09`). |

All four diagnostic theory audits passed with zero failed checks. These results justify running the full Wrench-Market campaigns, but only SP1 and SP3 can currently be described as clear quality improvements. SP2 should be reported as a tradeoff and retuned; SP4 should be reported as a safety improvement with timeout/arrival cost.

## Claims Allowed Now

- The repository implements the three main instances of vector contribution: scalar/quorum, effective capacity and planar wrench.
- SP2 explicitly separates plain payoff from marginal effective-capacity payoff and audits the potential-alignment condition.
- SP3 implements the physical counterexamples needed for the scalar-capacity critique.
- SP1-SP3 implement finite repair/guard layers that match the hybrid integer-clearing idea.
- SP4 contains motion policies that can be framed as protocol/field families, but it is not yet a full Euler-Lagrange wrench-space safety proof.

## Claims Not Allowed Yet

- Do not claim hardware validation.
- Do not claim full nonholonomic contact-force feasibility.
- Do not claim that the triple price identity has been numerically verified unless a dedicated force-allocation/dual-multiplier test is added.
- Do not claim protocol invariance until the new SP3 protocol-invariance config is run and the paired statistics support that interpretation.
- Do not claim full HOCBF-in-wrench-space safety; SP4 is still a kinematic safety proxy.

## Route For The Final TFM

The final document should present Smith-QR as one member of a larger architecture:

```text
vector contribution E_ik
  -> load aggregate S_k
  -> marginal price / shadow price
  -> positive-correlation protocol engine
  -> integer clearing with guard
  -> physical wrench/motion certificate
```

That framing makes the contribution broader than a single algorithm and keeps the theory, experiments and limitations aligned.

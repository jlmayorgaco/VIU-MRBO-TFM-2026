# Claim Ledger

This ledger separates defensible claims from roadmap claims. It is intended to prevent accidental overclaiming in the thesis, slides or paper draft.

## Defensible Claims

| ID | Claim | Evidence | Status |
|---|---|---|---|
| C1 | The project implements a reproducible SP1-SP8 experimental suite for multi-AMR coalition allocation, capacity, wrench feasibility, motion, obstacle transport, resilience, communication/sensing robustness and warehouse-scale scalability. | `configs/experiments/sp1` through `sp8`, `scripts/run_sp*_experiment.py`, tests | Defensible |
| C2 | SP1 compares classic, SOTA-like, model-based, data-driven and proposed recruitment variants using shared worlds and metrics. | SP1 configs/results/tests; method taxonomy columns | Defensible in simulation |
| C3 | SP2 extends the comparison to heterogeneous capacity constraints and reports comparable cost/quality metrics. | SP2 configs/results/tests | Defensible in simulation |
| C4 | SP3 demonstrates that scalar capacity/cardinality can produce false positives when wrench demands include torque or directional contact geometry. | SP3 wrench metrics, theory audit, pose videos | Defensible in planar quasi-static simulation |
| C5 | SP4-SP6 provide motion, obstacle-avoidance transport and operational recovery evidence using videos plus tabular metrics. | SP4-SP6 results, video catalogs, tests | Defensible in simulated kinematic/control setting |
| C6 | MAPPO in this repository is a real CTDE-style trained policy with a decentralized actor, centralized critic during training and a quorum decoder at execution. | `src/viu_mrob_tfm/sp1/mappo.py`, checkpoint metadata, SP7 resource columns | Defensible for the implemented simulator |
| C7 | SP7 evaluates temporal communication/sensing robustness during cooperative payload transport under radius, packet loss, delay, jitter and intermittent outages. | `results/sp7/SP7_MC_communication_robustness_high_power/` | Defensible for the implemented simulator |
| C8 | SP8 evaluates warehouse-scale intractability and distributed/hierarchical alternatives under moving loads, wrench/torque checks and static/mobile obstacle fields from 5 to 50.000 AMR. | `results/sp8/SP8_MC_fleet_ladder_high_power/`; representative MP4 in `results/sp8/SP8_MC_scalability_warehouse/` | Defensible for the mesoscopic simulator |
| C9 | A closed-form AMR control-law layer is implemented and tested for hand-point kinematics, required wrench, vGNE force sharing, HOCBF projection, unicycle inversion and uniform saturation, with SP4-SP6 supplements. | `src/viu_mrob_tfm/control/explicit_law.py`, `tests/test_explicit_amr_control_law.py`, `results/sp4/SP4_MC_explicit_control_law/`, `results/sp5/SP5_MC_explicit_control_law/`, `results/sp6/SP6_MC_explicit_control_law/` | Defensible in reduced-order simulation |

## Claims That Must Be Worded Carefully

| ID | Claim | Safe wording | Unsafe wording |
|---|---|---|---|
| L1 | MAPPO is SOTA. | "A compact MAPPO-style CTDE baseline/proposed data-driven variant is included." | "This is the best possible or full industrial MAPPO implementation." |
| L2 | Wrench feasibility proves physical transport. | "Wrench feasibility is a planar quasi-static assignment-layer certificate." | "The robots are guaranteed to physically manipulate the object in real contact dynamics." |
| L3 | Battery robustness is solved. | "Battery is measured in SP6 and recorded as an OOD covariate in SP7." | "All allocation methods optimize battery degradation." |
| L4 | Smith-QR is the whole contribution. | "Smith-QR is one member of a broader population-game/control family including replicator, logit, Brown/BNN, primal-dual and tensor-flow repair." | "The thesis contribution is only Smith-QR." |
| L5 | Videos prove correctness. | "Videos are qualitative inspection artifacts paired with quantitative metrics." | "The video alone validates the method." |
| L6 | SP8 proves industrial warehouse deployment. | "SP8 is a mesoscopic scalability/intractability benchmark that uses warehouse-scale AMR/load counts and transport-risk proxies." | "SP8 validates a deployable Amazon-scale or Cainiao-scale controller in real physics/hardware." |
| L7 | The explicit AMR control law is optimal in practice. | "The explicit law is a closed-form reduced-order controller integrated and tested in SP4-SP6; SP5 cargo performs well, while SP4 and SP6 expose tuning limits." | "The explicit law is a universally superior optimal controller for real AMR payload transport." |

## Roadmap Claims

| ID | Claim | Required future evidence |
|---|---|---|
| R1 | Full MAPPO ablations without decoder, without BC warm start or with learned repair selector. | Separate training configs, checkpoints, validation/test split and a future data-driven/OOD SP or appendix. |
| R2 | End-to-end differentiable wrench decoder or GNN-wrench policy. | Implemented training loop, held-out OOD benchmark, ablations. |
| R3 | Real robot transfer. | Hardware experiments, calibration logs, safety protocol, sensor/actuator details. |
| R4 | Formal convergence of every proposed discrete repair variant. | Mathematical proof or counterexample-driven bounded guarantee. |
| R5 | Mean-field game limit with rigorous finite-N error. | Assumptions, theorem, proof and numerical convergence study. |

## Thesis Rule

Every strong sentence in the final thesis should map to one of:

- A defensible claim in this ledger.
- A literature citation.
- A clearly marked hypothesis or future-work statement.

If a sentence maps only to a roadmap claim, it must not be phrased as a result.

# Paper Claims Matrix

This matrix is a draft bridge from thesis artifacts to a publishable paper.

## Candidate Paper 1: Wrench-Aware Coalition Recruitment

| Section | Claim | Evidence | Missing before submission |
|---|---|---|---|
| Introduction | Scalar capacity/cardinality is insufficient for cooperative payloads with torque requirements. | SP3 scenarios and false-positive metrics | Tight example figure in final style |
| Theory | Wrench feasibility is a geometric certificate over assigned contact slots. | SP3 wrench evaluator and theory audit | Formal notation cleanup and proof appendix |
| Methods | Population-game/local-repair methods can be extended with wrench residual terms. | SP3/SP1 method families | Sharper algorithm pseudocode |
| Experiments | Wrench-aware methods reduce false positives/residuals relative to scalar baselines. | `results/sp3/SP3_MC_wrench_comparison_methodology_v3/` and paper figures | Tighten final captions and export publication-resolution panels |

## Candidate Paper 2: Communication-Robust Cooperative Transport

| Section | Claim | Evidence | Missing before submission |
|---|---|---|---|
| Problem | Cooperative transport requires temporal connectivity, not only initial assignment. | SP7 communication profiles and network time series | Longer full-scale MC run |
| Methods | Radius, packet loss, burst drops, delay, jitter and sensor degradation can be swept on identical transport worlds. | `src/viu_mrob_tfm/sp7/` | Add richer RF/occlusion model if targeting networking venue |
| Experiments | Connectivity-aware/delay-robust methods can be compared against centralized and local-sensor baselines under harsh profiles. | `results/sp7/SP7_MC_communication_robustness_high_power/` | Increase seeds/profiles only if targeting a networking venue |
| Discussion | Multi-hop relay and temporal connectivity should be reported separately from direct all-to-all connectivity. | SP7 relay/direct/temporal metrics | Formalize temporal connectivity theorem |

## Candidate Paper 3: End-to-End Cooperative AMR Transport Benchmark

| Section | Claim | Evidence | Missing before submission |
|---|---|---|---|
| Benchmark | SP1-SP8 provide a staged benchmark from assignment to warehouse-scale scalability. | Configs/results/tests | Dataset card and public release checklist |
| Visual QA | Videos support qualitative inspection of motion, contact and recovery behavior. | SP1-SP6 video artifacts | Uniform video catalog for all canonical SPs |
| Reproducibility | Makefile targets reproduce tests, smoke and canonical runs. | `Makefile`, `docs/REPRODUCIBILITY.md` | CI workflow |

## Candidate Paper 4: Warehouse-Scale Wrench-Aware AMR Allocation

| Section | Claim | Evidence | Missing before submission |
|---|---|---|---|
| Problem | Exact/global coalition search and time-expanded centralized MPC become impractical at warehouse-scale AMR/load counts. | SP8 timeout and complexity metrics over 5-50.000 AMR | Add multi-seed hardware/runtime envelope if targeting publication |
| Methods | Distributed and hierarchical wrench-market variants can be compared against centralized/classic/SOTA baselines using the same moving-load, obstacle and wrench checks. | `src/viu_mrob_tfm/sp8/`, `results/sp8/SP8_MC_fleet_ladder_high_power/` | Formalize approximation and mean-field argument |
| Experiments | Proposed distributed/hierarchical methods improve completion and wrench feasibility over classic local/Hungarian baselines in the high-power fleet ladder. | SP8 H8.2/H8.3 Holm-rejected tests in `SP8_MC_fleet_ladder_high_power` | Expand seeds per fleet size and add publication-resolution figures |
| Discussion | Scale claims must separate algorithmic intractability, mesoscopic transport risk and hardware/contact validation. | SP8 theory audit and claim ledger | Add external benchmark context and citation audit |

## Candidate Paper 5: Closed-Form AMR Control for Cooperative Payload Transport

| Section | Claim | Evidence | Missing before submission |
|---|---|---|---|
| Theory | Hand-point unicycle control, required wrench, vGNE force sharing, HOCBF projection and uniform saturation can be assembled into an executable local AMR control layer. | `docs/EXPLICIT_AMR_CONTROL_LAW.md`, `src/viu_mrob_tfm/control/explicit_law.py`, unit tests | Formal proof cleanup and notation alignment with the final thesis |
| Methods | The explicit law can be inserted into SP4 motion, SP5 transport and SP6 recovery without changing the global assignment contract. | SP4/SP5/SP6 method factories and configs | Cleaner pseudocode and ablation of each term |
| Experiments | The cargo/caging variant is promising in SP5, but SP4 and SP6 show tuning limits rather than universal dominance. | `results/sp5/SP5_MC_explicit_control_law/`, `results/sp4/SP4_MC_explicit_control_law/`, `results/sp6/SP6_MC_explicit_control_law/` | Larger high-power rerun and stronger safety tuning before claiming a main result |
| Discussion | Negative/neutral results are useful: they identify where closed-form theory needs scenario-specific safety and allocation coupling. | H4E/H5E/H6E hypothesis tables | Hardware or higher-fidelity contact simulator before deployment claims |

## Do Not Submit Until

- Citation audit is complete.
- Claim ledger is synchronized with the manuscript.
- Canonical figures are regenerated from clean result folders.
- All tests pass after a clean checkout install.
- A reviewer can run at least smoke experiments in under a few minutes.

# Results Index

This folder is intentionally kept clean. Smoke/debug/diagnostic outputs were moved to `_archive/results_noncanonical_20260708_sp_cleanup/`.

## Canonical Monte Carlo Evidence

| SP | Result directory | Runs/checks | Notes |
|---|---|---:|---|
| SP1 | `sp1/SP1_MC_recruitment_comparison` | 27,300 | recruitment, MAPPO/model-based/classic/SOTA/ours |
| SP2 | `sp2/SP2_MC_capacity_comparison` | 20,280 | heterogeneous effective capacity |
| SP3 | `sp3/SP3_MC_wrench_comparison_high_power` | 20,040 runs / 38,076 checks | wrench feasibility and scalar false positives; 0 failed checks |
| SP4 | `sp4/SP4_MC_motion_comparison_high_power` | 20,070 rollouts / 21,408 checks | motion, safety and arrival; 0 failed checks |
| SP5 | `sp5/SP5_MC_cooperative_transport_high_power` | 20,040 rollouts / 20,040 checks | rigid payload transport with solid-load clearance; 0 failed checks |
| SP6 | `sp6/SP6_MC_robustness_comparison_high_power` | 20,000 rollouts / 20,000 checks | failures, battery, replacement and recovery; 0 failed checks |
| SP7 | `sp7/SP7_MC_communication_robustness_high_power` | 20,176 runs / 20,176 checks | communication/sensing degradation, no video rendering in statistical run; 0 failed checks |
| SP8 | `sp8/SP8_MC_fleet_ladder_high_power` | 20,000 runs / 20,000 checks | 5-50,000 AMR scale ladder, 100 seeds per scale; 0 failed checks |

## Supplementary Evidence Kept In Results

| Directory | Purpose |
|---|---|
| `sp2/SP2_MC_marginal_payoff_ablation` | Theory ablation for marginal payoff / vector potential alignment. |
| `sp3/SP3_MC_wrench_comparison_methodology_v3` | Earlier compact SP3 wrench run retained for representative videos and traceability. |
| `sp3/SP3_POSE_suite_euler_lagrange_transport` | Euler-Lagrange/Hamiltonian pose-control videos and standardized pose metrics. |
| `sp4/SP4_MC_motion_comparison` | Earlier compact SP4 motion run retained for representative videos and traceability. |
| `sp4/SP4_MC_explicit_control_law` | Explicit AMR hand-point/HOCBF motion supplement: 432 rollouts, 504 checks, 0 failed checks; includes manual explicit-method MP4. |
| `sp5/SP5_MC_explicit_control_law` | Explicit AMR vGNE-CBF transport supplement: 432 rollouts, 0 failed checks; explicit cargo reaches targets in all paired worlds; includes manual explicit cargo MP4. |
| `sp6/SP6_MC_explicit_control_law` | Explicit required-wrench recovery supplement: 360 rollouts, 0 failed checks; includes manual ours-recovery MP4. |
| `sp5/SP5_MC_cooperative_transport` | Earlier 3,000-run SP5 canonical with long MP4 videos retained for qualitative review. |
| `sp6/SP6_MC_robustness_comparison` | Earlier 4,000-run SP6 canonical with long MP4 recovery videos retained for qualitative review. |
| `sp7/SP7_MC_communication_robustness_paper` | Earlier 832-run SP7 statistical run retained for traceability. |
| `sp8/SP8_MC_fleet_ladder_extended` | Earlier 600-run SP8 fleet ladder retained for traceability. |
| `sp8/SP8_MC_scalability_warehouse` | Compact SP8 run with representative MP4 videos. |

## Paper Figures

Run:

```powershell
python scripts/generate_paper_figures.py
```

Each canonical SP directory receives a `paper_figures/` folder with PDF and PNG figures. The global index is `results/PAPER_FIGURES_INDEX.md`.

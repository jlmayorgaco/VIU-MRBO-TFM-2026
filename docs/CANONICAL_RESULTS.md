# Canonical Results Register

This file defines which artifacts are part of the official SP1-SP8 pipeline evidence. Anything outside these paths is exploratory unless it is promoted here.

## Canonical Experiment Set

| SP | Scientific question | Canonical config | Canonical result path | Primary evidence |
|---|---|---|---|---|
| SP1 | Which AMRs should be recruited for heterogeneous load demands? | `configs/experiments/sp1/SP1_MC_recruitment_comparison.yaml` | `results/sp1/SP1_MC_recruitment_comparison/` | allocation metrics, load status, rankings, videos |
| SP2 | Which coalitions are capacity-feasible under heterogeneous robot/load limits? | `configs/experiments/sp2/SP2_MC_capacity_comparison.yaml` | `results/sp2/SP2_MC_capacity_comparison/` | capacity satisfaction, cost, rankings, videos |
| SP3 | Can assigned coalitions generate the required planar wrench? | `configs/experiments/sp3/SP3_MC_wrench_comparison_high_power.yaml` plus compact/video run `SP3_MC_wrench_comparison_methodology_v3.yaml` plus pose supplement `SP3_POSE_suite_euler_lagrange_transport.yaml` | `results/sp3/SP3_MC_wrench_comparison_high_power/` plus videos in `results/sp3/SP3_MC_wrench_comparison_methodology_v3/` plus `results/sp3/SP3_POSE_suite_euler_lagrange_transport/` | high-power wrench residuals, false positives, standardized pose metrics, pose videos |
| SP4 | Can coalitions remain coordinated during motion/control constraints? | `configs/experiments/sp4/SP4_MC_motion_comparison_high_power.yaml` plus compact/video run `SP4_MC_motion_comparison.yaml` plus explicit-control supplement `SP4_MC_explicit_control_law.yaml` | `results/sp4/SP4_MC_motion_comparison_high_power/` plus videos in `results/sp4/SP4_MC_motion_comparison/` plus `results/sp4/SP4_MC_explicit_control_law/` | high-power trajectory metrics, safety/control figures, videos, explicit AMR control-law negative result |
| SP5 | Can cooperative transport avoid obstacles/traffic while preserving formation? | `configs/experiments/sp5/SP5_MC_cooperative_transport_high_power.yaml` plus video run `SP5_MC_cooperative_transport.yaml` plus explicit-control supplement `SP5_MC_explicit_control_law.yaml` | `results/sp5/SP5_MC_cooperative_transport_high_power/` plus videos in `results/sp5/SP5_MC_cooperative_transport/` plus `results/sp5/SP5_MC_explicit_control_law/` | target error, safety, obstacle clearance, MC statistics, videos and explicit AMR cargo-control supplement |
| SP6 | Can the system recover from failures/battery degradation during load transport? | `configs/experiments/sp6/SP6_MC_robustness_comparison_high_power.yaml` plus video run `SP6_MC_robustness_comparison.yaml` plus explicit-control supplement `SP6_MC_explicit_control_law.yaml` | `results/sp6/SP6_MC_robustness_comparison_high_power/` plus videos in `results/sp6/SP6_MC_robustness_comparison/` plus `results/sp6/SP6_MC_explicit_control_law/` | recovery time, replacement behavior, safety, MC statistics, videos and explicit required-wrench recovery supplement |
| SP7 | How do communication radius, packet loss, delays, jitter and sensing degradation affect cooperative transport? | `configs/experiments/sp7/SP7_MC_communication_robustness_high_power.yaml` | `results/sp7/SP7_MC_communication_robustness_high_power/` | temporal connectivity, relay metrics, sensing, transport success, paper figures |
| SP8 | At warehouse scale, which centralized methods become impractical and which distributed/hierarchical methods retain useful wrench-aware transport performance? | `configs/experiments/sp8/SP8_MC_fleet_ladder_high_power.yaml` plus compact video run `SP8_MC_scalability_warehouse.yaml` | `results/sp8/SP8_MC_fleet_ladder_high_power/` plus compact videos in `results/sp8/SP8_MC_scalability_warehouse/` | timeout/intractability, wrench success, throughput, complexity, resource-normalized rankings, videos |

## Current SP3-SP8 High-Power Runs

Last regenerated in this workspace:

- SP3 wrench feasibility: `20,040` runs, `38,076` checks, `0` failed checks, `334` seeds, `10` methods, `6` scenario families.
- SP4 motion/control: `20,070` rollouts, `21,408` checks, `0` failed checks, `223` seeds, `15` methods, `6` scenario families.
- SP5 cooperative transport: `20,040` runs, `20,040` checks, `0` failed checks, `334` seeds, `10` methods, `6` scenario families.
- SP6 operational robustness: `20,000` runs, `20,000` checks, `0` failed checks, `250` seeds, `10` methods, `8` scenario families.
- SP7 communication/sensing robustness: `20,176` runs, `20,176` checks, `0` failed checks, `97` seeds, `8` methods, `6` scenario families and 5 named communication profiles plus randomized profiles.
- SP8 fleet ladder: `20,000` runs, `20,000` checks, `0` failed checks, `100` seeds per scale, `10` methods and 20 fleet sizes.

SP3, SP4, SP5 and SP7 are intentionally slightly above `20,000` because preserving balanced Cartesian products over scenarios, seeds and methods is preferable to dropping scenarios or methods to hit a round number exactly. SP6 and SP8 land exactly on `20,000`.

## Current Explicit AMR Control-Law Supplements

The explicit closed-form AMR control law is documented in `docs/EXPLICIT_AMR_CONTROL_LAW.md` and implemented in `src/viu_mrob_tfm/control/explicit_law.py`.

- SP4 explicit motion: `results/sp4/SP4_MC_explicit_control_law/`, `432` rollouts, `504` checks, `0` failed checks. Result: reaches targets but does not improve collision or gap versus direct/CBF.
- SP5 explicit transport: `results/sp5/SP5_MC_explicit_control_law/`, `432` rollouts, `0` failed checks. Result: `ours_explicit_vgne_cbf_cargo` reaches targets in all paired worlds and ranks third behind reference and SOTA VO cargo; explicit push does not beat tensor on residual.
- SP6 explicit recovery: `results/sp6/SP6_MC_explicit_control_law/`, `360` rollouts, `0` failed checks. Result: improves physical traceability of required-wrench recovery, but does not prove significant lost-load/completion gains over the chosen baselines.

## Current SP7 Communication Run

Current promoted statistical run:

- Runs: `20,176`
- Theory/audit failed checks: `0`
- Main figures:
  - `results/sp7/SP7_MC_communication_robustness_high_power/figures/sp7_connectivity_vs_radius_by_method.png`
  - `results/sp7/SP7_MC_communication_robustness_high_power/figures/sp7_transport_success_under_network_stress.png`
  - `results/sp7/SP7_MC_communication_robustness_high_power/figures/sp7_relay_temporal_connectivity.png`
  - `results/sp7/SP7_MC_communication_robustness_high_power/figures/sp7_packet_loss_delay_heatmap.png`
  - `results/sp7/SP7_MC_communication_robustness_high_power/paper_figures/paper_metric_heatmap.pdf`

SP7 result interpretation:

- The current high-power run is the promoted statistical SP7 run. It separates Monte Carlo inference from video rendering.
- It verifies that the pipeline measures packet delivery, control packets, algebraic connectivity, direct vs relay connectivity, temporal connectivity, sensing coverage, outage duration and transport success on shared SP5 worlds.
- It includes 6 scenario families, 5 named communication/sensing profiles, randomized MC profiles, 97 seeds and 8 methods.

## Current SP8 Scalability Runs

Last regenerated in this workspace:

- Extended scale runs: `20,000`
- Extended scale fleet ladder: `5, 10, 25, 50, 100, 250, 500, 1000, 1250, 1500, 2000, 2500, 5000, 7500, 10000, 12500, 15000, 20000, 25000, 50000` AMR with `100` seeds per scale
- Extended scale max loads: `12.500`
- Compact/video runs retained separately: `150`
- Theory/audit failed checks: `0` in both current SP8 runs
- Methods: `10`
- Main extended figures:
  - `results/sp8/SP8_MC_fleet_ladder_high_power/figures/sp8_runtime_scaling_loglog.png`
  - `results/sp8/SP8_MC_fleet_ladder_high_power/figures/sp8_timeout_boundary.png`
  - `results/sp8/SP8_MC_fleet_ladder_high_power/figures/sp8_wrench_success_by_scale.png`
  - `results/sp8/SP8_MC_fleet_ladder_high_power/figures/sp8_quality_complexity_pareto.png`
- Compact video figures:
  - `results/sp8/SP8_MC_scalability_warehouse/figures/sp8_runtime_scaling_loglog.png`
  - `results/sp8/SP8_MC_scalability_warehouse/figures/sp8_timeout_boundary.png`
  - `results/sp8/SP8_MC_scalability_warehouse/figures/sp8_wrench_success_by_scale.png`
  - `results/sp8/SP8_MC_scalability_warehouse/figures/sp8_quality_complexity_pareto.png`
- Representative videos:
  - `results/sp8/SP8_MC_scalability_warehouse/videos/sp8_scale_ladder_scale_64r_16l_seed9810_classic_local_greedy_seed9810.mp4`
  - `results/sp8/SP8_MC_scalability_warehouse/videos/sp8_scale_ladder_scale_64r_16l_seed9810_ours_wrench_market_hierarchical_seed9810.mp4`

SP8 result interpretation:

- The high-power fleet ladder is the canonical scale plot evidence; the compact run remains canonical for representative MP4 inspection.
- The high-power fleet ladder tests 5-50.000 AMR and 1-12.500 loads with static/mobile obstacles, moving loads, wrench/torque checks, transport risk proxies and complexity/resource metrics. The duplicate `10000` requested in the scale ladder was normalized to one point to avoid overweighting that scale.
- In the extended run, the centralized coalition oracle declares timeout increasingly with scale (`H8.1`, Holm reject). The hierarchical wrench-market method beats classic local greedy on task completion (`H8.2`, Holm reject) and beats expanded Hungarian on wrench feasibility (`H8.3`, Holm reject).
- The model is mesoscopic/vectorized. It is appropriate for scalability and intractability claims, not for full contact dynamics, RF propagation or hardware deployment claims.
- `SP8_MC_scalability_warehouse_full.yaml` remains useful for 1000-3000 AMR warehouse/peak scenarios with multiple seeds and videos; the promoted fleet ladder now provides the high-power 20-scale statistical evidence.

## Promotion Rule

An experiment may be promoted to canonical only if it has:

- A config in `configs/experiments/sp*/`.
- A result directory under `results/sp*/`.
- `report.md`, `tables/runs.csv`, `tables/summary.csv`, `tables/performance_ranking.csv`, `tables/hypothesis_results.csv` where applicable.
- A `theory_audit.json` or equivalent audit artifact with `failed_checks = 0`, except when a failure is the explicit scientific phenomenon being demonstrated and is labeled as such.
- Clear method taxonomy columns: `method_family`, `method_scope`, `method_ownership`, `method_variant`, `method_comparison_group`.

## Non-Canonical Artifacts

Diagnostic configs, smoke runs, draft plots and one-off videos may remain in the repository while developing, but they are not thesis evidence until they are promoted here. When presenting results, use this file as the source of truth.

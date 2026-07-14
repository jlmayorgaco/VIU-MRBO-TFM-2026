# Canonical Results Register

This file defines which artifacts are part of the official integrated certificate and SP0--SP8 pipeline evidence. Anything outside these paths is exploratory unless it is promoted here. SP0 uses an explicit protocol lifecycle register because its CPU and full-budget versions have different claim scopes.

## Integrated Physical-Coalition Certificate

The primary end-to-end numerical evidence is `PHYSICAL_COALITION_CERTIFICATE_v1`: config `configs/experiments/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1.yaml`, code under `src/viu_mrob_tfm/physical_coalition/`, and results under `results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1/`. It executes the cumulative A0--FULL ladder on one Euler--Lagrange load model, contains 960 frozen base runs and 2,160 total unique runs after precision-only extension, and uses CPU only. Its claim scope is planar numerical simulation. FULL uses a global-candidate replacement proxy and retains a 0.14 collision rate in the obstacle/dropout family; it is not evidence of end-to-end local recovery or functional safety.


## Canonical Experiment Set

| SP | Scientific question | Canonical config | Canonical result path | Primary evidence |
|---|---|---|---|---|
| SP0 | Which distributed assignment dynamics and closures provide useful cardinality matchings across load regimes? | `configs/experiments/sp0/SP0_PROTOCOL_v1_2_CPU.yaml` | `results/sp0/SP0_PROTOCOL_v1_2_CPU/` qualified by `results/sp0/SP0_AUDIT_v1/` | frozen CPU-resource-constrained campaign, 15,436 base evaluations, closure attribution, paired inference, figures and videos |
| SP1 | How do homogeneous population dynamics and integer closure recruit quorum coalitions? | `configs/experiments/sp1/SP1_HOMOGENEOUS_v1_1.yaml` | `results/sp1/SP1_HOMOGENEOUS_v1_1/` | 900 paired worlds, 7,200 runs, RAW/closed separation, potential audit and five frozen paired contrasts |
| SP2 | Which coalitions are capacity-feasible under heterogeneous robot/load limits? | `configs/experiments/sp2/SP2_HETEROGENEOUS_GAME_v1_2.yaml` | `results/sp2/SP2_HETEROGENEOUS_GAME_v1_2/` | 480 paired worlds, 6,720 runs, fitness-by-dynamics comparison, RAW/closed attribution and theory audit |
| SP3 | Can a robot--load--slot game seek a wrench-feasible equilibrium and close a mechanically certified coalition? | `configs/experiments/sp3/SP3_WRENCH_NASH_GAME_v1_1.yaml` | `results/sp3/SP3_WRENCH_NASH_GAME_v1_1/` | 600 worlds, 7,200 runs, independent QP/KKT audit, RAW/CLOSED attribution, guarded closure and consensus sensitivity |
| SP4 | Can a wrench-selected coalition recruit physically to fixed contacts through a constrained distributed primitive game? | configs/experiments/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3.yaml | results/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3/ | 108 paired worlds, 1,188 runs, dynamic-unicycle plant, exact-potential/KKT audit, RAW/SAFE/EXEC separation, zero guarded collisions and scaling to 12 robots |
| SP5 | Can a post-docking coalition transport an extended payload without conflating safe commands with executed mechanics? | `configs/experiments/sp5/SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2.yaml` | `results/sp5/SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2/` | 108 paired worlds, 864 CPU runs, immutable freeze before seed opening, RAW/SAFE/EXEC wrench separation, no pose repair, collisions/timeouts preserved and Holm decisions |
| SP6 | Can the system recover from failures/battery degradation during load transport? | `configs/experiments/sp6/SP6_MC_robustness_comparison_high_power.yaml` plus video run `SP6_MC_robustness_comparison.yaml` plus explicit-control supplement `SP6_MC_explicit_control_law.yaml` | `results/sp6/SP6_MC_robustness_comparison_high_power/` plus videos in `results/sp6/SP6_MC_robustness_comparison/` plus `results/sp6/SP6_MC_explicit_control_law/` | recovery time, replacement behavior, safety, MC statistics, videos and explicit required-wrench recovery supplement |
| SP7 | How do communication radius, packet loss, delays, jitter and sensing degradation affect cooperative transport? | `configs/experiments/sp7/SP7_MC_communication_robustness_high_power.yaml` | `results/sp7/SP7_MC_communication_robustness_high_power/` | temporal connectivity, relay metrics, sensing, transport success, paper figures |
| SP8 | At warehouse scale, which centralized methods become impractical and which distributed/hierarchical methods retain useful wrench-aware transport performance? | `configs/experiments/sp8/SP8_MC_fleet_ladder_high_power.yaml` plus compact video run `SP8_MC_scalability_warehouse.yaml` | `results/sp8/SP8_MC_fleet_ladder_high_power/` plus compact videos in `results/sp8/SP8_MC_scalability_warehouse/` | timeout/intractability, wrench success, throughput, complexity, resource-normalized rankings, videos |

## Current SP0 CPU campaign

SP0 v1.2 is canonical only within its declared resource-constrained scope:

- Frozen protocol and manifest precede the confirmatory seed-opening event.
- Three independent final MAPPO seeds completed exactly 200,000 joint environment transitions each; no failed seed was replaced.
- Base counts are B0=300, B2=2,400, B3=1,536, B4=5,760, B5=4,000, B6=960 and B7=480, totaling 15,436.
- B5 alone extended from 40 to 100 worlds under the registered precision-only rule.
- Postprocessing records 108 contrasts, 165 models, 22 figures and 10 official post-hoc videos.
- The authoritative lifecycle and wording contract is `results/sp0/PROTOCOL_INDEX.md`.

Canonical status does not erase audit limitations. The v1.2 training schedule is not equivalent to v1.1's 26M budget; audited MAPPO RAW behavior fails while closure-assisted behavior succeeds; and any hypothesis with non-finite estimates or intervals remains unsupported. The stopped `SP0_PROTOCOL_v1_1` CPU process is pre-freeze engineering evidence only and must never be mixed into v1.2 rankings.

## Current SP3--SP8 Campaigns

Last regenerated in this workspace:

- SP3 wrench game v1.1: `7,200` runs, `600` paired worlds, theory audit PASS, `100` seeds per scenario, `12` methods and `6` scenario families. The historical 20,040-run campaign remains non-canonical context.
- SP4 docking game v3: 1,188 runs, 108 paired worlds, theory audit PASS, 0 initial collisions, 6 seeds per scenario/scale, 11 methods, 6 scenarios and N={4,8,12}. Guarded methods had zero swept collisions; replicator safe success was 0.2685 with 0.7315 timeout.
- SP5 payload transport v2: `864` runs, `108` paired worlds, theory/semantics audit PASS, `6` confirmatory seeds, `8` methods, `6` scenarios and `N={4,8,12}`. Local CBF achieved 0.593 safe success with zero collisions; Hamiltonian+CBF achieved 0.426 and zero collisions versus 0.167 success/0.833 collision in RAW.
- SP5 legacy note: the 20,040-run high-power package and 432-run explicit supplement remain historical because the legacy plant projected payload/robot poses after integration; they are not canonical evidence for continuous safety.
- SP6 operational robustness: `20,000` runs, `20,000` checks, `0` failed checks, `250` seeds, `10` methods, `8` scenario families.
- SP7 communication/sensing robustness: `20,176` runs, `20,176` checks, `0` failed checks, `97` seeds, `8` methods, `6` scenario families and 5 named communication profiles plus randomized profiles.
- SP8 fleet ladder: `20,000` runs, `20,000` checks, `0` failed checks, `100` seeds per scale, `10` methods and 20 fleet sizes.

SP4 uses the frozen 1,188-run v3 docking campaign and SP5 uses the frozen 864-run v2 payload campaign. Their invalid or post-integration-projected predecessors remain non-canonical audit context. SP7 remains a historical high-row-count descriptive package rather than being strengthened by row count alone.

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

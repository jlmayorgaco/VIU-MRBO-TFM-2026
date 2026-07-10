# SP6 Video Index

Cada MP4 muestra transporte cooperativo de carga con evento de resiliencia: reclutamiento a slots, movimiento de payload, fallo/degradacion, reemplazo/reasignacion y estado final.

## sp6_battery-depletion-reallocation_reference_model-based-reference_centralized_centralized-resilient-recovery_reference-resilient-oracle_seed7658.mp4

- Scenario: `battery_depletion_reallocation` / `battery_depletion_reallocation_v00`.
- Method: `reference_resilient_oracle` (Reference centralized resilient recovery).
- Seed: `7658`.
- Event: `battery_depletion_reallocation` at `18.360000000000003` s.
- Size: `8` AMR, `3` loads.
- Objective: Recover payload transport after the disruption while preserving slot formation, wrench feasibility and final load pose.
- Metrics: recovery_success=0.0000; completion=0.5000; target_rate=0.5000; min_wrench_margin=-0.0342; pause_s=0.7000; degraded_s=5.6000; replacement_s=0.1200; pose_error_m=2.6256; collision_rate=0.0000
- Snapshot: `sp6_battery-depletion-reallocation_reference_model-based-reference_centralized_centralized-resilient-recovery_reference-resilient-oracle_seed7658.png`.

## sp6_blocked-corridor-recovery_baseline_classic_decentralized_local-greedy-recovery_classic-decentralized-greedy-recovery_seed7652.mp4

- Scenario: `blocked_corridor_recovery` / `blocked_corridor_recovery_v00`.
- Method: `classic_decentralized_greedy_recovery` (Classic decentralized greedy recovery).
- Seed: `7652`.
- Event: `blocked_corridor_recovery` at `20.400000000000002` s.
- Size: `9` AMR, `3` loads.
- Objective: Recover payload transport after the disruption while preserving slot formation, wrench feasibility and final load pose.
- Metrics: recovery_success=0.0000; completion=0.3333; target_rate=0.3333; min_wrench_margin=0.0000; pause_s=0.0000; degraded_s=0.0000; replacement_s=0.0400; pose_error_m=3.4329; collision_rate=0.0000
- Snapshot: `sp6_blocked-corridor-recovery_baseline_classic_decentralized_local-greedy-recovery_classic-decentralized-greedy-recovery_seed7652.png`.

## sp6_monte-carlo_baseline_sota_centralized_centralized-cbf-recovery_cbf-recovery_seed7661.mp4

- Scenario: `monte_carlo` / `monte_carlo_infeasible_load_detection_seed7661`.
- Method: `cbf_recovery` (CBF recovery).
- Seed: `7661`.
- Event: `infeasible_load_detection` at `21.11739381478095` s.
- Size: `6` AMR, `4` loads.
- Objective: Recover payload transport after the disruption while preserving slot formation, wrench feasibility and final load pose.
- Metrics: recovery_success=0.0000; completion=0.5000; target_rate=0.5000; min_wrench_margin=-1.0000; pause_s=41.1600; degraded_s=0.0000; replacement_s=40.9926; pose_error_m=5.8267; collision_rate=0.0000
- Snapshot: `sp6_monte-carlo_baseline_sota_centralized_centralized-cbf-recovery_cbf-recovery_seed7661.png`.

## sp6_multi-load-priority-shift_proposed_model-based_decentralized_smith-qr-recovery_smith-qr-recovery_seed7652.mp4

- Scenario: `multi_load_priority_shift` / `multi_load_priority_shift_v00`.
- Method: `smith_qr_recovery` (Smith-QR recovery).
- Seed: `7652`.
- Event: `multi_load_priority_shift` at `19.720000000000002` s.
- Size: `10` AMR, `4` loads.
- Objective: Recover payload transport after the disruption while preserving slot formation, wrench feasibility and final load pose.
- Metrics: recovery_success=0.0000; completion=0.6667; target_rate=0.6667; min_wrench_margin=-1.0000; pause_s=19.7400; degraded_s=1.6800; replacement_s=4.5000; pose_error_m=1.9788; collision_rate=0.0000
- Snapshot: `sp6_multi-load-priority-shift_proposed_model-based_decentralized_smith-qr-recovery_smith-qr-recovery_seed7652.png`.

## sp6_robot-dropout-mid-task_reference_model-based-reference_centralized_centralized-resilient-recovery_reference-resilient-oracle_seed7656.mp4

- Scenario: `robot_dropout_mid_task` / `robot_dropout_mid_task_v00`.
- Method: `reference_resilient_oracle` (Reference centralized resilient recovery).
- Seed: `7656`.
- Event: `robot_dropout_mid_task` at `18.360000000000003` s.
- Size: `8` AMR, `3` loads.
- Objective: Recover payload transport after the disruption while preserving slot formation, wrench feasibility and final load pose.
- Metrics: recovery_success=1.0000; completion=1.0000; target_rate=1.0000; min_wrench_margin=-0.6667; pause_s=1.5400; degraded_s=12.7400; replacement_s=6.2800; pose_error_m=0.3686; collision_rate=0.0000
- Snapshot: `sp6_robot-dropout-mid-task_reference_model-based-reference_centralized_centralized-resilient-recovery_reference-resilient-oracle_seed7656.png`.


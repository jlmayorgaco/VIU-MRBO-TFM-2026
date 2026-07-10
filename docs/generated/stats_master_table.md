| SP | Hipotesis | Metrica | n | p-Holm | Efecto | Veredicto |
| --- | --- | --- | --- | --- | --- | --- |
| SP1 | H01_methods_differ_theoretical_gap | optimality_gap_vs_oracle | 2100 | 0 | 0.6063 | rechaza H0 |
| SP1 | H02_mappo_lower_gap_than_imitation | optimality_gap_vs_oracle | 2100 | 0 | -0.8951 | rechaza H0 |
| SP1 | H03_mappo_lower_gap_than_hungarian_classic | optimality_gap_vs_oracle | 2100 | 1.56e-182 | -0.6904 | rechaza H0 |
| SP1 | H04_smith_lower_runtime_than_mappo | runtime_ms | 2100 | 0 | -1.092 | rechaza H0 |
| SP1 | H05_mappo_higher_coalition_success_than_smith | coalition_success_rate | 2100 | 0 | 1.482 | rechaza H0 |
| SP2 | H01_methods_differ_capacity_gap | optimality_gap_vs_oracle | 1560 | 0 | 0.71 | rechaza H0 |
| SP2 | H01b_methods_differ_capacity_ceiling_gap | capacity_gap_vs_capacity_oracle | 1560 | 5.68e-10 | 0.008093 | rechaza H0 |
| SP2 | H02_primal_dual_higher_capacity_success_than_greedy | capacity_success_rate | 1560 | 1 | -0.7076 | no rechaza H0 |
| SP2 | H03_neural_lower_gap_than_linear_imitation | optimality_gap_vs_oracle | 1560 | 1.17e-26 | -0.2328 | rechaza H0 |
| SP2 | H04_local_primal_dual_lower_messages_than_oracle | communication_messages | 1560 | 6.85e-18 | -0.362 | rechaza H0 |
| SP2 | H05_smith_lower_runtime_than_neural | runtime_ms | 1560 | 8.71e-256 | -1.589 | rechaza H0 |
| SP3 | H3_HP_1_scalar_false_positives_rotational_loads | false_positive_rate | 2004 | 8.47e-198 | 0.9998 | rechaza H0 |
| SP3 | H3_HP_2_smith_wrench_lower_residual_than_capacity | wrench_residual_feasible_available | 2004 | 1 | -0.0316 | no rechaza H0 |
| SP3 | H3_HP_3_capacity_greedy_more_infeasible_assignments_than_support_dual | fp_given_assigned | 2004 | 1 | 0.0316 | no rechaza H0 |
| SP3 | H3_HP_4_support_dual_lower_gap_than_cbba | optimality_gap_vs_wrench_oracle | 2004 | 1 | 0.02293 | no rechaza H0 |
| SP3 | H3_HP_5_methods_differ_wrench_gap | optimality_gap_vs_wrench_oracle | 2004 | 0 | 0.1175 | rechaza H0 |
| SP4 | H4_HP_1_reference_reduces_collision_vs_direct | collision_rate | 1338 | 2.52e-183 | -0.8525 | rechaza H0 |
| SP4 | H4_HP_2_cbf_reduces_collision_vs_direct | collision_rate | 1338 | 8.88e-183 | -0.8471 | rechaza H0 |
| SP4 | H4_HP_3_tensor_reduces_collision_vs_direct | collision_rate | 1338 | 1.41e-183 | -0.843 | rechaza H0 |
| SP4 | H4_HP_4_energy_smith_reduces_energy_vs_cbf | energy_proxy_wh | 1338 | 1 | -0.06049 | no rechaza H0 |
| SP4 | H4_HP_5_methods_differ_gap_vs_reference | performance_gap_vs_reference | 1338 | 0 | 0.3687 | rechaza H0 |
| SP5 | H5_1_reference_reduces_gap_vs_classic_apf | performance_gap_vs_reference | 2004 | 0 | -31.63 | rechaza H0 |
| SP5 | H5_2_ours_hamiltonian_reduces_formation_break_vs_sota_vo_cargo | formation_broken_rate | 2004 | 0.2153 | -0.06775 | no rechaza H0 |
| SP5 | H5_3_ours_tensor_improves_target_reached_vs_classic_push | target_reached | 2004 | 0.5356 | -0.0316 | no rechaza H0 |
| SP5 | H5_4_methods_differ_transport_score | score_value | 2004 | 0 | 0.7322 | rechaza H0 |
| SP6 | H6.1_ours_reduces_lost_load_rate_vs_classic_greedy | lost_load_rate | 2000 | 2.55e-05 | -0.1359 | rechaza H0 |
| SP6 | H6.2_ours_improves_completion_vs_smith_qr | task_completion_rate | 2000 | 0.1962 | 0.03077 | no rechaza H0 |
| SP6 | H6.3_ours_reduces_reference_gap_vs_cbba | performance_gap_vs_reference | 2000 | 2.06e-92 | -0.3084 | rechaza H0 |
| SP6 | H6.4_recovery_family_differs_on_reference_gap | performance_gap_vs_reference | 2000 | 7.19e-160 | 0.07529 | rechaza H0 |
| SP7 | H7.1_radius_improves_coalition_connectivity | coalition_connected_time_ratio | 20176 | 0 | 0.8934 | rechaza H0 |
| SP7 | H7.2_ours_connectivity_beats_classic_under_harsh_profiles | transport_network_score | 485 | 1.36e-80 | 0.8804 | rechaza H0 |
| SP7 | H7.3_methods_differ_under_intermittent_communication | transport_network_score |  | 1 | nan | no rechaza H0 |
| SP8 | H8.1_centralized_oracle_timeout_increases_with_scale | timeout_rate | 2000 | 4.93e-287 | 0.6937 | rechaza H0 |
| SP8 | H8.2_ours_hierarchical_higher_completion_than_classic_local | task_completion_rate | 2000 | 4.18e-300 | 0.7791 | rechaza H0 |
| SP8 | H8.3_ours_hierarchical_higher_wrench_feasibility_than_hungarian | wrench_feasible_rate | 2000 | 6.45e-299 | 1.167 | rechaza H0 |

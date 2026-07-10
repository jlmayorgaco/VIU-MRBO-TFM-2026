| Restriccion | Familia | SP | Evidencia | Claim seguro |
| --- | --- | --- | --- | --- |
| Quorum entero | Poblacionales con cierre entero y referencias centralizadas | SP1 | H01_methods_differ_theoretical_gap; metric=optimality_gap_vs_oracle; p-Holm=0 | El reclutamiento se evalua por brecha contra oraculo, exito y coste. |
| Heterogeneidad de capacidad | Capacity-aware, payoff marginal y comparadores aprendidos | SP2 | H01_methods_differ_capacity_gap; metric=optimality_gap_vs_oracle; p-Holm=0 | La cardinalidad deja de ser proxy suficiente de servicio. |
| Wrench vectorial | Verificacion explicita de contactos y residual wrench | SP3 | H3_HP_1_scalar_false_positives_rotational_loads; metric=false_positive_rate; p-Holm=8.47e-198 | El criterio escalar puede producir falsos positivos fisicos. |
| Movimiento seguro | CBF, campos con barrera y referencias temporales | SP4 | H4_HP_1_reference_reduces_collision_vs_direct; metric=collision_rate; p-Holm=2.52e-183 | La llegada debe leerse junto con colision, despeje, energia y tiempo. |
| Transporte con formacion | Cargo/caging/control de pose | SP5 | H5_1_reference_reduces_gap_vs_classic_apf; metric=performance_gap_vs_reference; p-Holm=0 | Mover robots no equivale a transportar una carga extendida. |
| Fallos, bateria e inviabilidad | Recovery-aware y guarded/wrench-market | SP6 | H6.1_ours_reduces_lost_load_rate_vs_classic_greedy; metric=lost_load_rate; p-Holm=2.55e-05 | La robustez se mide por recuperacion y perdida de carga. |
| Comunicacion degradada | Connectivity-aware, relay y topologia temporal | SP7 | H7.1_radius_improves_coalition_connectivity; metric=coalition_connected_time_ratio; p-Holm=0 | La conectividad temporal condiciona el transporte cooperativo. |
| Escala e intratabilidad | Distribuidas, jerarquicas y tensor/market | SP8 | H8.1_centralized_oracle_timeout_increases_with_scale; metric=timeout_rate; p-Holm=4.93e-287 | La escala cambia la utilidad practica de las familias. |
| Brecha teoria-implementacion | Predicho-vs-medido en CoppeliaSim/Pioneer | SP9 | pending | Solo se reporta si existen CSV, figuras y manifest reales. |

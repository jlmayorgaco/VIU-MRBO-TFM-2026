# SP1_SCALE_QPG_BENCHMARK_v2_preview

## Resultado principal

El preview bloqueante aprobó los gates de integridad. La campaña full no se interpreta desde este paquete.

| experiment   | method                    |   worlds |   feasibility |   feasibility_ci_lower |   feasibility_ci_upper |   median_all_world_cost |   median_common_candidate_distance_m |   median_payload_bytes |   median_time_to_first_feasible_s |   median_wall_time_s |   censoring_rate |
|:-------------|:--------------------------|---------:|--------------:|-----------------------:|-----------------------:|------------------------:|-------------------------------------:|-----------------------:|----------------------------------:|---------------------:|-----------------:|
| PREVIEW      | Capacity-CBBA             |       30 |      0.7      |               0.521242 |               0.833353 |                1395.11  |                             1085.2   |                  44184 |                          0.647245 |             0.802646 |         0.933333 |
| PREVIEW      | SCALE-QPG-LogitBR-LocalAR |       30 |      0.633333 |               0.455136 |               0.781261 |                1646.45  |                              998.902 |                 309320 |                          0.323457 |             0.676556 |         0        |
| PREVIEW      | Weighted-Pair-GRAPE       |       30 |      0.866667 |               0.703187 |               0.946903 |                 833.425 |                              791.733 |                 203336 |                          2.83988  |             3.07     |         0.966667 |

## Comparaciones emparejadas

| comparison                                       | metric                | common_feasible_only   |   pairs |   median_paired_difference |   bootstrap_ci_lower |   bootstrap_ci_upper |   p_raw |   rank_biserial |   p_holm |
|:-------------------------------------------------|:----------------------|:-----------------------|--------:|---------------------------:|---------------------:|---------------------:|--------:|----------------:|---------:|
| SCALE-QPG-LogitBR-LocalAR vs Capacity-CBBA       | all_world_cost        | False                  |       0 |                        nan |                  nan |                  nan |       1 |               0 |        1 |
| SCALE-QPG-LogitBR-LocalAR vs Capacity-CBBA       | distance_total_m      | True                   |       0 |                        nan |                  nan |                  nan |       1 |               0 |        1 |
| SCALE-QPG-LogitBR-LocalAR vs Capacity-CBBA       | payload_bytes_total   | False                  |       0 |                        nan |                  nan |                  nan |       1 |               0 |        1 |
| SCALE-QPG-LogitBR-LocalAR vs Capacity-CBBA       | first_feasible_time_s | False                  |       0 |                        nan |                  nan |                  nan |       1 |               0 |        1 |
| SCALE-QPG-LogitBR-LocalAR vs Capacity-CBBA       | feasibility           | False                  |       0 |                        nan |                  nan |                  nan |       1 |             nan |        1 |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-Pair-GRAPE | all_world_cost        | False                  |       0 |                        nan |                  nan |                  nan |       1 |               0 |        1 |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-Pair-GRAPE | distance_total_m      | True                   |       0 |                        nan |                  nan |                  nan |       1 |               0 |        1 |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-Pair-GRAPE | payload_bytes_total   | False                  |       0 |                        nan |                  nan |                  nan |       1 |               0 |        1 |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-Pair-GRAPE | first_feasible_time_s | False                  |       0 |                        nan |                  nan |                  nan |       1 |               0 |        1 |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-Pair-GRAPE | feasibility           | False                  |       0 |                        nan |                  nan |                  nan |       1 |             nan |        1 |

## Gates

```json
{
  "zero_double_assignment": true,
  "zero_accepted_version_violations": true,
  "strict_potential_non_decreasing": true,
  "zero_cycles": true,
  "message_accounting_reproducible": true,
  "local_recovery_scope_enforced": true,
  "same_instance_for_all_methods": true,
  "no_nan_inf_core_metrics": true,
  "exact_world_count": true,
  "exact_operational_run_count": true,
  "checkpoint_resume_available": true,
  "task_failures_zero": true
}
```

## Dominio separado de servicios

C9 conserva GRAPE-S y Pair-GRAPE-S en servicios discretos. Weighted-GRAPE es una adaptación escalar y no se presenta como GRAPE-S canónico.

## Claims permitidos

- La salida física de SCALE-QPG es atómica en todos los runs auditados.
- La fase strict-BR solo acepta incrementos exactos positivos del potencial.
- El payload lógico se contabiliza por eventos y rutas del grafo.
- Los resultados se limitan a reclutamiento escalar SP1 en simulación.

## Claims prohibidos

- Superioridad universal sobre CBBA o GRAPE.
- Convergencia global o optimalidad social.
- Equivalencia de Weighted-GRAPE con GRAPE-S canónico.
- Validación de transporte físico, contacto o hardware.

## Contabilidad

- Tareas: 30.
- Censuras: 184.
- Fallbacks globales: 0.
- Runtime del driver: 213.554 s.

Conclusión seleccionada: F. Existen regímenes distintos y no hay dominador.

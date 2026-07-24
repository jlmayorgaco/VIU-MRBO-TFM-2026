# SP1_SCALE_QPG_BENCHMARK_v2_preview

## Resultado principal

El preview bloqueante no aprobó los gates de integridad y rendimiento. La campaña full no se ejecuta desde este paquete.

| experiment      | method                         |   worlds |   feasibility |   feasibility_ci_lower |   feasibility_ci_upper |   median_all_world_cost |   median_common_candidate_distance_m |   median_payload_bytes |   median_time_to_first_feasible_s |   median_wall_time_s |   censoring_rate |
|:----------------|:-------------------------------|---------:|--------------:|-----------------------:|-----------------------:|------------------------:|-------------------------------------:|-----------------------:|----------------------------------:|---------------------:|-----------------:|
| PREVIEW         | Capacity-CBBA                  |       30 |      0.566667 |              0.391973  |               0.726225 |                1395.11  |                              697.136 |                  44184 |                          0.126587 |             1.14928  |         0.933333 |
| PREVIEW         | SCALE-QPG-LogitBR-LocalAR      |       30 |      0.6      |              0.423204  |               0.754094 |                1746.02  |                              986.612 |                 309320 |                          0.357353 |             0.917498 |         0        |
| PREVIEW         | SCALE-QPG-ReplicatorBR-LocalAR |       30 |      0.633333 |              0.455136  |               0.781261 |                1705.05  |                              991.49  |                 369280 |                          0.449477 |             1.28978  |         0        |
| PREVIEW         | Weighted-GRAPE                 |       30 |      0.666667 |              0.487801  |               0.807695 |                1481.64  |                              978.738 |                  99064 |                          0.124421 |             0.270103 |         0.966667 |
| PREVIEW         | Weighted-Pair-GRAPE            |       30 |      0.766667 |              0.590717  |               0.882076 |                 833.425 |                              741.454 |                 203336 |                          3.6732   |             4.41461  |         0.966667 |
| PREVIEW-DYNAMIC | Capacity-CBBA                  |       25 |      1        |              0.866808  |               1        |                2502.94  |                             2502.94  |                  35616 |                          3.67038  |             3.67038  |         0.68     |
| PREVIEW-DYNAMIC | SCALE-QPG-LogitBR-LocalAR      |       25 |      0.8      |              0.60869   |               0.911394 |                3951.12  |                             3859.45  |                  43424 |                          0        |             1.09251  |         0        |
| PREVIEW-DYNAMIC | SCALE-QPG-ReplicatorBR-LocalAR |       25 |      0.84     |              0.653464  |               0.935965 |                3941.56  |                             3886.05  |                  52536 |                          0        |             1.10567  |         0        |
| PREVIEW-DYNAMIC | Weighted-GRAPE                 |       25 |      0.24     |              0.114963  |               0.434297 |               12529.3   |                             3621.08  |                 123432 |                          0.927139 |             1.40025  |         1        |
| PREVIEW-DYNAMIC | Weighted-Pair-GRAPE            |       25 |      0.2      |              0.0886058 |               0.39131  |               12679.2   |                             2885.55  |                 174800 |                          5.03812  |             5.51748  |         1        |

## Comparaciones emparejadas

| comparison                                            | metric                | common_feasible_only   |   pairs |   median_paired_difference |   bootstrap_ci_lower |   bootstrap_ci_upper |       p_raw |   rank_biserial |      p_holm |
|:------------------------------------------------------|:----------------------|:-----------------------|--------:|---------------------------:|---------------------:|---------------------:|------------:|----------------:|------------:|
| SCALE-QPG-LogitBR-LocalAR vs Capacity-CBBA            | all_world_cost        | False                  |      30 |                123.134     |         -174.059     |           259.963    | 0.855272    |       0.0408602 | 1           |
| SCALE-QPG-LogitBR-LocalAR vs Capacity-CBBA            | distance_total_m      | True                   |      15 |                262.933     |          198.152     |           353.012    | 6.10352e-05 |       1         | 0.00115967  |
| SCALE-QPG-LogitBR-LocalAR vs Capacity-CBBA            | payload_bytes_total   | False                  |      30 |             263680         |       132708         |        645636        | 1.86265e-09 |       1         | 6.70552e-08 |
| SCALE-QPG-LogitBR-LocalAR vs Capacity-CBBA            | first_feasible_time_s | False                  |      15 |                  0.212184  |           -0.0392062 |             0.259542 | 0.599487    |       0.166667  | 1           |
| SCALE-QPG-LogitBR-LocalAR vs Capacity-CBBA            | feasibility           | False                  |      30 |                  0.0333333 |          nan         |           nan        | 1           |     nan         | 1           |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-GRAPE           | all_world_cost        | False                  |      30 |                126.571     |           42.8841    |           301.838    | 0.0208499   |       0.47957   | 0.271048    |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-GRAPE           | distance_total_m      | True                   |      16 |                162.749     |          118.782     |           347.527    | 3.05176e-05 |       1         | 0.000640869 |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-GRAPE           | payload_bytes_total   | False                  |      30 |             207400         |        90948         |        497532        | 1.86265e-09 |       1         | 6.70552e-08 |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-GRAPE           | first_feasible_time_s | False                  |      16 |                  0.29682   |            0.262631  |             0.478485 | 3.05176e-05 |       1         | 0.000640869 |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-GRAPE           | feasibility           | False                  |      30 |                 -0.0666667 |          nan         |           nan        | 0.6875      |     nan         | 1           |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-Pair-GRAPE      | all_world_cost        | False                  |      30 |                328.392     |          215.659     |           753.042    | 0.000344958 |       0.711828  | 0.00586429  |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-Pair-GRAPE      | distance_total_m      | True                   |      17 |                332.476     |          248.164     |           741.956    | 1.52588e-05 |       1         | 0.000350952 |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-Pair-GRAPE      | payload_bytes_total   | False                  |      30 |              99824         |        46316         |        406548        | 5.58794e-09 |       0.991398  | 1.78814e-07 |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-Pair-GRAPE      | first_feasible_time_s | False                  |      17 |                  0.0595312 |           -3.53212   |             0.158242 | 0.159378    |      -0.398693  | 1           |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-Pair-GRAPE      | feasibility           | False                  |      30 |                 -0.166667  |          nan         |           nan        | 0.125       |     nan         | 1           |
| SCALE-QPG-ReplicatorBR-LocalAR vs Capacity-CBBA       | all_world_cost        | False                  |      30 |                 77.4078    |         -231.678     |           153.31     | 0.730342    |      -0.0752688 | 1           |
| SCALE-QPG-ReplicatorBR-LocalAR vs Capacity-CBBA       | distance_total_m      | True                   |      15 |                160.776     |          101.854     |           281.655    | 6.10352e-05 |       1         | 0.00115967  |
| SCALE-QPG-ReplicatorBR-LocalAR vs Capacity-CBBA       | payload_bytes_total   | False                  |      30 |             327868         |       154708         |        693800        | 1.86265e-09 |       1         | 6.70552e-08 |
| SCALE-QPG-ReplicatorBR-LocalAR vs Capacity-CBBA       | first_feasible_time_s | False                  |      15 |                  0.207334  |            0.0399044 |             0.287461 | 0.0150757   |       0.7       | 0.21106     |
| SCALE-QPG-ReplicatorBR-LocalAR vs Capacity-CBBA       | feasibility           | False                  |      30 |                  0.0666667 |          nan         |           nan        | 0.6875      |     nan         | 1           |
| SCALE-QPG-ReplicatorBR-LocalAR vs Weighted-GRAPE      | all_world_cost        | False                  |      30 |                105.787     |          -15.9344    |           174.667    | 0.119077    |       0.329032  | 1           |
| SCALE-QPG-ReplicatorBR-LocalAR vs Weighted-GRAPE      | distance_total_m      | True                   |      17 |                162.634     |          104.959     |           262.429    | 0.000656128 |       0.869281  | 0.00984192  |
| SCALE-QPG-ReplicatorBR-LocalAR vs Weighted-GRAPE      | payload_bytes_total   | False                  |      30 |             271280         |       118712         |        587167        | 1.86265e-09 |       1         | 6.70552e-08 |
| SCALE-QPG-ReplicatorBR-LocalAR vs Weighted-GRAPE      | first_feasible_time_s | False                  |      17 |                  0.392983  |            0.287084  |             0.839162 | 1.52588e-05 |       1         | 0.000350952 |
| SCALE-QPG-ReplicatorBR-LocalAR vs Weighted-GRAPE      | feasibility           | False                  |      30 |                 -0.0333333 |          nan         |           nan        | 1           |     nan         | 1           |
| SCALE-QPG-ReplicatorBR-LocalAR vs Weighted-Pair-GRAPE | all_world_cost        | False                  |      30 |                308.717     |          185.225     |           695.183    | 0.000505488 |       0.694624  | 0.00808781  |
| SCALE-QPG-ReplicatorBR-LocalAR vs Weighted-Pair-GRAPE | distance_total_m      | True                   |      18 |                375.021     |          216.646     |           695.183    | 7.62939e-06 |       1         | 0.000228882 |
| SCALE-QPG-ReplicatorBR-LocalAR vs Weighted-Pair-GRAPE | payload_bytes_total   | False                  |      30 |             162124         |        62872         |        482361        | 1.30385e-08 |       0.982796  | 4.04194e-07 |
| SCALE-QPG-ReplicatorBR-LocalAR vs Weighted-Pair-GRAPE | first_feasible_time_s | False                  |      18 |                 -0.14817   |           -2.54787   |             0.129088 | 0.0665359   |      -0.497076  | 0.798431    |
| SCALE-QPG-ReplicatorBR-LocalAR vs Weighted-Pair-GRAPE | feasibility           | False                  |      30 |                 -0.133333  |          nan         |           nan        | 0.21875     |     nan         | 1           |
| SCALE-QPG-LogitBR-LocalAR vs Capacity-CBBA            | dynamic_recourse      | False                  |      25 |                -33         |          -35         |           -30        | 1.20143e-05 |      -1         | 0.000338073 |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-GRAPE           | dynamic_recourse      | False                  |      25 |                -11         |          -15         |            -7        | 1.20143e-05 |      -1         | 0.000338073 |
| SCALE-QPG-LogitBR-LocalAR vs Weighted-Pair-GRAPE      | dynamic_recourse      | False                  |      25 |                -23         |          -26         |           -18        | 1.18945e-05 |      -1         | 0.000338073 |
| SCALE-QPG-ReplicatorBR-LocalAR vs Capacity-CBBA       | dynamic_recourse      | False                  |      25 |                -33         |          -37         |           -32        | 1.16577e-05 |      -1         | 0.000338073 |
| SCALE-QPG-ReplicatorBR-LocalAR vs Weighted-GRAPE      | dynamic_recourse      | False                  |      25 |                -13         |          -16         |            -7        | 1.17971e-05 |      -1         | 0.000338073 |
| SCALE-QPG-ReplicatorBR-LocalAR vs Weighted-Pair-GRAPE | dynamic_recourse      | False                  |      25 |                -22         |          -27         |           -20        | 1.19162e-05 |      -1         | 0.000338073 |

## Gates

```json
{
  "baselines": [
    "Capacity-CBBA",
    "Weighted-GRAPE",
    "Weighted-Pair-GRAPE"
  ],
  "per_method": {
    "SCALE-QPG-LogitBR-LocalAR": {
      "observed": {
        "static_recovered_feasibility": 0.6,
        "dynamic_recovered_feasibility": 0.8,
        "distance_ratio_to_best_baseline": 1.3630866772479906,
        "bytes_ratio_to_best_baseline": 7.000724244070252,
        "recourse_ratio_to_best_dynamic_baseline": 0.7407407407407407,
        "unaffected_coalition_integrity": 0.10526315789473684,
        "global_fallback_rate": 0.0,
        "common_feasible_static_worlds": 15,
        "common_feasible_dynamic_worlds": 1
      },
      "passed": {
        "recovered_feasibility": false,
        "common_feasible_distance": false,
        "payload_bytes": false,
        "dynamic_recourse": false,
        "unaffected_coalition_integrity": false,
        "global_fallback_rate": true
      },
      "all_passed": false
    },
    "SCALE-QPG-ReplicatorBR-LocalAR": {
      "observed": {
        "static_recovered_feasibility": 0.6333333333333333,
        "dynamic_recovered_feasibility": 0.84,
        "distance_ratio_to_best_baseline": 1.2586272316221934,
        "bytes_ratio_to_best_baseline": 8.357776570704328,
        "recourse_ratio_to_best_dynamic_baseline": 0.6779661016949152,
        "unaffected_coalition_integrity": 0.10526315789473684,
        "global_fallback_rate": 0.0,
        "common_feasible_static_worlds": 15,
        "common_feasible_dynamic_worlds": 2
      },
      "passed": {
        "recovered_feasibility": false,
        "common_feasible_distance": false,
        "payload_bytes": false,
        "dynamic_recourse": true,
        "unaffected_coalition_integrity": false,
        "global_fallback_rate": true
      },
      "all_passed": false
    }
  },
  "passed": {
    "recovered_feasibility": false,
    "common_feasible_distance": false,
    "payload_bytes": false,
    "dynamic_recourse": false,
    "unaffected_coalition_integrity": false,
    "global_fallback_rate": true
  },
  "all_passed": false
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

- Tareas: 55.
- Censuras: 328.
- Fallbacks globales: 0.
- Runtime del driver: 0.588 s.

Conclusión seleccionada: F. SCALE-QPG no supera todos los gates del preview; V2 full queda bloqueada.

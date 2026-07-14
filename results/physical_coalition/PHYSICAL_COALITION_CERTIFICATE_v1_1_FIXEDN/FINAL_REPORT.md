# Physical-coalition certificate campaign — final report

Protocol: `PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN`. CPU-only reduced-order Python simulation; no GPU, MARL training, CoppeliaSim, replacement seeds or synthetic rows.

## Execution gate

- Retained rows: 2400; unique run IDs: 2400.
- Numerical errors: 0.
- Final paired worlds by family: `{"nominal_rotation": 100, "obstacle_network_dropout": 100, "scarcity_capacity": 100, "torque_complementarity": 100}`.
- Confirmatory seeds were opened only after `frozen_manifest.json` recorded `frozen_ready_for_execution`.
- The confirmatory analysis used a fixed sample size; no optional stopping was applied.

## FULL robust-local stage

| scenario_family          |   success_rate |   physical_false_positive_rate |   mean_messages |   mean_runtime_wall_s |
|:-------------------------|---------------:|-------------------------------:|----------------:|----------------------:|
| nominal_rotation         |           1    |                           0    |          442.36 |              0.578069 |
| obstacle_network_dropout |           0.89 |                           0.11 |          631.84 |              0.721745 |
| scarcity_capacity        |           0.92 |                           0.08 |          503.38 |              0.460008 |
| torque_complementarity   |           1    |                           0    |          431.79 |              0.533115 |

## Confirmatory paired contrasts

| scenario_family          | before            | after             |   effect_estimate |   CI95_low |   CI95_high |       raw_p |   n_worlds |   improved_worlds |   degraded_worlds |   margin |   Holm_adjusted_p |   effect_size | decision             |
|:-------------------------|:------------------|:------------------|------------------:|-----------:|------------:|------------:|-----------:|------------------:|------------------:|---------:|------------------:|--------------:|:---------------------|
| nominal_rotation         | A0_RAW_PREF       | A1_INTEGER_QR     |              0    |       0    |     0       | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| nominal_rotation         | A1_INTEGER_QR     | A2_CAPACITY       |              0    |       0    |     0       | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| nominal_rotation         | A2_CAPACITY       | A3_WRENCH_PAIR    |              0.07 |       0.02 |     0.12025 | 0.015625    |        100 |                 7 |                 0 |        0 |       0.203125    |          0.07 | inconclusive_or_null |
| nominal_rotation         | A3_WRENCH_PAIR    | A4_MECHANICS_SAFE |              0    |       0    |     0       | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| nominal_rotation         | A4_MECHANICS_SAFE | FULL_ROBUST_LOCAL |              0    |       0    |     0       | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| scarcity_capacity        | A0_RAW_PREF       | A1_INTEGER_QR     |              0.56 |       0.46 |     0.65    | 2.77556e-17 |        100 |                56 |                 0 |        0 |       4.996e-16   |          0.56 | positive_supported   |
| scarcity_capacity        | A1_INTEGER_QR     | A2_CAPACITY       |              0.44 |       0.34 |     0.54    | 1.13687e-13 |        100 |                44 |                 0 |        0 |       1.93268e-12 |          0.44 | positive_supported   |
| scarcity_capacity        | A2_CAPACITY       | A3_WRENCH_PAIR    |             -0.16 |      -0.24 |    -0.09    | 3.05176e-05 |        100 |                 0 |                16 |        0 |       0.000457764 |         -0.16 | negative_supported   |
| scarcity_capacity        | A3_WRENCH_PAIR    | A4_MECHANICS_SAFE |              0.08 |       0.03 |     0.14    | 0.0078125   |        100 |                 8 |                 0 |        0 |       0.109375    |          0.08 | inconclusive_or_null |
| scarcity_capacity        | A4_MECHANICS_SAFE | FULL_ROBUST_LOCAL |              0    |       0    |     0       | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| torque_complementarity   | A0_RAW_PREF       | A1_INTEGER_QR     |              0    |       0    |     0       | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| torque_complementarity   | A1_INTEGER_QR     | A2_CAPACITY       |              0    |       0    |     0       | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| torque_complementarity   | A2_CAPACITY       | A3_WRENCH_PAIR    |              0.63 |       0.54 |     0.72    | 2.1684e-19  |        100 |                63 |                 0 |        0 |       4.11997e-18 |          0.63 | positive_supported   |
| torque_complementarity   | A3_WRENCH_PAIR    | A4_MECHANICS_SAFE |              0.01 |       0    |     0.03    | 1           |        100 |                 1 |                 0 |        0 |       1           |          0.01 | inconclusive_or_null |
| torque_complementarity   | A4_MECHANICS_SAFE | FULL_ROBUST_LOCAL |              0    |       0    |     0       | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| obstacle_network_dropout | A0_RAW_PREF       | A1_INTEGER_QR     |              0    |       0    |     0       | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| obstacle_network_dropout | A1_INTEGER_QR     | A2_CAPACITY       |              0    |       0    |     0       | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| obstacle_network_dropout | A2_CAPACITY       | A3_WRENCH_PAIR    |              0    |       0    |     0       | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| obstacle_network_dropout | A3_WRENCH_PAIR    | A4_MECHANICS_SAFE |              0.22 |       0.14 |     0.3     | 4.76837e-07 |        100 |                22 |                 0 |        0 |       7.62939e-06 |          0.22 | positive_supported   |
| obstacle_network_dropout | A4_MECHANICS_SAFE | FULL_ROBUST_LOCAL |              0.67 |       0.58 |     0.76    | 1.35525e-20 |        100 |                67 |                 0 |        0 |       2.71051e-19 |          0.67 | positive_supported   |

## Interpretation boundary

The ladder isolates which certificate removes which physical false positive inside the specified deterministic model. Static acceptance is never reported as dynamic convergence. The mechanics claim assumes an established rigid grasp with bounded signed traction; safety requires feasible HOCBF actuation. The empirical rates are not universal theoretical bounds.

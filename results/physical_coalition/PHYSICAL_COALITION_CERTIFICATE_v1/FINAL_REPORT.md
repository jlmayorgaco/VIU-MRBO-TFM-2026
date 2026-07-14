# Physical-coalition certificate campaign — final report

Protocol: `PHYSICAL_COALITION_CERTIFICATE_v1`. CPU-only reduced-order Python simulation; no GPU, MARL training, CoppeliaSim, replacement seeds or synthetic rows.

## Execution gate

- Retained rows: 2160; unique run IDs: 2160.
- Numerical errors: 0.
- Final paired worlds by family: `{"nominal_rotation": 60, "obstacle_network_dropout": 100, "scarcity_capacity": 100, "torque_complementarity": 100}`.
- Confirmatory seeds were opened only after `frozen_manifest.json` recorded `frozen_ready_for_execution`.
- Precision extensions used CI-width only; Holm was applied at final sample sizes.

## FULL robust-local stage

| scenario_family          |   success_rate |   physical_false_positive_rate |   mean_messages |   mean_runtime_wall_s |
|:-------------------------|---------------:|-------------------------------:|----------------:|----------------------:|
| nominal_rotation         |           0.95 |                           0.05 |          471    |              0.440843 |
| obstacle_network_dropout |           0.86 |                           0.14 |          661.46 |              0.533422 |
| scarcity_capacity        |           0.89 |                           0.11 |          501.72 |              0.326943 |
| torque_complementarity   |           1    |                           0    |          427.64 |              0.447155 |

## Confirmatory paired contrasts

| scenario_family          | before            | after             |   effect_estimate |   CI95_low |   CI95_high |       raw_p |   n_worlds |   improved_worlds |   degraded_worlds |   margin |   Holm_adjusted_p |   effect_size | decision             |
|:-------------------------|:------------------|:------------------|------------------:|-----------:|------------:|------------:|-----------:|------------------:|------------------:|---------:|------------------:|--------------:|:---------------------|
| nominal_rotation         | A0_RAW_PREF       | A1_INTEGER_QR     |              0    |       0    |        0    | 1           |         60 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| nominal_rotation         | A1_INTEGER_QR     | A2_CAPACITY       |              0    |       0    |        0    | 1           |         60 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| nominal_rotation         | A2_CAPACITY       | A3_WRENCH_PAIR    |              0.05 |      -0.05 |        0.15 | 0.507812    |         60 |                 6 |                 3 |        0 |       1           |          0.05 | inconclusive_or_null |
| nominal_rotation         | A3_WRENCH_PAIR    | A4_MECHANICS_SAFE |              0    |       0    |        0    | 1           |         60 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| nominal_rotation         | A4_MECHANICS_SAFE | FULL_ROBUST_LOCAL |              0    |       0    |        0    | 1           |         60 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| scarcity_capacity        | A0_RAW_PREF       | A1_INTEGER_QR     |              0.67 |       0.58 |        0.76 | 1.35525e-20 |        100 |                67 |                 0 |        0 |       2.71051e-19 |          0.67 | positive_supported   |
| scarcity_capacity        | A1_INTEGER_QR     | A2_CAPACITY       |              0.33 |       0.24 |        0.42 | 2.32831e-10 |        100 |                33 |                 0 |        0 |       3.95812e-09 |          0.33 | positive_supported   |
| scarcity_capacity        | A2_CAPACITY       | A3_WRENCH_PAIR    |             -0.18 |      -0.25 |       -0.11 | 7.62939e-06 |        100 |                 0 |                18 |        0 |       0.000114441 |         -0.18 | negative_supported   |
| scarcity_capacity        | A3_WRENCH_PAIR    | A4_MECHANICS_SAFE |              0.07 |       0.03 |        0.12 | 0.015625    |        100 |                 7 |                 0 |        0 |       0.21875     |          0.07 | inconclusive_or_null |
| scarcity_capacity        | A4_MECHANICS_SAFE | FULL_ROBUST_LOCAL |              0    |       0    |        0    | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| torque_complementarity   | A0_RAW_PREF       | A1_INTEGER_QR     |              0    |       0    |        0    | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| torque_complementarity   | A1_INTEGER_QR     | A2_CAPACITY       |              0    |       0    |        0    | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| torque_complementarity   | A2_CAPACITY       | A3_WRENCH_PAIR    |              0.6  |       0.5  |        0.7  | 2.73219e-17 |        100 |                61 |                 1 |        0 |       4.91794e-16 |          0.6  | positive_supported   |
| torque_complementarity   | A3_WRENCH_PAIR    | A4_MECHANICS_SAFE |              0.01 |       0    |        0.03 | 1           |        100 |                 1 |                 0 |        0 |       1           |          0.01 | inconclusive_or_null |
| torque_complementarity   | A4_MECHANICS_SAFE | FULL_ROBUST_LOCAL |              0    |       0    |        0    | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| obstacle_network_dropout | A0_RAW_PREF       | A1_INTEGER_QR     |              0    |       0    |        0    | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| obstacle_network_dropout | A1_INTEGER_QR     | A2_CAPACITY       |              0    |       0    |        0    | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| obstacle_network_dropout | A2_CAPACITY       | A3_WRENCH_PAIR    |              0    |       0    |        0    | 1           |        100 |                 0 |                 0 |        0 |       1           |          0    | inconclusive_or_null |
| obstacle_network_dropout | A3_WRENCH_PAIR    | A4_MECHANICS_SAFE |              0.24 |       0.16 |        0.33 | 1.19209e-07 |        100 |                24 |                 0 |        0 |       1.90735e-06 |          0.24 | positive_supported   |
| obstacle_network_dropout | A4_MECHANICS_SAFE | FULL_ROBUST_LOCAL |              0.62 |       0.52 |        0.71 | 4.33681e-19 |        100 |                62 |                 0 |        0 |       8.23994e-18 |          0.62 | positive_supported   |

## Interpretation boundary

The ladder isolates which certificate removes which physical false positive inside the specified deterministic model. Static acceptance is never reported as dynamic convergence. The mechanics claim assumes an established rigid grasp with bounded signed traction; safety requires feasible HOCBF actuation. The empirical rates are not universal theoretical bounds.

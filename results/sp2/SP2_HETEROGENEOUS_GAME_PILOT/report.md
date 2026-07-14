# SP2_HETEROGENEOUS_GAME_PILOT

- Worlds: `24`
- Runs: `336`
- Theory audit: `PASS`

## Summary

| method                       |   n |   served_rate_mean |   coverage_mean |   regret_mean |   regret_std |   raw_served_rate_mean |   convergence_rate |   potential_gain_mean |   messages_mean |   runtime_s_mean |
|:-----------------------------|----:|-------------------:|----------------:|--------------:|-------------:|-----------------------:|-------------------:|----------------------:|----------------:|-----------------:|
| milp_exact                   |  24 |            0.77778 |         0.89229 |       0       |      0       |                0.77778 |                  1 |             nan       |              24 |       7.0063e-05 |
| erv_bnn__marginal_log        |  24 |            0.61111 |         0.89795 |       0.21327 |      0.1838  |                0.51389 |                  0 |               3.1554  |           39600 |       0.036796   |
| smith__marginal_log          |  24 |            0.59722 |         0.89395 |       0.22615 |      0.19374 |                0.54167 |                  0 |               4.1209  |           39600 |       0.037639   |
| replicator__marginal_log     |  24 |            0.58333 |         0.90582 |       0.24048 |      0.22486 |                0.52778 |                  0 |               3.6713  |           39600 |       0.035405   |
| uniform_closure              |  24 |            0.56944 |         0.91271 |       0.2542  |      0.25496 |                0       |                  1 |             nan       |              24 |       0.0003749  |
| greedy_capacity              |  24 |            0.56944 |         0.80978 |       0.27759 |      0.20077 |                0.56944 |                  1 |             nan       |              24 |       0.00049977 |
| erv_bnn__marginal_deficit    |  24 |            0.52778 |         0.89999 |       0.2917  |      0.23819 |                0.34722 |                  0 |               0.56904 |           39600 |       0.039726   |
| smith__marginal_deficit      |  24 |            0.52778 |         0.89957 |       0.29947 |      0.28878 |                0.33333 |                  0 |               0.74801 |           39600 |       0.038812   |
| random_closure               |  24 |            0.55556 |         0.87107 |       0.30565 |      0.27997 |                0.31944 |                  1 |             nan       |              24 |       0.000483   |
| auction_capacity             |  24 |            0.5     |         0.89947 |       0.32308 |      0.25537 |                0.5     |                  1 |             nan       |              24 |       0.00023722 |
| replicator__plain_deficit    |  24 |            0.48611 |         0.85789 |       0.33345 |      0.27053 |                0.36111 |                  0 |             nan       |           39600 |       0.032092   |
| erv_bnn__plain_deficit       |  24 |            0.47222 |         0.86749 |       0.35093 |      0.26178 |                0.375   |                  0 |             nan       |           39600 |       0.033382   |
| smith__plain_deficit         |  24 |            0.45833 |         0.85858 |       0.35915 |      0.25208 |                0.40278 |                  0 |             nan       |           39600 |       0.034575   |
| replicator__marginal_deficit |  24 |            0.45833 |         0.90896 |       0.36926 |      0.27735 |                0.36111 |                  0 |               0.52054 |           39600 |       0.036369   |

## Hypotheses

| id      | candidate                    | reference                 | metric            |   n_pairs |   effect_mean_paired |   ci95_low |   ci95_high |   p_value_raw | interpretation   |   p_value_holm | reject_holm_005   |
|:--------|:-----------------------------|:--------------------------|:------------------|----------:|---------------------:|-----------:|------------:|--------------:|:-----------------|---------------:|:------------------|
| H-SP2-1 | smith__marginal_deficit      | smith__plain_deficit      | normalized_regret |        24 |            -0.05968  |  -0.16089  |    0.038327 |    0.56776    | inconclusive     |     1          | False             |
| H-SP2-2 | replicator__marginal_deficit | replicator__plain_deficit | normalized_regret |        24 |             0.035814 |  -0.043468 |    0.11448  |    0.2312     | inconclusive     |     1          | False             |
| H-SP2-3 | erv_bnn__marginal_deficit    | erv_bnn__plain_deficit    | normalized_regret |        24 |            -0.059229 |  -0.15932  |    0.033708 |    0.38838    | inconclusive     |     1          | False             |
| H-SP2-4 | erv_bnn__marginal_deficit    | greedy_capacity           | normalized_regret |        24 |             0.014111 |  -0.089259 |    0.12851  |    0.48195    | inconclusive     |     1          | False             |
| H-SP2-5 | erv_bnn__marginal_deficit    | auction_capacity          | normalized_regret |        24 |            -0.031373 |  -0.11846  |    0.058378 |    0.56607    | inconclusive     |     1          | False             |
| H-SP2-6 | erv_bnn__marginal_deficit    | milp_exact                | normalized_regret |        24 |             0.2917   |   0.19721  |    0.38904  |    1.1921e-07 | reference_better |     7.1526e-07 | True              |

## Interpretation

- Fitness and revision protocols are crossed factorially.
- Plain deficit fitness is a heuristic under pair-dependent capacity.
- RAW preferences, capacity closure, and the MILP oracle are separate stages.
- Ring results are sensitivity evidence, not a time-varying-graph theorem.
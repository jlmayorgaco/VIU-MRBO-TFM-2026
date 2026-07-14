# SP2_HETEROGENEOUS_GAME_v1_1

- Worlds: `480`
- Runs: `6720`
- Theory audit: `PASS`

## Summary

| method                       |   n |   served_rate_mean |   coverage_mean |   regret_mean |   regret_std |   raw_served_rate_mean |   convergence_rate |   potential_gain_mean |   messages_mean |   runtime_s_mean |
|:-----------------------------|----:|-------------------:|----------------:|--------------:|-------------:|-----------------------:|-------------------:|----------------------:|----------------:|-----------------:|
| milp_exact                   | 480 |            0.81181 |         0.88562 |       0       |      0       |                0.81181 |            1       |              nan      |     48          |       8.7194e-05 |
| uniform_closure              | 480 |            0.58764 |         0.91195 |       0.25829 |      0.24682 |                0       |            1       |              nan      |     48          |       0.00069078 |
| erv_bnn__marginal_log        | 480 |            0.57458 |         0.8865  |       0.26934 |      0.21804 |                0.53625 |            1       |                5.0279 |      1.0145e+05 |       0.046259   |
| replicator__marginal_log     | 480 |            0.57042 |         0.88345 |       0.27187 |      0.21092 |                0.53208 |            0.56667 |                5.5805 |      1.3503e+05 |       0.06072    |
| smith__marginal_log          | 480 |            0.56917 |         0.88291 |       0.27528 |      0.21279 |                0.53889 |            0.94375 |                5.6858 |      1.1165e+05 |       0.051677   |
| replicator__marginal_deficit | 480 |            0.53403 |         0.88508 |       0.30376 |      0.24185 |                0.3375  |            0.62917 |                1.2806 |      1.244e+05  |       0.056771   |
| erv_bnn__marginal_deficit    | 480 |            0.53111 |         0.89033 |       0.30632 |      0.24819 |                0.32653 |            0.98542 |                1.1536 |  94176          |       0.042981   |
| auction_capacity             | 480 |            0.51347 |         0.8893  |       0.31788 |      0.23131 |                0.51347 |            1       |              nan      |     48          |       0.00048264 |
| smith__marginal_deficit      | 480 |            0.51889 |         0.8808  |       0.31834 |      0.23799 |                0.34389 |            0.95625 |                1.4873 |      1.1003e+05 |       0.051991   |
| replicator__plain_deficit    | 480 |            0.51569 |         0.86492 |       0.32171 |      0.25277 |                0.35986 |            0.78542 |              nan      |      1.0363e+05 |       0.042259   |
| erv_bnn__plain_deficit       | 480 |            0.51597 |         0.87423 |       0.32401 |      0.25915 |                0.36375 |            0.98958 |              nan      |  86457          |       0.035944   |
| smith__plain_deficit         | 480 |            0.51153 |         0.86505 |       0.32711 |      0.2476  |                0.37417 |            0.95625 |              nan      |      1.0156e+05 |       0.043044   |
| greedy_capacity              | 480 |            0.53292 |         0.78594 |       0.33367 |      0.21162 |                0.53292 |            1       |              nan      |     48          |       0.00090457 |
| random_closure               | 480 |            0.53792 |         0.86016 |       0.34718 |      0.22609 |                0.32667 |            1       |              nan      |     48          |       0.00079981 |

## Hypotheses

| id       | candidate                    | reference                 | metric            |   n_pairs |   effect_mean_paired |   ci95_low |   ci95_high |   p_value_raw | interpretation   |   p_value_holm | reject_holm_005   |
|:---------|:-----------------------------|:--------------------------|:------------------|----------:|---------------------:|-----------:|------------:|--------------:|:-----------------|---------------:|:------------------|
| H-SP2-1  | smith__marginal_deficit      | smith__plain_deficit      | normalized_regret |       480 |           -0.0087699 |  -0.026462 |  0.0084594  |    0.092361   | inconclusive     |     0.18472    | False             |
| H-SP2-2  | replicator__marginal_deficit | replicator__plain_deficit | normalized_regret |       480 |           -0.017945  |  -0.034944 | -0.0012956  |    0.0034995  | candidate_better |     0.020997   | True              |
| H-SP2-3  | erv_bnn__marginal_deficit    | erv_bnn__plain_deficit    | normalized_regret |       480 |           -0.017694  |  -0.034543 | -0.00070163 |    0.004004   | candidate_better |     0.020997   | True              |
| H-SP2-4  | smith__marginal_log          | smith__plain_deficit      | normalized_regret |       480 |           -0.051827  |  -0.072163 | -0.031697   |    0.00056995 | candidate_better |     0.0045596  | True              |
| H-SP2-5  | replicator__marginal_log     | replicator__plain_deficit | normalized_regret |       480 |           -0.049841  |  -0.071149 | -0.029934   |    0.00080148 | candidate_better |     0.0056104  | True              |
| H-SP2-6  | erv_bnn__marginal_log        | erv_bnn__plain_deficit    | normalized_regret |       480 |           -0.054669  |  -0.074323 | -0.035167   |    6.7074e-05 | candidate_better |     0.00060367 | True              |
| H-SP2-7  | erv_bnn__marginal_log        | smith__marginal_log       | normalized_regret |       480 |           -0.0059392 |  -0.013839 |  0.0021605  |    0.013447   | inconclusive     |     0.053787   | False             |
| H-SP2-8  | erv_bnn__marginal_log        | replicator__marginal_log  | normalized_regret |       480 |           -0.0025236 |  -0.012109 |  0.0069359  |    0.62579    | inconclusive     |     0.62579    | False             |
| H-SP2-9  | erv_bnn__marginal_log        | greedy_capacity           | normalized_regret |       480 |           -0.064325  |  -0.087406 | -0.041302   |    4.0095e-10 | candidate_better |     4.0095e-09 | True              |
| H-SP2-10 | erv_bnn__marginal_log        | auction_capacity          | normalized_regret |       480 |           -0.04854   |  -0.070743 | -0.027477   |    0.014962   | candidate_better |     0.053787   | False             |
| H-SP2-11 | erv_bnn__marginal_log        | milp_exact                | normalized_regret |       480 |            0.26934   |   0.24938  |  0.28916    |    1.0502e-79 | reference_better |     1.1552e-78 | True              |

## Interpretation

- Fitness and revision protocols are crossed factorially.
- Plain deficit fitness is a heuristic under pair-dependent capacity.
- RAW preferences, capacity closure, and the MILP oracle are separate stages.
- Ring results are sensitivity evidence, not a time-varying-graph theorem.
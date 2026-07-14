# SP2_HETEROGENEOUS_GAME_v1

- Worlds: `480`
- Runs: `6720`
- Theory audit: `FAIL`

## Summary

| method                       |   n |   served_rate_mean |   coverage_mean |   regret_mean |   regret_std |   raw_served_rate_mean |   convergence_rate |   potential_gain_mean |   messages_mean |   runtime_s_mean |
|:-----------------------------|----:|-------------------:|----------------:|--------------:|-------------:|-----------------------:|-------------------:|----------------------:|----------------:|-----------------:|
| milp_exact                   | 480 |            0.81056 |         0.88615 |       0       |      0       |                0.81056 |            1       |              nan      |     48          |       8.2081e-05 |
| uniform_closure              | 480 |            0.58958 |         0.91233 |       0.25539 |      0.24462 |                0       |            1       |              nan      |     48          |       0.00068894 |
| erv_bnn__marginal_log        | 480 |            0.565   |         0.8839  |       0.28173 |      0.21097 |                0.53069 |            1       |                5.0245 |      1.0099e+05 |       0.044869   |
| replicator__marginal_log     | 480 |            0.55861 |         0.88018 |       0.2878  |      0.20856 |                0.52639 |            0.56875 |                5.5828 |      1.3456e+05 |       0.059411   |
| replicator__marginal_deficit | 480 |            0.54306 |         0.88544 |       0.29344 |      0.23008 |                0.34514 |            0.61875 |                1.2894 |      1.2422e+05 |       0.056129   |
| smith__marginal_log          | 480 |            0.55431 |         0.88124 |       0.29386 |      0.21622 |                0.52903 |            0.95417 |                5.6996 |      1.1082e+05 |       0.050278   |
| erv_bnn__marginal_deficit    | 480 |            0.53847 |         0.89194 |       0.29903 |      0.24063 |                0.33611 |            0.99792 |                1.1588 |  93300          |       0.041717   |
| auction_capacity             | 480 |            0.52181 |         0.88957 |       0.31035 |      0.23982 |                0.52181 |            1       |              nan      |     48          |       0.00045751 |
| smith__marginal_deficit      | 480 |            0.52444 |         0.88298 |       0.312   |      0.23559 |                0.34403 |            0.9375  |                1.4944 |      1.1082e+05 |       0.051559   |
| erv_bnn__plain_deficit       | 480 |            0.51819 |         0.87661 |       0.32026 |      0.24881 |                0.38292 |            0.99375 |              nan      |  85711          |       0.035078   |
| replicator__plain_deficit    | 480 |            0.51625 |         0.8705  |       0.32264 |      0.24292 |                0.36889 |            0.80417 |              nan      |      1.0045e+05 |       0.040565   |
| smith__plain_deficit         | 480 |            0.50542 |         0.86931 |       0.33416 |      0.24489 |                0.38708 |            0.95625 |              nan      |      1.0159e+05 |       0.042414   |
| greedy_capacity              | 480 |            0.52847 |         0.77917 |       0.33878 |      0.21128 |                0.52847 |            1       |              nan      |     48          |       0.00089244 |
| random_closure               | 480 |            0.53292 |         0.86557 |       0.35097 |      0.22708 |                0.32    |            1       |              nan      |     48          |       0.00078926 |

## Hypotheses

| id       | candidate                    | reference                 | metric            |   n_pairs |   effect_mean_paired |   ci95_low |   ci95_high |   p_value_raw | interpretation   |   p_value_holm | reject_holm_005   |
|:---------|:-----------------------------|:--------------------------|:------------------|----------:|---------------------:|-----------:|------------:|--------------:|:-----------------|---------------:|:------------------|
| H-SP2-1  | smith__marginal_deficit      | smith__plain_deficit      | normalized_regret |       480 |           -0.02216   |  -0.039567 |  -0.0051554 |    0.0028942  | candidate_better |     0.014471   | True              |
| H-SP2-2  | replicator__marginal_deficit | replicator__plain_deficit | normalized_regret |       480 |           -0.029198  |  -0.046896 |  -0.012742  |    9.8595e-05 | candidate_better |     0.00069016 | True              |
| H-SP2-3  | erv_bnn__marginal_deficit    | erv_bnn__plain_deficit    | normalized_regret |       480 |           -0.021228  |  -0.038158 |  -0.0034022 |    8.1118e-05 | candidate_better |     0.00064894 | True              |
| H-SP2-4  | smith__marginal_log          | smith__plain_deficit      | normalized_regret |       480 |           -0.040296  |  -0.059699 |  -0.020455  |    0.012134   | candidate_better |     0.036401   | True              |
| H-SP2-5  | replicator__marginal_log     | replicator__plain_deficit | normalized_regret |       480 |           -0.034837  |  -0.053915 |  -0.014211  |    0.026044   | candidate_better |     0.052088   | False             |
| H-SP2-6  | erv_bnn__marginal_log        | erv_bnn__plain_deficit    | normalized_regret |       480 |           -0.038527  |  -0.05852  |  -0.017741  |    0.0073029  | candidate_better |     0.029212   | True              |
| H-SP2-7  | erv_bnn__marginal_log        | smith__marginal_log       | normalized_regret |       480 |           -0.012133  |  -0.020106 |  -0.0044923 |    2.7898e-06 | candidate_better |     2.5108e-05 | True              |
| H-SP2-8  | erv_bnn__marginal_log        | replicator__marginal_log  | normalized_regret |       480 |           -0.0060723 |  -0.013689 |   0.0013515 |    0.0021912  | inconclusive     |     0.013147   | True              |
| H-SP2-9  | erv_bnn__marginal_log        | greedy_capacity           | normalized_regret |       480 |           -0.057051  |  -0.081729 |  -0.032772  |    4.274e-08  | candidate_better |     4.274e-07  | True              |
| H-SP2-10 | erv_bnn__marginal_log        | auction_capacity          | normalized_regret |       480 |           -0.028618  |  -0.050248 |  -0.0062945 |    0.65197    | candidate_better |     0.65197    | False             |
| H-SP2-11 | erv_bnn__marginal_log        | milp_exact                | normalized_regret |       480 |            0.28173   |   0.26325  |   0.30191   |    4.5128e-78 | reference_better |     4.9641e-77 | True              |

## Interpretation

- Fitness and revision protocols are crossed factorially.
- Plain deficit fitness is a heuristic under pair-dependent capacity.
- RAW preferences, capacity closure, and the MILP oracle are separate stages.
- Ring results are sensitivity evidence, not a time-varying-graph theorem.